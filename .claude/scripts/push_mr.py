#!/usr/bin/env python3
"""Commit a branch's files, push the exact SHA and open the MR, from one job file.

One reviewed helper replaces a hand-written commit-and-push script per branch. The
founder approves one line, ``python3 push_mr.py <job.json>``, and the reviewer of
that line reads the job file (data), or the output of ``--dry-run``, not shell code.

Job file (JSON):
  worktree         absolute path of the git worktree
  branch           the branch checked out there
  paths            files to commit, relative to the worktree; each must have changed
  message_file     the commit message, trailer lines included
  mode             "new" (the branch is not on the remote) or "fix" (a review fix)
  prior_sha        "fix" only: local HEAD and the remote branch must both equal it
  base             target branch, default "main"
  mr               optional: {repo, title, description_file, squash, remove_source}

The helper never merges, applies or force-pushes: no code path builds such a command.
Exit codes: 0 done, 1 stopped by a check (STOP line), 2 bad job file.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

CREDENTIALS = ["-c", "credential.helper=", "-c", "credential.helper=!glab auth git-credential"]
SHA = re.compile(r"^[0-9a-f]{40}$")

Runner = Callable[[Sequence[str]], "tuple[int, str]"]


class Stop(Exception):
    """A check failed: nothing further runs."""


class BadJob(Exception):
    """The job file is not usable."""


def subprocess_runner(cmd: Sequence[str]) -> tuple[int, str]:
    done = subprocess.run(list(cmd), capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr).rstrip("\n")  # keep a leading space: porcelain status columns


def load_job(path: Path) -> dict:
    try:
        job = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise BadJob(f"cannot read {path}: {error}") from error
    for key in ("worktree", "branch", "paths", "message_file", "mode"):
        if key not in job:
            raise BadJob(f"missing key: {key}")
    if job["mode"] not in ("new", "fix"):
        raise BadJob('mode must be "new" or "fix"')
    if job["mode"] == "fix" and not SHA.match(str(job.get("prior_sha", ""))):
        raise BadJob('mode "fix" needs a 40-hex prior_sha')
    paths = job["paths"]
    if not paths or not all(isinstance(p, str) and p and not p.startswith("/") and ".." not in Path(p).parts for p in paths):
        raise BadJob("paths must be a non-empty list of relative paths without '..'")
    if not Path(job["message_file"]).is_file():
        raise BadJob(f"message_file not found: {job['message_file']}")
    mr = job.get("mr")
    if mr is not None and (not {"repo", "title", "description_file"} <= set(mr) or not Path(mr["description_file"]).is_file()):
        raise BadJob("mr needs repo, title and an existing description_file")
    return job


def changed_paths(status: str) -> list[tuple[str, str]]:
    """(status code, path) from ``git status --porcelain`` output; a rename keeps its new path."""
    entries = []
    for line in status.splitlines():
        if len(line) > 3:
            entries.append((line[:2], line[3:].split(" -> ")[-1]))
    return entries


def execute(job: dict, runner: Runner = subprocess_runner, dry_run: bool = False, out=print) -> None:
    worktree, branch, mode = job["worktree"], job["branch"], job["mode"]
    paths, base = job["paths"], job.get("base", "main")
    ref = f"refs/heads/{branch}"

    def git(*args: str) -> tuple[int, str]:
        return runner(["git", "-C", worktree, *args])

    def remote_head() -> str:
        rc, text = git(*CREDENTIALS, "ls-remote", "--heads", "origin", ref)
        return text.split()[0] if rc == 0 and text else ""

    if runner(["glab", "auth", "status"])[0] != 0:
        raise Stop("glab auth failed")
    if git("branch", "--show-current")[1] != branch:
        raise Stop(f"the worktree is not on {branch}")

    remote = remote_head()
    if mode == "new":
        if remote:
            raise Stop(f"the remote branch exists at {remote}")
    else:
        prior = job["prior_sha"]
        if git("rev-parse", "HEAD")[1] != prior:
            raise Stop(f"local HEAD is not {prior}")
        if remote != prior:
            raise Stop(f"remote head is '{remote}', not {prior}")

    entries = changed_paths(git("status", "--porcelain", "--untracked-files=all")[1])
    stray = sorted({path for _, path in entries} - set(paths))
    if stray:
        raise Stop(f"unexpected files: {', '.join(stray)}")
    unchanged = sorted(set(paths) - {path for _, path in entries})
    if unchanged:
        raise Stop(f"listed but unchanged: {', '.join(unchanged)}")

    covered = None
    if mode == "fix":
        rc, in_mr = git("diff", "--name-only", f"origin/{base}...{job['prior_sha']}")
        covered = set(paths) <= set(in_mr.split()) if rc == 0 else None

    message = Path(job["message_file"]).read_text()
    if dry_run:
        out(f"DRY RUN, nothing changed. branch {branch} ({mode}), base {base}")
        for code, path in entries:
            out(f"  {code} {path}")
        out("commit message:")
        out("  " + message.strip().replace("\n", "\n  "))
        if job.get("mr"):
            out(f"MR in {job['mr']['repo']}: {job['mr']['title']}")
        if covered is not None:
            out(f"review fix inside the files already in the MR (decision-protocol 1d): {'yes' if covered else 'NO'}")
        return

    git("add", "--", *paths)
    staged = set(git("diff", "--cached", "--name-only")[1].split())
    if staged != set(paths):
        raise Stop(f"staged files differ from the job: {sorted(staged ^ set(paths))}")
    if git("commit", "-q", "-F", job["message_file"])[0] != 0:
        raise Stop("git commit failed")
    sha = git("rev-parse", "HEAD")[1]
    if git(*CREDENTIALS, "push", "-q", "origin", f"{sha}:{ref}")[0] != 0:
        raise Stop("git push failed")
    if remote_head() != sha:
        raise Stop(f"remote head is not the pushed {sha}")
    out(f"pushed and verified: {sha}")
    if covered is not None:
        out(f"review fix inside the files already in the MR (decision-protocol 1d): {'yes' if covered else 'NO'}")

    mr = job.get("mr")
    if mr:
        cmd = ["glab", "mr", "create", "-R", mr["repo"], "--source-branch", branch, "--target-branch", base,
               "--title", mr["title"], "--description", Path(mr["description_file"]).read_text()]
        if mr.get("squash"):
            cmd.append("--squash-before-merge")
        if mr.get("remove_source"):
            cmd.append("--remove-source-branch")
        rc, text = runner([*cmd, "--yes"])
        out(text)
        if rc != 0:
            raise Stop("glab mr create failed")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("job", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="run every check, print the plan, change nothing")
    args = parser.parse_args(argv)
    try:
        execute(load_job(args.job), dry_run=args.dry_run)
    except BadJob as error:
        print(f"BAD JOB: {error}", file=sys.stderr)
        return 2
    except Stop as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
