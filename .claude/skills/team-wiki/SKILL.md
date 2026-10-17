---
name: team-wiki
description: "The team's shared cross-project Obsidian knowledge base: where it lives, when to consult it, and how to contribute back. Preloaded into every team agent."
---

## Shared knowledge base — the wiki (always consult; contribute back)

The team keeps one persistent, cross-project Obsidian vault as long-lived memory across every engagement — remote `https://gitlab.com/<your-org>/wiki/<you>`, local `~/Documents/Projects/obsidian/<you>/`. Always use it: reuse what it already knows instead of re-researching or re-deciding, cite what you use as `[[Page Title]]`, and file durable cross-project knowledge back into it.

**The read is gated by size.** XS and lane-S delivery work, a review, a `/verify`, and a UX or feed run do not read the vault at all; lane M/L work, research, and venture work read `wiki/index.md` and the pages it names for the task's domain, never the vault's full `AGENTS.md` (→ RP-46). Contribute back only when the task produced cross-project knowledge that no existing page holds.

**At the start of a task that reads the vault, read `${CLAUDE_PLUGIN_ROOT}/.claude/process/wiki.md`** — it carries the read-first and contribute-back protocol, the vault's own behavioral rules (`raw/` is immutable, read before write, prefer updating over duplicating, log every operation, surface contradictions rather than overwriting), and the scope boundary that keeps project execution artifacts out of the wiki.
