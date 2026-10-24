# Harness maintenance detail

Moved out of `AGENTS.md` (→ RP-18). How agents are ported, how lanes and closure records work, and how agent definitions are edited.

## Agents — where they live (added 2026-09-05)

Skills need no adaptation: OpenCode reads `.claude/skills/` and `.agents/skills/` natively, so all repository skills are already visible to it. Agents do need it. OpenCode rejects Claude Code's agent frontmatter — `tools` must be an object rather than a comma-separated string, `color` must come from a fixed palette (`primary`/`secondary`/`accent`/`success`/`warning`/`error`/`info`), and `model`, `effort`, and `skills` mean nothing to it. A symlink therefore fails config validation.

`agents/*.md` (symlinked as `.claude/agents/*.md`) stays the single source of truth. `.opencode/agent/*.md` is **generated** from it by `.opencode/sync-agents.py`, which drops `name`/`tools`/`model`/`effort`, maps `color`, sets `mode` (`all` for `team-lead-coordinator`, `subagent` for the rest), and prepends two blocks: a vocabulary map (Agent/Task tool → `task`, `subagent_type` → agent name, Agent Teams → the documented one-shot fallback) and, replacing the unsupported `skills:` preloading, an instruction to load those skills with the `skill` tool.

**Editing an agent means editing `.claude/agents/`, then re-running both `.opencode/sync-agents.py` and `.codex/sync-agents.py`.** The generated files carry a header saying so. Never edit `.opencode/agent/` or `.codex/agents/` directly — the next sync overwrites it.

`.codex/agents/*.toml` is generated deterministically by `.codex/sync-agents.py`. Codex automatically discovers these project-scoped files; do not add absolute `config_file` entries to `~/.codex/config.toml`, and do not require a multi-agent feature flag unless the user has explicitly disabled agents. The generator owns each profile's required `name`, concise `description`, `developer_instructions`, model, reasoning effort, and least-privilege sandbox setting; it also supplies the coordinator's Codex operating-mode adaptation. Run `.codex/sync-agents.py --check` to validate freshly rendered TOML, compare it with generated output, and detect schema, coverage, or drift failures.

## Partial supersession

(added 2026-08-23, project-a feature 028, DEC-1): a second post-merge-modification mode alongside full supersession, for when only some of a shipped spec's FR/AC IDs need to change. Full six-invariant definition lives in `team-lead-coordinator.md`; the load-bearing one is that a reused ID must replace that exact ID, and every genuinely new requirement/criterion takes an ID the superseded spec doesn't use — otherwise traceability quietly depends on whether test headers happen to carry a spec tag. `product-owner.md`, `lead-system-architect.md`, `senior-software-engineer.md`, and `devops-infra-expert.md` each carry a shorter pointer to the same rule.

## Size lanes — the spec is weighted to the risk (added 2026-08-27)

`/specify` and `/plan` are tiered by risk, the way review already was. The lane is set by **what the change touches, never by how it is framed** — the same objective test as the design gate (→ `.claude/process/rule-provenance.md` RP-18).

| Lane | Trigger | Artifacts |
|---|---|---|
| **XS** | nothing user-visible: doc-only, comment-only, or a bugfix with no behavior change | a row in `tasks.md` |
| **S** | presentation, copy, styling, a tuned value, a contained bugfix — and no contract, persisted data, infra/deploy topology, auth, money, legal/GDPR surface, or second deployed artifact | `spec.md` ≤120 lines, five-section S template, **`tasks.md` (always)**, **no `plan.md`**, **no architect spawn**, **one MR**; UX runs only for a navigation or user-flow change (→ RP-46) |
| **M** | new behavior inside existing contracts, one deployed artifact | `spec.md` ≤250 + `plan.md` ≤250 |
| **L** | any S exclusion | full pipeline, no budget |

