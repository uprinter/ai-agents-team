---
name: harness-cleaner
description: "Audit and shrink the agent definitions, AGENTS.md and process rules in this repo: size against budget, duplicated rules, contradictions. Use when a size-budget check fails, after adding rules, on a weekly or monthly cleanup, or when the user says cleanup, audit, bloat or contradiction."
---

## Harness cleaner

Agent definitions and `AGENTS.md` load in full on every spawn, so each byte costs on every run. This skill finds what to merge or remove. It proposes; the founder approves each change.

### Run

1. Run `python3 .claude/scripts/check_harness.py`. Budget breaches print as `exceeds budget`. List the five largest files and their growth since the last budget commit: `git log -p --follow -3 -- .claude/scripts/size-budget.json`.
2. **Duplicates.** For each file in step 1, list rules restated elsewhere. Search `(→ RP-nn)` citations that appear in `AGENTS.md` and in an agent file, and rules in an agent file that `.claude/process/*.md` or a preloaded skill already state. Keep one source of truth; replace the other with a pointer.
3. **Contradictions.** Group the rules by situation (dispatch, review, merge, status, wiki, copy, GitLab). Spawn one fresh `general-purpose` agent per group with the rule texts only. Ask: "List pairs of instructions that cannot both be followed. Quote both." Check each reported pair against the files before you act on it.
4. **Proposals.** Write one line per change: file, rule, action (merge, remove, point), bytes saved. Present them to the founder in the `decision-protocol` format. Apply only approved changes.
5. **Close.** After approved edits, regenerate ports (`.opencode/sync-agents.py`, `.codex/sync-agents.py`), run `check_harness.py --ratchet-budget`, then `check_harness.py` and the unit tests. Commit the lowered budget with the edits.

Done when every file is at or under its budget, every contradiction pair has a disposition (fixed, or kept with a reason), and the commit carries the lowered `size-budget.json`.

### Raising a budget

A rule that must grow its file raises that file's entry in `.claude/scripts/size-budget.json` by hand. The commit message names the reason and what was considered for removal. `--ratchet-budget` never raises.

### Not yet covered

Rules that never fire need agent run tails and a weekly digest. Those do not exist; do not guess dead rules from file contents.
