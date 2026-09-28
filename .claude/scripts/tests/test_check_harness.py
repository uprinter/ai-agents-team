from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "check_harness.py"
SPEC = importlib.util.spec_from_file_location("check_harness", SCRIPT)
assert SPEC and SPEC.loader
check_harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_harness)


class HarnessCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_agent(self, filename: str, name: str) -> None:
        path = self.root / ".claude" / "agents" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nname: "{name}"\ndescription: test\ntools: Read\nmodel: sonnet\n'
            'skills:\n  - gitlab-access\ncolor: blue\n---\n'
            'Before any GitLab API or authenticated Git transport operation, follow the preloaded '
            '`gitlab-access` skill. If it is not preloaded, read and follow '
            '`${CLAUDE_PLUGIN_ROOT}/.claude/skills/gitlab-access/SKILL.md` directly.\nPrompt\n',
            encoding="utf-8",
        )

    def write_generated_gitlab_wiring(
        self,
        stem: str,
        *,
        codex_trigger: bool = True,
        opencode_skill: bool = True,
    ) -> None:
        codex = self.root / ".codex" / "agents" / f"{stem}.toml"
        codex.parent.mkdir(parents=True, exist_ok=True)
        trigger = (
            "`$gitlab-access` from `.agents/skills/gitlab-access/SKILL.md`.\n"
            if codex_trigger
            else "No shared skill trigger.\n"
        )
        codex.write_text(
            f"developer_instructions = '''## Codex runtime notes\n{trigger}"
            "<!-- END CODEX RUNTIME NOTES -->\n'''\n",
            encoding="utf-8",
        )

        opencode = self.root / ".opencode" / "agent" / f"{stem}.md"
        opencode.parent.mkdir(parents=True, exist_ok=True)
        skills = "`gitlab-access`, `team-wiki`" if opencode_skill else "`team-wiki`"
        opencode.write_text(
            "## Load these skills first\n\n"
            f"Load these with the `skill` tool: {skills}. Their rules bind you.\n\n"
            "Agent body.\n",
            encoding="utf-8",
        )

    def add_skill(self, name: str) -> None:
        real = self.root / ".agents" / "skills" / name
        mirror = self.root / ".claude" / "skills" / name
        real.mkdir(parents=True)
        (real / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.symlink_to(real)

    def add_sync_script(self, directory: str, exit_code: int = 0) -> None:
        path = self.root / directory / "sync-agents.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "import sys\n"
            "assert sys.argv[1:] == ['--check']\n"
            f"raise SystemExit({exit_code})\n",
            encoding="utf-8",
        )

    def write_feature(
        self,
        lane: str,
        *,
        spec_body: str = "## Acceptance Criteria\n\n- AC-1.1 works\n",
        tasks_body: str | None = None,
        plan_body: str | None = None,
    ) -> Path:
        feature = self.root / "specs" / "001-example"
        feature.mkdir(parents=True, exist_ok=True)
        (feature / "spec.md").write_text(
            f"---\nsize: {lane}\nstatus: Draft\n---\n{spec_body}",
            encoding="utf-8",
        )
        if tasks_body is None:
            tasks_body = (
                "# Tasks\n\n"
                "| AC | Method | Stage | Evidence | Owner |\n"
                "|---|---|---|---|---|\n"
                "| `AC-1.1` | `pytest tests/test_feature.py` in job `test` | `CI` | job `test` output | engineer |\n"
            )
        (feature / "tasks.md").write_text(tasks_body, encoding="utf-8")
        if plan_body is not None:
            (feature / "plan.md").write_text(plan_body, encoding="utf-8")
        return feature

    def write_verify_log(self, gates: str | None = None) -> None:
        specs = self.root / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        gates = gates or (
            "gates: lane=S budget=20/120 tasks.md=yes status=Active mrs=1/1 "
            "worktrees=clean design=n/a copy=n/a live=n/a ci=pass tier=1 gap=20s/15s"
        )
        (specs / "verify-log.md").write_text(
            "# Verification log\n\n"
            "## 001-example — PASSED 2026-09-24 · lane S · 1 MR(s) (!12)\n\n"
            f"{gates}\n\n"
            "- **Open follow-ups:** none.\n",
            encoding="utf-8",
        )

    def test_valid_agent_name_and_skill_mirror(self) -> None:
        self.write_agent("builder.md", "builder")
        self.add_skill("testing")

        self.assertEqual([], check_harness.validate_agent_names(self.root))
        self.assertEqual([], check_harness.validate_skill_mirrors(self.root))

    def test_agent_name_must_match_filename(self) -> None:
        self.write_agent("builder.md", "reviewer")

        errors = check_harness.validate_agent_names(self.root)

        self.assertTrue(any("does not match filename" in error for error in errors))

    def test_agent_requires_shared_gitlab_access_skill(self) -> None:
        self.write_agent("builder.md", "builder")
        path = self.root / ".claude" / "agents" / "builder.md"
        text = path.read_text(encoding="utf-8").replace("skills:\n  - gitlab-access\n", "")
        path.write_text(text, encoding="utf-8")

        errors = check_harness.validate_agent_names(self.root)

        self.assertIn(
            ".claude/agents/builder.md: skills must include gitlab-access",
            errors,
        )

    def test_agent_requires_inline_gitlab_trigger_for_main_session(self) -> None:
        self.write_agent("builder.md", "builder")
        path = self.root / ".claude" / "agents" / "builder.md"
        text = path.read_text(encoding="utf-8").replace(
            "If it is not preloaded, read and follow "
            "`${CLAUDE_PLUGIN_ROOT}/.claude/skills/gitlab-access/SKILL.md` directly.",
            "",
        )
        path.write_text(text, encoding="utf-8")

        errors = check_harness.validate_agent_names(self.root)

        self.assertIn(
            ".claude/agents/builder.md: body must include the GitLab access load trigger",
            errors,
        )

    def test_agent_frontmatter_requires_documented_keys(self) -> None:
        self.write_agent("builder.md", "builder")
        path = self.root / ".claude" / "agents" / "builder.md"
        path.write_text(path.read_text(encoding="utf-8").replace("model: sonnet\n", ""), encoding="utf-8")

        errors = check_harness.validate_agent_names(self.root)

        self.assertIn(
            ".claude/agents/builder.md: frontmatter must contain exactly one model field",
            errors,
        )

    def test_agent_frontmatter_allows_optional_tools_and_color_to_be_absent(self) -> None:
        self.write_agent("builder.md", "builder")
        path = self.root / ".claude" / "agents" / "builder.md"
        text = path.read_text(encoding="utf-8").replace("tools: Read\n", "").replace("color: blue\n", "")
        path.write_text(text, encoding="utf-8")

        self.assertEqual([], check_harness.validate_agent_names(self.root))

    def test_skill_requires_one_matching_symlink(self) -> None:
        left = self.root / ".agents" / "skills" / "testing"
        right = self.root / ".claude" / "skills" / "testing"
        left.mkdir(parents=True)
        right.mkdir(parents=True)
        (left / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
        (right / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

        errors = check_harness.validate_skill_mirrors(self.root)

        self.assertIn("skill 'testing': exactly one entry must be a symlink", errors)

    def test_generated_port_checks_invoke_both_scripts(self) -> None:
        self.add_sync_script(".codex")
        self.add_sync_script(".opencode")

        self.assertEqual([], check_harness.run_generated_port_checks(self.root))

    def test_generated_port_check_reports_failure(self) -> None:
        self.add_sync_script(".codex", exit_code=1)
        self.add_sync_script(".opencode")

        errors = check_harness.run_generated_port_checks(self.root)

        self.assertEqual([".codex/sync-agents.py --check failed"], errors)

    def test_generated_gitlab_wiring_accepts_both_runtime_triggers(self) -> None:
        self.write_agent("builder.md", "builder")
        self.write_generated_gitlab_wiring("builder")

        self.assertEqual([], check_harness.validate_generated_gitlab_wiring(self.root))

    def test_generated_gitlab_wiring_requires_codex_runtime_trigger(self) -> None:
        self.write_agent("builder.md", "builder")
        self.write_generated_gitlab_wiring("builder", codex_trigger=False)

        errors = check_harness.validate_generated_gitlab_wiring(self.root)

        self.assertIn(
            ".codex/agents/builder.toml: Codex runtime notes must load gitlab-access",
            errors,
        )

    def test_generated_gitlab_wiring_requires_opencode_skill_loader_entry(self) -> None:
        self.write_agent("builder.md", "builder")
        self.write_generated_gitlab_wiring("builder", opencode_skill=False)

        errors = check_harness.validate_generated_gitlab_wiring(self.root)

        self.assertIn(
            ".opencode/agent/builder.md: OpenCode skill loader must include gitlab-access",
            errors,
        )

    def test_target_mode_accepts_lane_s_and_verify_log(self) -> None:
        self.write_feature("S")
        self.write_verify_log()

        self.assertEqual([], check_harness.check_target(self.root))

    def test_target_mode_accepts_lane_m_with_plan(self) -> None:
        self.write_feature("M", plan_body="# Plan\n\nImplementation details.\n")

        self.assertEqual([], check_harness.check_target(self.root))

    def test_target_mode_rejects_missing_size_frontmatter(self) -> None:
        feature = self.write_feature("S")
        (feature / "spec.md").write_text("---\nstatus: Draft\n---\nAC-1.1 works\n", encoding="utf-8")

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("frontmatter must contain one size field" in error for error in errors))

    def test_target_mode_rejects_missing_status_frontmatter(self) -> None:
        feature = self.write_feature("S")
        spec = feature / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8").replace("status: Draft\n", ""), encoding="utf-8")

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("exactly one status field" in error for error in errors))

    def test_target_mode_rejects_duplicate_status_frontmatter(self) -> None:
        feature = self.write_feature("S")
        spec = feature / "spec.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("status: Draft\n", "status: Draft\nstatus: Active\n"),
            encoding="utf-8",
        )

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("exactly one status field" in error for error in errors))

    def test_target_mode_rejects_archived_status_in_active_directory(self) -> None:
        feature = self.write_feature("S")
        spec = feature / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8").replace("status: Draft", "status: Historic"), encoding="utf-8")

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("exactly one status field" in error for error in errors))

    def test_target_mode_rejects_lane_s_plan_and_incomplete_map(self) -> None:
        self.write_feature(
            "S",
            spec_body="## Acceptance Criteria\n\n- AC-1.1 works\n- AC-1.2 fails safely\n",
            plan_body="# Plan\n",
        )

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("lane S must not have plan.md" in error for error in errors))
        self.assertTrue(any("validation map is missing AC-1.2" in error for error in errors))

    def test_target_mode_ignores_ac_references_outside_definition_section(self) -> None:
        self.write_feature(
            "S",
            spec_body=(
                "## Acceptance Criteria\n\n"
                "- AC-1.1 works\n\n"
                "## Decisions\n\n"
                "This partially supersedes AC-9.4 from an earlier feature.\n"
            ),
        )

        self.assertEqual([], check_harness.check_target(self.root))

    def test_target_mode_parses_numbered_acceptance_section_and_ac_subheading(self) -> None:
        self.write_feature(
            "S",
            spec_body=(
                "## 8. Acceptance Criteria (Given / When / Then)\n\n"
                "### AC-1 — Happy path\n\n"
                "- **Given** the service is running\n"
                "- **When** a request arrives\n"
                "- **Then** it succeeds\n"
            ),
            tasks_body=(
                "# Tasks\n\n"
                "| AC | Method | Stage | Evidence | Owner |\n"
                "|---|---|---|---|---|\n"
            ),
        )

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("validation map is missing AC-1" in error for error in errors))

    def test_target_mode_rejects_unparsed_acceptance_format_with_empty_map(self) -> None:
        self.write_feature(
            "S",
            spec_body="## 8) Acceptance Criteria\n\nCriterion one works.\n",
            tasks_body=(
                "# Tasks\n\n"
                "| AC | Method | Stage | Evidence | Owner |\n"
                "|---|---|---|---|---|\n"
            ),
        )

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("no acceptance-criterion definitions found" in error for error in errors))

    def test_target_mode_explicitly_excludes_spec_less_xs_directory(self) -> None:
        feature = self.root / "specs" / "001-doc-cleanup"
        feature.mkdir(parents=True)
        (feature / "tasks.md").write_text("# Tasks\n\n| Task | Lane |\n|---|---|\n| Update docs | XS |\n")

        self.assertEqual([], check_harness.check_target(self.root))

    def test_target_feature_filter_skips_immutable_legacy_artifacts(self) -> None:
        self.write_feature("S")
        legacy = self.root / "specs" / "002-legacy"
        legacy.mkdir()
        (legacy / "spec.md").write_text("---\nsize: S\n---\n## Acceptance Criteria\n\n- AC-2 works\n")
        (legacy / "tasks.md").write_text("# Tasks without a validation map\n")
        (self.root / "specs" / "verify-log.md").write_text("## legacy invalid entry\n")

        self.assertEqual([], check_harness.check_target(self.root, "001-example"))

    def test_target_mode_rejects_lane_m_budgets_and_missing_plan(self) -> None:
        feature = self.write_feature("M")
        spec = feature / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8") + "detail\n" * 250, encoding="utf-8")

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("lane M spec is" in error for error in errors))
        self.assertTrue(any("lane M requires plan.md" in error for error in errors))

    def test_target_mode_rejects_lane_s_spec_over_budget(self) -> None:
        feature = self.write_feature("S")
        spec = feature / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8") + "detail\n" * 120, encoding="utf-8")

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("lane S spec is" in error for error in errors))

    def test_target_mode_rejects_lane_m_plan_over_budget(self) -> None:
        self.write_feature("M", plan_body="plan detail\n" * 251)

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("lane M plan is 251 lines; limit is 250" in error for error in errors))

    def test_target_mode_rejects_invalid_verify_gates(self) -> None:
        self.write_feature("S")
        self.write_verify_log(
            "gates: lane=S budget=20/120 tasks.md=yes status=Active mrs=1/1 "
            "worktrees=clean design=n/a copy=n/a live=n/a tier=1 gap=20s/15s"
        )

        errors = check_harness.check_target(self.root)

        self.assertTrue(any("invalid or missing gates line" in error for error in errors))

    def test_target_mode_accepts_superseded_verify_status(self) -> None:
        self.write_feature("S")
        self.write_verify_log(
            "gates: lane=S budget=20/120 tasks.md=yes status=Superseded-by: 002 mrs=1/1 "
            "worktrees=clean design=n/a copy=n/a live=n/a ci=pass tier=1 gap=20s/15s"
        )

        self.assertEqual([], check_harness.check_target(self.root))

    def test_target_mode_accepts_singular_mr_header(self) -> None:
        self.write_feature("S")
        self.write_verify_log()
        path = self.root / "specs" / "verify-log.md"
        path.write_text(path.read_text(encoding="utf-8").replace("1 MR(s)", "1 MR"), encoding="utf-8")

        self.assertEqual([], check_harness.check_target(self.root))

    def test_target_mode_accepts_plural_mrs_header(self) -> None:
        self.write_feature("S")
        self.write_verify_log(
            "gates: lane=S budget=20/120 tasks.md=yes status=Active mrs=2/2 "
            "worktrees=clean design=n/a copy=n/a live=n/a ci=pass "
            "tiers=!12:0,!13:2 gap=!12:n/a,!13:130s/120s"
        )
        path = self.root / "specs" / "verify-log.md"
        text = path.read_text(encoding="utf-8").replace("1 MR(s) (!12)", "2 MRs (!12, !13)")
        path.write_text(text, encoding="utf-8")

        self.assertEqual([], check_harness.check_target(self.root))


if __name__ == "__main__":
    unittest.main()