- A lane above S must name an exclusion from the table; bookkeeping volume is not one. Tier down from a set lane only with the stakeholder's explicit approval; a lighter-lane recommendation at dispatch is not a tier-down (→ RP-26). When the coordinator recommends the lighter lane and the stakeholder has not answered at dispatch time, the lighter lane stands (→ RP-47).
- Budgets are `/verify` gates. Over budget has two resolutions — cut it, or re-classify up a lane on the record. Never waive the number, and meet it by **moving** material to `specs/NNN-<slug>/evidence/`, not by deleting it.
- **Lane S is one branch and one MR:** the PO authors `spec.md` and pushes without opening an MR; the engineer adds code and tests on the same branch and opens the single MR; a second engineer instance reviews spec and code together and attests; the author merges SHA-pinned. Architect and PO consultations are comments on that MR.
- **Artifact type is never a reason to split an MR.** M defaults to two (governing docs, then implementation, per SDD non-negotiable 1); L splits by risk tier, never by filename.
- On a shared branch the reviewer must differ from *every* instance that committed. `/verify` counts a feature's MRs against its lane and records any excess.
- Rework is classified on its own diff, never inherited.

Definitions: `.claude/skills/sdd-workflow/SKILL.md`; S template in `product-owner.md` §2a; gates in `team-lead-coordinator.md` Core Operating Rule 11.

## Batched closure records (added 2026-08-28)

`/verify` closure records land as entries in **`specs/verify-log.md`**, one append-only log at the root of the target project's `specs/`. Entries are pushed to the batch branch `docs/verify-log-<YYYY-MM>` as each `/verify` passes; **one** Tier-0 MR merges the batch at five entries or session end, carrying any `/archive` moves and `status:` flips due in the same window. Replaces the per-feature closure MR (→ RP-18).

- A feature is done when `/verify` passes, not when its entry merges — batching never gates delivery.
- `/verify` on the next feature blocks until the previous batch is pushed.
- Merged spec artifacts are never edited afterwards: `tasks.md` is written once on the feature branch and reviewed with the feature.

Rule: `team-lead-coordinator.md` Core Operating Rule 12. Format and worked example: `.claude/process/verify-log.md`.

## Editing agent definitions

- Frontmatter `name` must match the filename stem. Renaming an agent means renaming the file and updating references in `team-lead-coordinator.md` (which maps roles → `subagent_type`).
- `tools:` empty means inherit all from the spawner; otherwise it's an explicit allowlist. The five authoring agents have `Bash`, `Read`, `Write`, `Edit` so they can produce their SDD artifacts (spec.md, plan.md, etc.) and push them via `glab` CLI or a configured GitLab MCP. The boundary against architect/PO writing source code is intent-based — enforced by their system prompts and the coordinator's `/verify` gate, NOT by their tool list. Effective git/GitLab read/write scope is governed by the configured auth (MCP scope or `glab` token), not by anything in the agent definitions.
- **Shared blocks live once, as preloaded skills.** An agent definition's body is used verbatim as its system prompt and cannot `@import`, but the `skills:` frontmatter field injects a skill's full content into the agent's context at spawn — verified 2026-09-02 on 2.1.258, including that a *rule* placed in a preloaded skill is actually obeyed. The shared blocks are therefore skills, not copies: `.claude/skills/sdd-workflow/` (the SDD block, which contains the size lanes and the spec-change-management pointer as subsections), `.claude/skills/team-wiki/`, `.claude/skills/teammate-protocol/`, and `.claude/skills/gitlab-access/`. Edit the skill; there is nothing to keep in lockstep and no drift checker to run.
  - No copy remains inline: `team-lead-coordinator.md` preloads `sdd-workflow` like the specialists; its own `/verify` checklist lives in `.claude/process/verify-gates.md` (→ RP-50).
  - `lead-system-architect.md` keeps one role-specific paragraph inline ("Lane S — your design input has no `plan.md`"); the rest comes from the skill.
  - **Preloading does not apply when an agent runs as the main session** (`claude --agent <name>`), only when it is spawned as a subagent. The GitLab trigger therefore tells that session to read `${CLAUDE_PLUGIN_ROOT}/.claude/skills/gitlab-access/SKILL.md` directly; its procedure remains only in the skill.
