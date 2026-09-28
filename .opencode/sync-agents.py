#!/usr/bin/env python3
"""Regenerate .opencode/agent/*.md from .claude/agents/*.md.

OpenCode rejects Claude Code's agent frontmatter: `tools` must be an object,
`color` must come from a fixed palette, and `model`/`effort`/`skills` mean
nothing to it. Run this after editing any file in .claude/agents/.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / ".claude" / "agents"
DST = ROOT / ".opencode" / "agent"

COLOR = {"purple": "accent", "pink": "accent", "red": "error", "green": "success",
         "yellow": "warning", "orange": "warning", "blue": "info", "cyan": "info"}
DROP = ("name:", "tools:", "model:", "effort:")
PRIMARY = {"team-lead-coordinator"}

RUNTIME = """
## OpenCode runtime notes

This file is generated from `.claude/agents/{stem}.md`. Edit that file, then run
`.opencode/sync-agents.py`. Everything after these notes is the Claude Code prompt verbatim.

Vocabulary differs in OpenCode. Where the prompt says:

- "the Agent tool" or "the Task tool" — use the `task` tool.
- "subagent_type" — use the agent name.
- "TodoWrite" — use `todowrite`.
- "Claude Code Agent Teams", `TeamCreate`, `SendMessage` — not available here. Always
  use the documented fallback: spawn one-shot subagents with `task`.
"""

SKILLS = """
## Load these skills first

OpenCode does not preload skills from frontmatter. Before you start work, load each of
these with the `skill` tool: {names}. Their rules bind you exactly as if written here.
"""


def convert(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        sys.exit(f"no frontmatter in {path}")
    head, body = m.group(1), m.group(2)

    out, skills, in_skills = [], [], False
    for line in head.split("\n"):
        if in_skills:
            if line.startswith("  - "):
                skills.append(line[4:].strip())
                continue
            in_skills = False
        if line.startswith("skills:"):
            in_skills = True
            continue
        if line.startswith(DROP):
            continue
        if line.startswith("color:"):
            name = line.split(":", 1)[1].strip()
            if name in COLOR:
                out.append(f"color: {COLOR[name]}")
            continue
        out.append(line)

    stem = path.stem
    out.append(f"mode: {'all' if stem in PRIMARY else 'subagent'}")

    prefix = RUNTIME.format(stem=stem)
    if skills:
        prefix += SKILLS.format(names=", ".join(f"`{s}`" for s in skills))

    return "---\n" + "\n".join(out) + "\n---\n" + prefix + "\n" + body


def expected_outputs():
    return {DST / src.name: convert(src) for src in sorted(SRC.glob("*.md"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated agents are stale")
    args = parser.parse_args()

    expected = expected_outputs()
    actual = set(DST.glob("*.md")) if DST.is_dir() else set()
    unexpected = actual - set(expected)
    drifted = [
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text() != content
    ]

    if args.check:
        for path in sorted(drifted):
            print(f"stale: {path.relative_to(ROOT)}")
        for path in sorted(unexpected):
            print(f"unexpected: {path.relative_to(ROOT)}")
        if drifted or unexpected:
            return 1
        print(f"{len(expected)} OpenCode agent profile(s) valid and in sync")
        return 0

    DST.mkdir(parents=True, exist_ok=True)
    for stale in sorted(unexpected):
        stale.unlink()
    for path, content in expected.items():
        path.write_text(content)
        print(f"{path.name} -> .opencode/agent/{path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
