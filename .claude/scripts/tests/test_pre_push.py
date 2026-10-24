from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[3] / ".githooks" / "pre-push"
ZERO = "0" * 40


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


class PrePushTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.remote = root / "remote.git"
        self.clone = root / "clone"
        git(root, "init", "-q", "--bare", "-b", "main", str(self.remote))
        git(root, "clone", "-q", str(self.remote), str(self.clone))
        self.commit("first")
        git(self.clone, "push", "-q", "origin", "main")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def commit(self, name: str) -> None:
        (self.clone / name).write_text(name)
        git(self.clone, "add", name)
        git(self.clone, "commit", "-q", "-m", name)

    def run_hook(self, branch: str = "main", env: dict | None = None) -> subprocess.CompletedProcess:
        local = git(self.clone, "rev-parse", "HEAD")
        remote = subprocess.run(
            ["git", "rev-parse", f"origin/{branch}"], cwd=self.clone, capture_output=True, text=True
        ).stdout.strip() or ZERO
        line = f"refs/heads/{branch} {local} refs/heads/{branch} {remote}\n"
        merged = {key: value for key, value in os.environ.items() if key != "HARNESS_PUSH_COUNT"}
        merged.update(env or {})
        return subprocess.run(
            [str(HOOK), "origin", str(self.remote)],
            cwd=self.clone, input=line, capture_output=True, text=True, env=merged,
        )

    def test_one_commit_to_main_passes(self) -> None:
        self.commit("second")
        self.assertEqual(self.run_hook().returncode, 0)

    def test_two_commits_to_main_are_blocked_and_listed(self) -> None:
        self.commit("second")
        self.commit("third")
        result = self.run_hook()
        self.assertEqual(result.returncode, 1)
        self.assertIn("2 commits", result.stderr)
        self.assertIn("third", result.stderr)

    def test_confirmed_count_passes(self) -> None:
        self.commit("second")
        self.commit("third")
        self.assertEqual(self.run_hook(env={"HARNESS_PUSH_COUNT": "2"}).returncode, 0)

    def test_wrong_count_stays_blocked(self) -> None:
        self.commit("second")
        self.commit("third")
        self.assertEqual(self.run_hook(env={"HARNESS_PUSH_COUNT": "1"}).returncode, 1)

    def test_feature_branch_with_many_commits_passes(self) -> None:
        git(self.clone, "checkout", "-q", "-b", "feature")
        self.commit("second")
        self.commit("third")
        self.commit("fourth")
        self.assertEqual(self.run_hook(branch="feature").returncode, 0)


if __name__ == "__main__":
    unittest.main()
