# Project stage

A target project states its stage in one line of its instructions file (`AGENTS.md` or `CLAUDE.md`):

```text
Project stage: pre-users
```

`pre-users` means the product has no measured outside use yet. Any other value, or no line, means `live`: the full flow applies (→ RP-101).

## What changes at `pre-users`

Only XS and lane-S changes run light. The coordinator still sets the lane by Rule 11 at intake; lane M, lane L and a change that touches any lane-S exclusion keep the full flow at every stage. The target project's own rules (for example a deploy-impact rule) stay.

An XS or lane-S change at `pre-users`:

- The engineer works in a worktree on a branch and opens one MR. The MR description holds the stakeholder's request in their words, at most five acceptance criteria and the line `lane=<XS|S> stage=pre-users`. The project must allow a merge with zero approvals.
- Green CI on the MR is the test evidence (Rule 20). CI assertions stay, shipped-artifact hygiene included.
- A change a user can see: the engineer posts the screenshots of the self-review loop (~375 px and desktop) on the MR, plus the motion evidence of `gates.md` for an element that moves, and the stakeholder looks before merge. Copy follows `ux-copy`, and the stakeholder's look checks it.
- A stakeholder rejection is a row of `harness-quality-loop.md` §3, as at `live`.
- The visual sandbox (`visual-sandbox.md`) stays: a new element with no sample starts there, and the MR links its states page.
- The engineer merges, SHA-pinned, after green CI and, for a visible change, the stakeholder's ok.

Not done at `pre-users`: `spec.md`, `tasks.md`, the product owner, `code-reviewer` and its attestation, the render sheet, `taste-critic`, `user-eyes-tester`, the verify-log entry and its `gates:` line. These are Rules 3, 6, 7, 10, 12 and 17 and the lane-S task rows of Rule 11 in `team-lead-coordinator.md`, the review lifecycle and tiers of `verify-gates.md` (item 6, non-negotiable 4), and the design, copy and simulated-user gates of `gates.md`, their lane-S parts included. The engineer's review duties in `senior-software-engineer.md` and the independent review of the `AGENTS.md` delegation paragraph yield to this file for such a change.

## Switch to `live`

The switch conditions are the stakeholder's and stand beside the project's goal measure, wherever the team records it. The regular backlog review compares the measure with them and, when one is met, asks the stakeholder once. The stakeholder's yes changes the line through a documentation MR. The stakeholder can switch at any time; a project never returns to `pre-users`.
