from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "push_mr.py"
SPEC = importlib.util.spec_from_file_location("push_mr", SCRIPT)
assert SPEC and SPEC.loader
push_mr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(push_mr)

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
ALLOWED_GIT = {"branch", "rev-parse", "ls-remote", "status", "diff", "add", "commit", "push"}


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=GIT_ENV, check=True)
    return done.stdout.strip()


class Fixture:
    """A work repo on a feature branch with a bare remote; glab is faked."""

    def __init__(self, tmp: Path) -> None:
        self.remote = tmp / "origin.git"
        self.work = tmp / "work"
        self.work.mkdir()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True)
        git(self.work, "init", "-q", "-b", "main")
        git(self.work, "remote", "add", "origin", str(self.remote))
        (self.work / "a.txt").write_text("a\n")
        (self.work / "b.txt").write_text("b\n")
        git(self.work, "add", ".")
        git(self.work, "commit", "-q", "-m", "init")
        git(self.work, "push", "-q", "origin", "main")
        git(self.work, "checkout", "-q", "-b", "feature/x")
        self.message = tmp / "msg.txt"
        self.message.write_text("feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
        self.description = tmp / "desc.md"
        self.description.write_text("MR text\n")
        self.commands: list[list[str]] = []
        self.glab_auth_ok = True

    def runner(self, cmd):
        cmd = list(cmd)
        self.commands.append(cmd)
        if cmd[0] == "glab":
            if cmd[1:3] == ["auth", "status"]:
                return (0 if self.glab_auth_ok else 1), ""
            if cmd[1:3] == ["mr", "create"]:
                return 0, "https://example.com/mr/1"
            raise AssertionError(f"unexpected glab call: {cmd}")
        return push_mr.subprocess_runner(cmd)

    def job(self, **extra) -> dict:
        job = {
            "worktree": str(self.work),
            "branch": "feature/x",
            "paths": ["a.txt"],
            "message_file": str(self.message),
            "mode": "new",
        }
        job.update(extra)
        return job

    def remote_branch(self) -> str:
        return git(self.remote, "rev-parse", "--verify", "-q", "refs/heads/feature/x") if self._has_branch() else ""

    def _has_branch(self) -> bool:
        return subprocess.run(["git", "rev-parse", "--verify", "-q", "refs/heads/feature/x"], cwd=self.remote, capture_output=True).returncode == 0


class PushMrTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patch = mock.patch.dict(os.environ, GIT_ENV)  # the helper's own runner makes the commit
        patch.start()
        self.addCleanup(patch.stop)
        self.fx = Fixture(Path(self._tmp.name))
        (self.fx.work / "a.txt").write_text("a changed\n")

    def run_job(self, job: dict, dry_run: bool = False) -> list[str]:
        lines: list[str] = []
        push_mr.execute(job, self.fx.runner, dry_run, lines.append)
        return lines

    def test_new_branch_is_committed_pushed_and_verified(self) -> None:
        lines = self.run_job(self.fx.job())
        head = git(self.fx.work, "rev-parse", "HEAD")
        self.assertEqual(self.fx.remote_branch(), head)
        self.assertIn(f"pushed and verified: {head}", lines)
        self.assertEqual(git(self.fx.work, "show", "-s", "--format=%b", "HEAD").strip(), "Co-Authored-By: Claude <noreply@anthropic.com>")

    def test_mr_is_opened_when_the_job_names_one(self) -> None:
        mr = {"repo": "g/p", "title": "T", "description_file": str(self.fx.description), "squash": True, "remove_source": True}
        self.run_job(self.fx.job(mr=mr))
        create = [c for c in self.fx.commands if c[:3] == ["glab", "mr", "create"]]
        self.assertEqual(len(create), 1)
        self.assertIn("--squash-before-merge", create[0])
        self.assertIn("--remove-source-branch", create[0])
        self.assertEqual(create[0][-1], "--yes")

    def test_dry_run_changes_nothing(self) -> None:
        before = git(self.fx.work, "rev-parse", "HEAD")
        lines = self.run_job(self.fx.job(), dry_run=True)
        self.assertEqual(git(self.fx.work, "rev-parse", "HEAD"), before)
        self.assertEqual(self.fx.remote_branch(), "")
        self.assertTrue(lines[0].startswith("DRY RUN"))
        self.assertTrue(any("a.txt" in line for line in lines))

    def test_stops_when_the_remote_branch_exists(self) -> None:
        git(self.fx.work, "push", "-q", "origin", "HEAD:refs/heads/feature/x")
        with self.assertRaisesRegex(push_mr.Stop, "remote branch exists"):
            self.run_job(self.fx.job())

    def test_stops_on_an_unexpected_file(self) -> None:
        (self.fx.work / "stray.txt").write_text("x\n")
        with self.assertRaisesRegex(push_mr.Stop, "unexpected files: stray.txt"):
            self.run_job(self.fx.job())

    def test_stops_when_a_listed_path_did_not_change(self) -> None:
        with self.assertRaisesRegex(push_mr.Stop, "listed but unchanged: b.txt"):
            self.run_job(self.fx.job(paths=["a.txt", "b.txt"]))

    def test_stops_on_the_wrong_branch(self) -> None:
        with self.assertRaisesRegex(push_mr.Stop, "not on feature/y"):
            self.run_job(self.fx.job(branch="feature/y"))

    def test_stops_when_glab_is_not_signed_in(self) -> None:
        self.fx.glab_auth_ok = False
        with self.assertRaisesRegex(push_mr.Stop, "glab auth failed"):
            self.run_job(self.fx.job())

    def test_fix_mode_needs_both_heads_at_the_prior_sha(self) -> None:
        self.run_job(self.fx.job())
        prior = git(self.fx.work, "rev-parse", "HEAD")
        (self.fx.work / "a.txt").write_text("a fixed\n")
        self.run_job(self.fx.job(mode="fix", prior_sha=prior))
        self.assertEqual(self.fx.remote_branch(), git(self.fx.work, "rev-parse", "HEAD"))
        (self.fx.work / "a.txt").write_text("a fixed again\n")
        with self.assertRaisesRegex(push_mr.Stop, "local HEAD is not"):
            self.run_job(self.fx.job(mode="fix", prior_sha=prior))

    def test_fix_mode_reports_whether_the_files_were_already_in_the_mr(self) -> None:
        git(self.fx.work, "push", "-q", "origin", "main")  # origin/main exists for the three-dot diff
        git(self.fx.work, "fetch", "-q", "origin")
        self.run_job(self.fx.job())
        prior = git(self.fx.work, "rev-parse", "HEAD")
        (self.fx.work / "a.txt").write_text("a fixed\n")
        lines = self.run_job(self.fx.job(mode="fix", prior_sha=prior))
        self.assertIn("review fix inside the files already in the MR (decision-protocol 1d): yes", lines)

    def test_only_allowed_commands_are_ever_built(self) -> None:
        mr = {"repo": "g/p", "title": "T", "description_file": str(self.fx.description)}
        self.run_job(self.fx.job(mr=mr))
        for cmd in self.fx.commands:
            if cmd[0] == "glab":
                self.assertIn(cmd[1:3], (["auth", "status"], ["mr", "create"]))
            else:
                verb = next(arg for arg in cmd[3:] if not arg.startswith("-") and arg != "credential.helper=" and not arg.startswith("credential.helper="))
                self.assertIn(verb, ALLOWED_GIT)
                self.assertNotIn("--force", cmd)
                self.assertNotIn("--force-with-lease", cmd)

    def test_source_has_no_merge_apply_or_force_path(self) -> None:
        source = SCRIPT.read_text()
        code = source.split('"""', 2)[2]
        for word in ('"merge"', "'merge'", '"apply"', "--force", "tofu", "kubectl"):
            self.assertNotIn(word, code)


class LoadJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.message = self.tmp / "m.txt"
        self.message.write_text("m\n")

    def write(self, **fields) -> Path:
        job = {"worktree": "/w", "branch": "b", "paths": ["a"], "message_file": str(self.message), "mode": "new"}
        job.update(fields)
        path = self.tmp / "job.json"
        path.write_text(json.dumps(job))
        return path

    def test_a_valid_job_loads(self) -> None:
        self.assertEqual(push_mr.load_job(self.write())["branch"], "b")

    def test_bad_jobs_are_refused(self) -> None:
        for fields in (
            {"mode": "merge"},
            {"mode": "fix"},
            {"mode": "fix", "prior_sha": "abc"},
            {"paths": []},
            {"paths": ["/etc/passwd"]},
            {"paths": ["../x"]},
            {"message_file": str(self.tmp / "missing.txt")},
            {"mr": {"repo": "g/p", "title": "T"}},
        ):
            with self.subTest(fields=fields), self.assertRaises(push_mr.BadJob):
                push_mr.load_job(self.write(**fields))

    def test_missing_key_is_refused(self) -> None:
        path = self.tmp / "job.json"
        path.write_text(json.dumps({"worktree": "/w"}))
        with self.assertRaisesRegex(push_mr.BadJob, "missing key"):
            push_mr.load_job(path)


if __name__ == "__main__":
    unittest.main()
