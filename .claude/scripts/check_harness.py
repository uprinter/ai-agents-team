#!/usr/bin/env python3
"""Validate this harness, or deterministic SDD artifacts in a target project.

Target mode checks active top-level ``specs/NNN-slug/`` features that contain
``spec.md``. Spec-less XS work has no universal directory or lane declaration,
so it is outside target-mode coverage. Archived features are historical records
and are not revalidated against newer rules. Use ``--feature NNN-slug`` in
target CI to check only the current feature; that mode skips the historical
verify log, which may contain entries written before the current grammar.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
NAME_LINE = re.compile(r"^name:\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s#]+))\s*$", re.MULTILINE)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
FRONTMATTER_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$", re.MULTILINE)
REQUIRED_AGENT_KEYS = {"name", "description", "model"}
OPTIONAL_AGENT_KEYS = {"tools", "color", "skills", "effort"}
FEATURE_DIR = re.compile(r"^\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*$")
AC_ID = re.compile(r"\bAC-\d+(?:\.\d+)*\b")
AC_SECTION = re.compile(
    r"^(?P<marks>#{1,6})\s+(?:\d+\.\s+)?Acceptance Criteria(?:\s+\([^)]*\))?\s*$",
    re.IGNORECASE,
)
AC_DEFINITION = re.compile(
    r"^\s*(?:(?:#{1,6}|[-*+]|\d+[.)])\s+)?(?:\*\*|`)?"
    r"(?P<id>AC-\d+(?:\.\d+)*)(?:\*\*|`)?(?:\s|:|—|-)"
)
SIZE_LINE = re.compile(r"^size:\s*(?:\"([XSML])\"|'([XSML])'|([XSML]))\s*$", re.MULTILINE)
STATUS_LINE = re.compile(
    r"^status:\s*(?:\"(Draft|Active)\"|'(Draft|Active)'|(Draft|Active))\s*$",
    re.MULTILINE,
)
VERIFY_HEADER = re.compile(
    r"^## (?P<slug>(?:\d{3}-)?[a-z0-9]+(?:-[a-z0-9]+)*) — "
    r"(?P<result>PASSED|BLOCKED) (?P<date>\d{4}-\d{2}-\d{2}) · "
    r"lane (?P<lane>XS|S|M|L) · (?P<count>\d+) MR(?:s|\(s\))? "
    r"\((?P<iids>!\d+(?:, !\d+)*)\)(?P<reason> — .+)?$"
)
GATES_LINE = re.compile(
    r"^gates: lane=(?P<lane>XS|S|M|L) "
    r"budget=(?:n/a|\d+/\d+)(?: waived-by-\S+)? "
    r"tasks\.md=(?:yes|no)(?: waived-by-\S+)? "
    r"status=(?:Draft|Active|Withdrawn|Historic|Superseded-by: \d{3})(?: waived-by-\S+)? "
    r"mrs=\d+/\d+(?: waived-by-\S+)? "
    r"worktrees=(?:clean|\d+ left)(?: waived-by-\S+)? "
    r"design=(?:pass|n/a)(?: waived-by-\S+)? "
    r"copy=(?:pass|n/a)(?: waived-by-\S+)? "
    r"live=(?:pass|n/a)(?: waived-by-\S+)? "
    r"ci=(?:pass|n/a)(?: waived-by-\S+)? "
    r"(?:(?:tier=[012])|(?:tiers=!\d+:[012](?:,!\d+:[012])*)) "
    r"gap=(?:n/a|[0-9.]+[a-z]+/[0-9.]+[a-z]+|!\d+:(?:n/a|[0-9.]+[a-z]+/[0-9.]+[a-z]+)(?:,!\d+:(?:n/a|[0-9.]+[a-z]+/[0-9.]+[a-z]+))*)$"
)
GITLAB_INLINE_TRIGGER = (
    "If it is not preloaded, read and follow "
    "`${CLAUDE_PLUGIN_ROOT}/.claude/skills/gitlab-access/SKILL.md` directly"
)
CODEX_GITLAB_TRIGGER = "`$gitlab-access` from `.agents/skills/gitlab-access/SKILL.md`."
OPENCODE_SKILL_BLOCK = re.compile(
    r"## Load these skills first\n\n(?P<body>.*?)(?:\n\n|\Z)",
    re.DOTALL,
)


def validate_agent_names(root: Path) -> list[str]:
    errors: list[str] = []
    agent_dir = root / ".claude" / "agents"
    agents = sorted(agent_dir.glob("*.md"))
    if not agents:
        return [f"no source agents found in {agent_dir.relative_to(root)}"]

    seen: dict[str, Path] = {}
    for path in agents:
        relative = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            errors.append(f"{relative}: cannot read file: {error}")
            continue
        frontmatter = FRONTMATTER.match(text)
        if not frontmatter:
            errors.append(f"{relative}: missing YAML frontmatter")
            continue
        frontmatter_text = frontmatter.group(1)
        key_counts: dict[str, int] = {}
        for key, _ in FRONTMATTER_KEY.findall(frontmatter_text):
            key_counts[key] = key_counts.get(key, 0) + 1
        for key in sorted(REQUIRED_AGENT_KEYS):
            count = key_counts.get(key, 0)
            if count != 1:
                errors.append(f"{relative}: frontmatter must contain exactly one {key} field")
        for key in sorted(OPTIONAL_AGENT_KEYS):
            if key_counts.get(key, 0) > 1:
                errors.append(f"{relative}: frontmatter contains duplicate {key} fields")
        lines = frontmatter_text.splitlines()
        declared_skills: set[str] = set()
        for index, line in enumerate(lines):
            if line != "skills:":
                continue
            for skill_line in lines[index + 1 :]:
                if not skill_line.startswith("  - "):
                    break
                declared_skills.add(skill_line[4:].strip())
            break
        if "gitlab-access" not in declared_skills:
            errors.append(f"{relative}: skills must include gitlab-access")
        if GITLAB_INLINE_TRIGGER not in text[frontmatter.end() :]:
            errors.append(f"{relative}: body must include the GitLab access load trigger")
        names = NAME_LINE.findall(frontmatter_text)
        if len(names) != 1:
            errors.append(f"{relative}: frontmatter must contain exactly one name field")
            continue
        name = next(value for value in names[0] if value)
        if name != path.stem:
            errors.append(f"{relative}: name {name!r} does not match filename {path.stem!r}")
        if name in seen:
            errors.append(f"{relative}: duplicate agent name {name!r} also used by {seen[name].relative_to(root)}")
        else:
            seen[name] = path
    return errors


def skill_entries(path: Path) -> dict[str, Path]:
    if not path.is_dir():
        return {}
    return {entry.name: entry for entry in path.iterdir() if entry.is_dir()}


def validate_skill_mirrors(root: Path) -> list[str]:
    errors: list[str] = []
    agents_dir = root / ".agents" / "skills"
    claude_dir = root / ".claude" / "skills"
    agents = skill_entries(agents_dir)
    claude = skill_entries(claude_dir)

    if not agents:
        errors.append(f"no skills found in {agents_dir.relative_to(root)}")
    if not claude:
        errors.append(f"no skills found in {claude_dir.relative_to(root)}")

    for name in sorted(set(agents) | set(claude)):
        left = agents.get(name)
        right = claude.get(name)
        if left is None:
            errors.append(f".agents/skills/{name}: missing mirror for .claude/skills/{name}")
            continue
        if right is None:
            errors.append(f".claude/skills/{name}: missing mirror for .agents/skills/{name}")
            continue
        if left.is_symlink() == right.is_symlink():
            errors.append(f"skill {name!r}: exactly one entry must be a symlink")
            continue
        try:
            same_target = left.resolve(strict=True) == right.resolve(strict=True)
        except OSError as error:
            errors.append(f"skill {name!r}: cannot resolve mirror: {error}")
            continue
        if not same_target:
            errors.append(f"skill {name!r}: mirror points to a different directory")
            continue
        if not (left / "SKILL.md").is_file() or not (right / "SKILL.md").is_file():
            errors.append(f"skill {name!r}: mirrored directory must contain SKILL.md")
    return errors


def run_generated_port_checks(root: Path) -> list[str]:
    errors: list[str] = []
    scripts = (root / ".codex" / "sync-agents.py", root / ".opencode" / "sync-agents.py")
    for script in scripts:
        relative = script.relative_to(root)
        if not script.is_file():
            errors.append(f"{relative}: generated-port checker is missing")
            continue
        result = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        if result.returncode:
            errors.append(f"{relative} --check failed" + (f":\n{output}" if output else ""))
        elif output:
            print(output)
    return errors


def validate_generated_gitlab_wiring(root: Path) -> list[str]:
    errors: list[str] = []
    for source in sorted((root / ".claude" / "agents").glob("*.md")):
        stem = source.stem
        codex_path = root / ".codex" / "agents" / f"{stem}.toml"
        if not codex_path.is_file():
            errors.append(f"{codex_path.relative_to(root)}: generated profile is missing")
        else:
            text = codex_path.read_text(encoding="utf-8")
            runtime_notes, separator, _ = text.partition("<!-- END CODEX RUNTIME NOTES -->")
            if not separator or CODEX_GITLAB_TRIGGER not in runtime_notes:
                errors.append(
                    f"{codex_path.relative_to(root)}: Codex runtime notes must load gitlab-access"
                )

        opencode_path = root / ".opencode" / "agent" / f"{stem}.md"
        if not opencode_path.is_file():
            errors.append(f"{opencode_path.relative_to(root)}: generated profile is missing")
        else:
            text = opencode_path.read_text(encoding="utf-8")
            skill_block = OPENCODE_SKILL_BLOCK.search(text)
            if not skill_block or "`gitlab-access`" not in skill_block.group("body"):
                errors.append(
                    f"{opencode_path.relative_to(root)}: OpenCode skill loader must include gitlab-access"
                )
    return errors


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def parse_validation_map(tasks_path: Path) -> tuple[dict[str, tuple[str, str, str, str]], list[str]]:
    rows: dict[str, tuple[str, str, str, str]] = {}
    errors: list[str] = []
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    expected_header = ["ac", "method", "stage", "evidence", "owner"]
    for index, line in enumerate(lines):
        cells = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        if cells != expected_header:
            continue
        if index + 1 >= len(lines):
            return rows, ["validation map is missing its separator row"]
        separator = [cell.strip() for cell in lines[index + 1].strip().strip("|").split("|")]
        if len(separator) != 5 or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
            return rows, ["validation map has an invalid separator row"]
        for row in lines[index + 2 :]:
            if not row.strip().startswith("|"):
                break
            values = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(values) != 5:
                errors.append("validation map row must contain exactly five columns")
                continue
            ac, method, stage, evidence, owner = values
            ac = ac.strip("`")
            if not AC_ID.fullmatch(ac):
                errors.append(f"validation map has invalid AC value {ac!r}")
                continue
            if ac in rows:
                errors.append(f"validation map contains duplicate row for {ac}")
                continue
            if not all((method, stage, evidence, owner)):
                errors.append(f"validation map row for {ac} has an empty field")
                continue
            if stage.strip("`") not in {"CI", "review", "live"}:
                errors.append(f"validation map row for {ac} has invalid stage {stage!r}")
                continue
            if method.lower() in {"review", "verify manually"}:
                errors.append(f"validation map row for {ac} has vague method {method!r}")
                continue
            rows[ac] = (method, stage, evidence, owner)
        return rows, errors
    return rows, ["tasks.md is missing the AC validation map table"]


def acceptance_criterion_ids(spec_body: str) -> set[str]:
    """Return IDs from definition lines in the Acceptance Criteria section."""
    lines = spec_body.splitlines()
    section_level: int | None = None
    ids: set[str] = set()
    for line in lines:
        if section_level is None:
            heading = AC_SECTION.fullmatch(line.strip())
            if heading:
                section_level = len(heading.group("marks"))
            continue
        heading = re.match(r"^(#{1,6})\s+", line)
        if heading and len(heading.group(1)) <= section_level:
            break
        definition = AC_DEFINITION.match(line)
        if definition:
            ids.add(definition.group("id"))
    return ids


def validate_feature(feature: Path, root: Path) -> list[str]:
    errors: list[str] = []
    spec = feature / "spec.md"
    plan = feature / "plan.md"
    tasks = feature / "tasks.md"
    spec_text = spec.read_text(encoding="utf-8")
    frontmatter = FRONTMATTER.match(spec_text)
    if not frontmatter:
        return [f"{spec.relative_to(root)}: missing YAML frontmatter"]
    sizes = SIZE_LINE.findall(frontmatter.group(1))
    if len(sizes) != 1:
        return [f"{spec.relative_to(root)}: frontmatter must contain one size field (XS, S, M, or L)"]
    lane = next(value for value in sizes[0] if value)
    statuses = STATUS_LINE.findall(frontmatter.group(1))
    status_key_count = sum(
        1 for key, _ in FRONTMATTER_KEY.findall(frontmatter.group(1)) if key == "status"
    )
    if status_key_count != 1 or len(statuses) != 1:
        errors.append(
            f"{spec.relative_to(root)}: active spec frontmatter must contain exactly one status field (Draft or Active)"
        )

    spec_lines = len(spec_text.splitlines())
    if lane == "XS":
        errors.append(f"{spec.relative_to(root)}: lane XS must not have a numbered spec")
    elif lane == "S":
        if spec_lines > 120:
            errors.append(f"{spec.relative_to(root)}: lane S spec is {spec_lines} lines; limit is 120")
        if plan.exists():
            errors.append(f"{plan.relative_to(root)}: lane S must not have plan.md")
    elif lane == "M":
        if spec_lines > 250:
            errors.append(f"{spec.relative_to(root)}: lane M spec is {spec_lines} lines; limit is 250")
        if not plan.is_file():
            errors.append(f"{plan.relative_to(root)}: lane M requires plan.md")
        elif line_count(plan) > 250:
            errors.append(f"{plan.relative_to(root)}: lane M plan is {line_count(plan)} lines; limit is 250")
    elif lane == "L" and not plan.is_file():
        errors.append(f"{plan.relative_to(root)}: lane L requires plan.md")

    ac_ids = acceptance_criterion_ids(spec_text[frontmatter.end() :])
    if not ac_ids:
        errors.append(
            f"{spec.relative_to(root)}: no acceptance-criterion definitions found in an Acceptance Criteria section"
        )
    if not tasks.is_file():
        errors.append(f"{tasks.relative_to(root)}: feature is missing tasks.md")
    else:
        rows, map_errors = parse_validation_map(tasks)
        errors.extend(f"{tasks.relative_to(root)}: {error}" for error in map_errors)
        missing = sorted(ac_ids - set(rows))
        if missing:
            errors.append(f"{tasks.relative_to(root)}: validation map is missing {', '.join(missing)}")
    return errors


def validate_verify_log(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    entry_count = 0
    for index, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        entry_count += 1
        relative = path.relative_to(root)
        match = VERIFY_HEADER.fullmatch(line)
        if not match:
            errors.append(f"{relative}:{index + 1}: invalid verify-log header")
            continue
        if match.group("result") == "PASSED" and match.group("reason"):
            errors.append(f"{relative}:{index + 1}: PASSED header must not include a blocking reason")
        if match.group("result") == "BLOCKED" and not match.group("reason"):
            errors.append(f"{relative}:{index + 1}: BLOCKED header requires a reason")
        iids = match.group("iids").split(", ")
        if int(match.group("count")) != len(iids):
            errors.append(f"{relative}:{index + 1}: MR count does not match IID list")
        gates_index = index + 1
        while gates_index < len(lines) and not lines[gates_index].strip():
            gates_index += 1
        if gates_index >= len(lines) or not GATES_LINE.fullmatch(lines[gates_index]):
            errors.append(f"{relative}:{gates_index + 1}: invalid or missing gates line")
        else:
            gates = GATES_LINE.fullmatch(lines[gates_index])
            assert gates
            if gates.group("lane") != match.group("lane"):
                errors.append(f"{relative}:{gates_index + 1}: gates lane does not match header")
    if not entry_count:
        errors.append(f"{path.relative_to(root)}: no verify entries found")
    return errors


def check_target(root: Path, feature_name: str | None = None) -> list[str]:
    errors: list[str] = []
    specs = root / "specs"
    if not specs.is_dir():
        return ["target project has no specs directory"]
    if feature_name:
        if not FEATURE_DIR.fullmatch(feature_name):
            return [f"invalid feature name {feature_name!r}; expected NNN-kebab-slug"]
        feature = specs / feature_name
        if not (feature / "spec.md").is_file():
            return [f"specs/{feature_name}: current S/M/L feature is missing spec.md"]
        features = [feature]
    else:
        features = sorted(
            path
            for path in specs.iterdir()
            if path.is_dir() and FEATURE_DIR.fullmatch(path.name) and (path / "spec.md").is_file()
        )
    for feature in features:
        errors.extend(validate_feature(feature, root))
    verify_log = specs / "verify-log.md"
    if not feature_name and verify_log.exists():
        errors.extend(validate_verify_log(verify_log, root))
    return errors


def check(root: Path) -> list[str]:
    errors = validate_agent_names(root)
    errors.extend(validate_skill_mirrors(root))
    errors.extend(run_generated_port_checks(root))
    errors.extend(validate_generated_gitlab_wiring(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=argparse.SUPPRESS)
    parser.add_argument(
        "--target-root",
        type=Path,
        help="validate active SDD artifacts under a target project's specs directory",
    )
    parser.add_argument(
        "--feature",
        help="with --target-root, validate only the current NNN-slug feature and skip historical verify-log entries",
    )
    args = parser.parse_args()
    if args.feature and not args.target_root:
        parser.error("--feature requires --target-root")
    root = (args.target_root or args.root).resolve()
    errors = check_target(root, args.feature) if args.target_root else check(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Target SDD artifacts are valid" if args.target_root else "Harness configuration is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
