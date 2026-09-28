# Shared knowledge base — the wiki

**Authoritative protocol for the team's cross-project Obsidian vault.** Every delivery-team agent and `seo-specialist` carries a pointer here; this file carries the rules. Read it at the start of any substantive task before touching the vault.

The team keeps one persistent, cross-project knowledge base — an Obsidian vault that Claude Code owns — that serves as your long-lived memory across every engagement. Always use it.
- **Remote:** `https://gitlab.com/<your-org>/wiki/<you>`
- **Local copy:** `~/Documents/Projects/obsidian/<you>/`

**Read it before you work.** At the start of any substantive task, re-read the vault's own `AGENTS.md` (it defines the schema and workflow), then `wiki/index.md` (the master catalog) and `wiki/overview.md`, and open the entity / concept / source / query pages relevant to your task. Reuse what is already known instead of re-researching or re-deciding from scratch, and cite what you use as `[[Page Title]]` or the `raw/` source.

**Contribute durable knowledge back.** When your work yields reusable, long-lived knowledge — research findings, facts about a person/org/product, a framework or technique, or a hard-won decision or answer — file it into `wiki/` following the vault's schema (correct page type and sections, frontmatter, `[[wikilinks]]`, update `wiki/index.md`, append to `wiki/log.md`). Obey the vault's behavioral rules exactly: **never modify `raw/`**, read before write, prefer updating an existing page over creating a duplicate, refresh the `updated` field, log every operation, and surface contradictions explicitly instead of overwriting. Ask the human before any bulk rewrite. It is a git repo — commit and push wiki changes per its workflow and the user's git norms.

**Scope boundary.** The wiki holds *cross-project, long-lived knowledge and insight*. Project execution artifacts stay where they belong — specs under `specs/NNN-*/`, ADRs, and the target project's own `AGENTS.md` (or equivalent); team postmortems in this config repo's `collaboration-traces/`. The wiki complements those; it does not replace them.
