---
name: decision-protocol
description: "How to decide and how to ask: decide small reversible matters yourself and record them; ask the stakeholder only for decisions with lasting visible consequences, in at most eight lines, recommended option first. Preloaded into every team agent."
---

## Decisions — decide the small, ask the big briefly

**Decide yourself and record it** when one MR can reverse the choice and nothing outside the repository remembers it: wording, naming, formatting, styling, test data, which of two equivalent tools, how to record a deviation, accepting a check deviation that changed no shipped artifact and no persisted state. Write the choice and its reason in the artifact that already exists for it (`tasks.md` row, MR note, `verify-log` bullet, `DEC-n` line). Never put it to the stakeholder.

**Ask the stakeholder** only for a lasting, visible consequence: a contract or data shape another artifact consumes, persisted data, infra topology or project settings, auth, secrets, money, legal surface, anything irreversible, content going live under the stakeholder's name, scope changes, or a choice the stakeholder explicitly reserved.

**The ask is at most eight lines**: `Decision:` one line, `Why it matters:` one line, up to three numbered options with one-line consequences, the recommended option first and marked, then `Reply with a number. Details: <one pointer>`. No job IDs, SHAs, timestamps, paths, rule or AC IDs in the ask; they live at the pointer. One decision per message; ask the blocking one first. A relay forwards the block as is or shorter, never longer.

**Before you send any ask, read `${CLAUDE_PLUGIN_ROOT}/.claude/process/decision-protocol.md`** — it carries the full tier table, the format, and the gates (sender self-check, coordinator return, `/verify` `asks=` count) (→ RP-45).
