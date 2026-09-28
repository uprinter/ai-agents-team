---
name: gitlab-access
description: Use GitLab safely through a configured MCP, authenticated glab, and exact-SHA Git transport. Load before any GitLab API operation, authenticated GitLab Git operation, or claim that GitLab access is blocked.
---

# GitLab Access

Follow the current user request, role boundary, and approval policy. Loading this skill does not authorize an external mutation.

## Select the direct tool

- Use a configured GitLab MCP connector when available, or authenticated `glab`, for GitLab API work.
- Use Git directly for repository transport. Do not recreate a local commit through GitLab's commit API.
- If neither direct path works, report the blocker and request configuration or approval for the exact alternative. Do not switch to a browser, workflow platform, or another service's credential without explicit approval.

## Protect authentication

An authentication check can fail when the current runtime cannot read the operating-system keyring. Use that runtime's documented permission mechanism to repeat the diagnostic before concluding that the user is signed out.

Never print, copy, or place an access token in a command, URL, log, or file.

When running in Codex, read [references/codex.md](references/codex.md) before diagnosing authentication or using authenticated Git transport. Other runtimes do not load that reference.

## Use authenticated HTTPS Git transport

Keep the `glab` credential helper local to each Git command. Never change repository, global, or system Git credential configuration.

For a push:

1. Derive the default target from the current local branch, validate it, derive the full remote ref, and record the intended commit. Stop if the repository is detached or the branch is empty, and keep the commit unchanged during the push and verification.

   ```sh
   gitlab_remote_branch="$(git branch --show-current)"
   test -n "$gitlab_remote_branch"
   git check-ref-format --branch "$gitlab_remote_branch"
   gitlab_remote_ref="refs/heads/$gitlab_remote_branch"
   git check-ref-format "$gitlab_remote_ref"
   gitlab_local_sha="$(git rev-parse HEAD)"
   ```

   For an explicitly different target, receive the branch name as data instead of inserting it into shell source. For example, use `IFS= read -r gitlab_remote_branch`, then run the same non-empty and `git check-ref-format` validations before deriving `gitlab_remote_ref`.

2. Push that exact commit with the refspec quoted as one argument:

   ```sh
   git -c credential.helper= \
     -c credential.helper='!glab auth git-credential' \
     push origin "$gitlab_local_sha:$gitlab_remote_ref"
   ```

3. Read the validated remote ref with the same command-scoped helper:

   ```sh
   git -c credential.helper= \
     -c credential.helper='!glab auth git-credential' \
     ls-remote --heads origin "$gitlab_remote_ref"
   ```

4. Report success only when the returned remote branch SHA exactly equals `$gitlab_local_sha`.

Apply the same command-scoped helper to other authenticated GitLab HTTPS transport commands. Use the current runtime's documented permission mechanism when keyring or network access requires it.

## Force-push after a rebase

After rebasing a branch already pushed to `origin` (e.g. onto a moved `main`), a plain push is rejected as non-fast-forward. Use `--force-with-lease` scoped to the exact prior remote SHA, so the push aborts instead of clobbering someone else's commit if the remote moved since you last fetched it:

```sh
gitlab_remote_branch="$(git branch --show-current)"
gitlab_prior_sha="<the remote SHA you rebased from, e.g. from your last fetch/push>"
git -c credential.helper= \
  -c credential.helper='!glab auth git-credential' \
  push --force-with-lease="${gitlab_remote_branch}:${gitlab_prior_sha}" origin "$gitlab_remote_branch"
```

**zsh gotcha — always brace the variable before the colon.** In zsh, `$var:x` is parsed as a parameter-expansion modifier (`:a`, `:h`, `:t`, `:r`, `:e`, `:l`, `:u`, `:s`, `:q`, `:P`, …), not a literal colon, whenever a modifier letter immediately follows the colon. `--force-with-lease="$gitlab_remote_branch:$gitlab_prior_sha"` silently mangles the branch name into garbage (e.g. `:a` runs an absolute-path transform) whenever the SHA happens to start with one of those letters, and the lease then matches nothing — git falls back to a plain non-fast-forward rejection that looks exactly like a stale-branch problem, not a quoting bug. Braces (`${gitlab_remote_branch}:...`, used above) make `zsh` treat the whole thing as one token and avoid this. Bash is unaffected either way, but always brace it since a script may run under either shell.

Verify with `git push --dry-run` first if you want to confirm the lease will apply without risking the actual push.
