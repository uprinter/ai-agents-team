# Agent Team teammate protocol

**Authoritative protocol for teammates spawned with a `team_name`** (part of a pre-assembled Claude Code Agent Team rather than a one-shot sub-agent). Each specialist's definition carries the five rules in condensed form; this file carries them in full, with the reasoning. Read it when a team run starts, or whenever a rule's boundary is unclear.

When you are spawned with a `team_name` parameter (i.e., as part of a pre-assembled Claude Code Agent Team rather than a one-shot sub-agent), additional protocols apply on top of your role:

1. **Check the shared TaskList first.** Before doing anything else, call `TaskList` to see what already exists, what is assigned to you, and what is blocked. Never create a new task without first verifying no equivalent task exists — duplicate tasks fragment ownership and waste the coordinator's triage time.

2. **Log every substantive peer consultation.** When you exchange `SendMessage` with another teammate about a real decision, clarification, or unblock, write a brief summary to the run's trace directory at `${CLAUDE_PLUGIN_ROOT}/.claude/collaboration-traces/<run-dir>/<your-role>-consultation-<topic>.md`. Include: who asked what, the response, and how it was resolved. Then send a one-line acknowledgement to the coordinator so they have audit visibility. Trivial pings (acknowledgements, "received," etc.) do not need to be logged.

3. **Route structural blockers through the coordinator first.** If you cannot find an artifact, an answer, or a teammate's deliverable, message `coordinator` first. Only contact another specialist directly when you already know the answer is theirs (e.g., a specific contract question for the architect, a behavior question for the PO). When you do go peer-to-peer, copy the coordinator on the substance with a one-line summary.

4. **Idle-between-turns is normal.** After you finish a turn you will be idled until another `SendMessage` arrives. Do not poll. Do not assume idleness means the team is done. Wake up on the next message.
