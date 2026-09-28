---
name: teammate-protocol
description: The rules that apply when a specialist is spawned as part of a pre-assembled Claude Code Agent Team rather than as a one-shot sub-agent. Preloaded into the five delivery-team specialists.
---

## When operating as a teammate on an Agent Team

When you are spawned with a `team_name` — part of a pre-assembled Agent Team rather than a one-shot sub-agent — five protocols apply on top of your role:

1. **Read `TaskList` before anything else:** what exists, what is assigned to you, what is blocked. Never create a task without first verifying no equivalent one exists — duplicates fragment ownership and waste the coordinator's triage.
2. **Log every substantive peer consultation** to `${CLAUDE_PLUGIN_ROOT}/.claude/collaboration-traces/<run-dir>/<your-role>-consultation-<topic>.md` (who asked what, the response, how it resolved), then send the coordinator a one-line acknowledgement. Trivial pings need no log.
3. **Route structural blockers through the coordinator first.** Go peer-to-peer only when you already know whose answer it is, and copy the coordinator with a one-line summary of the substance.
4. **Idling between turns is normal.** Do not poll, and do not read idleness as the team being finished. Wake on the next message.

Full protocol with the reasoning behind each rule: `${CLAUDE_PLUGIN_ROOT}/.claude/process/teammate-protocol.md`.
