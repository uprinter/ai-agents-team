# Fold-in review

How the team decides whether a role stays a separate agent. Source: Anthropic, "Building agents: when to fold subagents into your main agent loop" (read 2026-10-29). A role stays separate only when a measurement shows it earns its handoff cost (→ RP-68).

## What stays separate by design

- Author, reviewer and coordinator. Separation of duties is a control, not an org chart (→ RP-02, RP-55).
- Independent parallel work with a fresh context: `tabula-rasa`, `user-eyes-tester`, `feed-scroller`.
- Everything else is a candidate. A candidate is a role whose work is mostly a procedure or a document, not a different context or a control.

## Evidence the review reads

1. **Volume and cost.** Run `python3 .claude/scripts/agent_digest.py`. A role with few runs, high steps per run and long duration costs more than it adds.
2. **Handoff loss.** Count review findings that trace to a paraphrased brief. The `request-ref` in `ASSUMPTION-CHALLENGE` is the check.
3. **Golden set.** Ten closed tasks, listed below. Each is rerun with the role present and with the role folded, three runs each. Record which tasks flipped, not only the total.

## Golden set

Pick ten closed tasks from the team's recorded run traces; keep the mix, replace a task only when it is archived.

| Lane | Tasks |
|---|---|
| S | three: a copy change, a small static page, a configuration alias |
| M | three: new behavior inside an existing contract, such as an analytics change or a cache fix |
| L | three: a task with an S exclusion, such as a migration, a design system or a new deployed artifact |
| Defect | one: a task where a review attestation missed a defect |

Each task has its recorded outcome as the expected result. A task passes when the run reaches the same outcome with every gate in `verify-gates.md` green.

## Fold-in procedure

1. Choose one candidate. Never two at once.
2. Turn its prompt into a skill, its API calls into tools, and its gate into a check in `verify-gates.md`.
3. Run the golden set with and without the role. Three runs per task, because regressions are intermittent.
4. Fold when no task flipped to worse. Keep the role when one did, and write the flipped task in the closing note.
5. Record the result in the run's trace directory, named for the date and the folded role. Update the role table in `AGENTS.md` only after the stakeholder approves the fold (→ RP-26 for any lane change).

## First candidates

- `lead-system-architect` at lane M: its work is the `plan.md`. Test: the engineer writes `plan.md` with an `architecture` skill; the architect stays for lane L.
- `product-owner` at lane M: test the same way with a `requirements` skill. Lane S already has no PO stage (→ RP-66).
- `seo-specialist`, `social-media-manager`: test as skills run inline, since `technical-seo` and `linkedin-presence` already exist.

Digest of 2026-10-22 to 2026-10-29: `lead-system-architect` 3 runs, `product-owner` 4 runs, `code-reviewer` 99 runs.

## Stale-rule probe

A rule written for an older model may block a newer one. Sort each `RP-nn` as **incident** (a control against a real failure: attestation, SHA-pinned merge, worktree) or **insurance** (it steers the model: wording, ordering, reminders). Remove insurance rules one batch at a time, rerun the golden set, and keep the removal when nothing flipped. `harness-cleaner` runs this probe.

## Tool lists

Specialists carry an explicit `tools:` allowlist taken from observed use (`agent_digest`-style transcript count), not `*`. Tool choice degrades beyond 30 to 50 definitions. Add a tool to a list when a run needs it; the review attestation names the addition.