- Each agent file also embeds a short **"Durable learnings live as artifacts, not memory"** section pointing learnings at `collaboration-traces/`, the target project's `AGENTS.md`, ADRs, or this agent's definition. The role-specific bullets differ; the spirit is identical. Keep them aligned if you edit one.
- **Seven agents preload the `team-wiki` and `gitlab-access` skills, and all eight preload `decision-protocol`.** The wiki protocol lives in `.claude/process/wiki.md`; its pointer lives in `.claude/skills/team-wiki/SKILL.md`.
- **Never create project-specific artifacts here.** No `specs/`, no source code, no Dockerfiles, no application configs. If a request seems to imply adding such artifacts, push back: those belong in the target project.

## Skills — where they live

Every skill is reachable from **both** `.agents/skills/` and `.claude/skills/`, so non-Claude agent tools (Amp, Codex, Gemini CLI, OpenCode, Copilot) see the same set Claude Code does. One path holds the real directory, the other a symlink. Which one is real depends on who authored the skill.

- **Every skill is real in `.claude/skills/`, symlinked into `.agents/skills/`** — this is also what the Claude Code plugin manifest (`.claude-plugin/plugin.json`) declares as the `skills` path, so a plugin install (which does not follow symlinks) still picks up every skill's actual content. Shared agent skills are injected by agent `skills:` frontmatter, and that preloading was verified with real directories; nothing has verified it through a symlink.

**Adding a skill means creating both entries.** Claude Code does not scan `.agents/skills/`, and the other tools do not scan `.claude/skills/`, so a skill with one entry is invisible to half the tools. `image-gen` was unreachable from the Skill tool from the day it was added until 2026-09-04.

Installed developer skills:
- **`context7-cli`** — Manage library documentation and Context7 integrations.
- **`frontend-design`** — Aesthetic and layout guidance for front-end assets. Mandatory for `senior-software-engineer` UI work (see that agent's "Frontend and UI Work" section).
- **`hallmark`** — Anti-slop design skill: component-level design-token discipline, interactive-state coverage, slop-test gates. Mandatory for `senior-software-engineer` UI work alongside `frontend-design`.
- **`web-design-guidelines`** — Vercel's Web Interface Guidelines review checklist (fetches current rules from GitHub at review time). Used by `code-reviewer` as the design dimension of UI-touching MR reviews.
- **`ux-copy`** — Plain-language, 2-second-read microcopy rules (no jargon, no exposed implementation detail, one idea per sentence; legal/consent text exempt). Mandatory for `senior-software-engineer` UI work alongside `frontend-design`/`hallmark`, and used by `code-reviewer` as the copy dimension of copy-touching MR reviews.
- **`ste100`** — ASD-STE100 Simplified Technical English writing rules for English documentation prose (`README*`, runbooks, ADRs, `spec.md`, `plan.md`, `docs/`): sentence-length limits, one instruction per sentence, imperative procedures, active voice. Followed by every authoring agent for the docs it writes, and used by `code-reviewer` as the docs dimension of docs-touching MR reviews.
- **`technical-seo`** — crawlability, indexing and AI retrieval: HTTP semantics, robots/sitemaps, canonicals, metadata, structured data, rendering parity, CDN/WAF access, provider-specific search/training controls and field-versus-lab verification, with dated official references. Mandatory for `senior-software-engineer` crawler-surface work (see that agent's "Crawler-Surface Work" section), and used by `code-reviewer` as the search-visibility dimension of crawler-surface-touching MR reviews.
- **`k8s-debug`** — Kubernetes diagnostic instructions.
- **`image-gen`** — General-purpose raster image generation via a direct Gemini image-model API call (no browser, no screenshot-cropping). Bundles `scripts/generate-ai.mjs`; requires `GEMINI_API_KEY` in the user's shell environment, never in a project repo.
