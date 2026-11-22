# Shared knowledge base — Notion, with the wiki read-only

**Authoritative protocol for the team's cross-project knowledge.** Every delivery-team agent and `seo-specialist` carries a pointer here; this file carries the rules.

New cross-project knowledge goes to Notion, under a topic page in `Knowledge base`. The Obsidian vault is read-only legacy: read it, never write to it, and never migrate Notion content into it (→ RP-97).
- **Notion:** the `Knowledge base` page in the stakeholder's workspace, reached through the Notion connector.
- **Wiki (read-only):** remote `https://gitlab.com/<your-org>/wiki/<you>`, local copy `~/Documents/Projects/obsidian/<you>/`.

**Read before you work — when the task is one that reads.** XS and lane-S delivery work, reviews, `/verify`, and UX or feed runs skip both: a styling fix has nothing to learn there, and ten agents reading per feature was measurable cost (→ RP-46). For lane M/L work, research, and venture work, search `Knowledge base` for the task's domain if you have Notion tools, and read `wiki/index.md` in the vault and the pages it names; without Notion tools, use the vault and what the brief carries, and never report the missing tools as a blocker. Reuse what is already known instead of re-researching or re-deciding, and cite the Notion page or the `[[Page Title]]` you used.

**Contribute durable knowledge back.** When your work yields reusable, long-lived knowledge — research findings, facts about a person, organization or product, a technique, or a hard-won answer — and no existing page holds it:
- With Notion tools, file it yourself under the right `Knowledge base` topic page; prefer updating an existing page over creating a duplicate.
- Without Notion tools, end your report with a `## For Notion` section: the target topic, a page title, and the body. The caller files it and its closing message names the page.

Surface a contradiction with an existing page explicitly instead of overwriting it. Ask the human before any bulk rewrite.

**Scope boundary.** `Knowledge base` holds *cross-project, long-lived knowledge*. Project execution artifacts stay where they belong — specs under `specs/NNN-*/`, ADRs, and the target project's own `AGENTS.md`; team postmortems in this config repo's `collaboration-traces/`.
