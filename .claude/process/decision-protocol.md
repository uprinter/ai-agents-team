# Decision protocol — decide small things, ask big things briefly

**Authoritative protocol for every decision an agent puts to the stakeholder.** Every agent and the root session carry a pointer here through the `decision-protocol` skill; this file carries the rules. It exists because the team asked the stakeholder to settle small, reversible matters in long technical messages (→ RP-45).

## 1. Classify the decision first

A decision is **ask** only when it has a long-term, visible consequence. The ask list is the list the team already uses for lane and review tiers, plus the irreversible and the outward-facing:

| Ask (Tier B) | Decide yourself (Tier A) |
|---|---|
| a contract, API, or data shape another artifact consumes | wording, naming, formatting, comments, documentation text |
| persisted data or a schema | styling, layout, a tuned value with no persisted effect |
| infra or deploy topology, project settings | test data, fixture shape, test naming |
| auth, secrets, money, legal or GDPR surface | which of two equivalent tools, commands, or orderings to use |
| anything deleted, force-pushed, or otherwise irreversible | what evidence to cite and how to record a deviation |
| content that goes live under the stakeholder's name or brand | accepting a check deviation that changed no shipped artifact and no persisted state |
| scope: adding, dropping, or tiering down a requested feature | one more retry, one more probe, one more read of a log |
| a choice the stakeholder explicitly reserved | any choice that one MR can reverse without a trace outside the repo |

Rules of the split:

- **Reversibility decides ties.** If one MR reverses it and nothing outside the repository remembers it, it is Tier A.
- **Tier A is recorded, never asked.** Write the choice and its one-line reason in the artifact that already exists for it: a `tasks.md` row, an MR note, a `verify-log` evidence bullet, a `DEC-n` line in `spec.md`. The stakeholder reads it there if they want to.
- **A Tier A decision never becomes Tier B because it is in a log the stakeholder owns.** The stakeholder's name on the log is the normal state of every artifact; it is not a reservation.
- **Uncertainty about the tier is not a Tier B question.** Apply the reversibility rule and move on.

## 1a. Found work

The same split applies to what you notice while working (→ RP-52):

- **Trivial and inside the change's own files** (a typo, a stale comment, a mismatched name, a formatting slip): fix it in the same MR, record it in one `tasks.md` row, do not mention it in the closing message.
- **Trivial and outside the change's files:** leave it; do not report it.
- **A real problem** (a defect, a wrong rule, a failing gate, a security or data issue): one line in the closing message, in the form `Separate task proposed: <what is wrong, in plain words>`. At most three such lines per closing message; if there are more, the three most important stay and the rest go to the run's postmortem.
- Never offer to fix it now, never dispatch it, never widen the current MR with it (Core Operating Rule 16).

## 1b. A blocked action

A permission block on a push, merge or edit is not a decision (→ RP-54). Report once: what was blocked, the exact command for the stakeholder to run, and what happens after; offer no options and do not ask again.

## 1c. Merging an MR

After a passing `REVIEW-ATTESTATION` the coordinator starts the second-instance review without asking who reviews. When the reviewer approves and CI is green, the author merges SHA-pinned and the close message reports the merge. The stakeholder is not asked to approve or merge; a refusal by the permission classifier is a blocker under §1b (→ RP-72).

## 2. The ask format (Tier B)

One decision per message. Eight lines maximum, in this order, nothing else:

```
Decision: <what you need settled, one line>
Why it matters: <the lasting consequence, one line>
1. <option> — <consequence, one line>   ← recommended
2. <option> — <consequence, one line>
3. <option> — <consequence, one line>   (optional)
Reply with a number. Details: <one pointer to the MR note, task, or file>
```

- **The recommended option is always first and always marked.** An ask with no recommendation goes back to the sender.
- **No technical detail in the ask.** Job IDs, SHAs, timestamps, file paths, line numbers, rule IDs, AC IDs stay in the pointer target. The one exception is an identifier the stakeholder must act on themself, such as a button to press.
- **No traps, caveats, or second questions.** If a later state change would need another decision, handle it under this protocol when it happens.
- **Several decisions at once:** ask the one that blocks first. Send the next after the answer. Independent decisions that fit the eight lines together may share a message, each with its own number set.
- **A relay never expands.** When the root session or the coordinator passes a teammate's ask to the stakeholder, it forwards the block as is or shortens it. It never adds background, never restates the options, never appends its own second question.

## 3. Gates

- **Sender self-check** before every ask: Tier B by the table? Eight lines or fewer? Recommended option first? No technical detail outside the pointer? One decision? If any answer is no, fix it or decide it yourself.
- **Coordinator** returns a teammate's ask that fails the self-check, or that puts a permission block to the stakeholder as options, to the teammate instead of relaying it, and records a Tier A decision it finds asked as a process finding in the run's postmortem.
- **`/verify`** records every Tier B ask of the feature in the closure entry as `asks=<n>`; a `/verify` entry whose evidence shows the stakeholder was asked a Tier A matter is a process finding and appends the compact feedback row of `harness-quality-loop.md`.
