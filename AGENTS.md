# Repository guidance

This file provides shared guidance to Claude Code, Codex, and OpenCode when working in this repository.

## What this repo is

This is **not an application** — it is a reusable agent-team configuration for Claude Code, Codex, and OpenCode. There is no application build or runtime. `agents/` (symlinked as `.claude/agents/` for the standard Claude Code project convention) is the source of truth; `.codex/agents/` and `.opencode/agent/` are generated ports, and repository skills are shared across runtimes through `.agents/skills/` and `.claude/skills/` (the latter holds every skill's real directory; see *Skills — where they live*).

- `.claude/agents/*.md` — agent definitions, each with YAML frontmatter (`name`, `description`, `tools`, `model`, `color`) followed by the agent's system prompt. Six form the SDD **delivery team** (see *The team*); `seo-specialist.md` is a standalone organic-search auditor (see *The standalone agent*).
- `.claude/collaboration-traces/<date>-<topic>/` — postmortems and traces from team test runs. This is where durable findings about team behavior live.
- `.claude/process/` — shared team process that agent definitions **point to** rather than embed (see *Shared process files* below):
  - `rule-provenance.md` — the incident narratives behind the team's non-obvious rules, as numbered `RP-nn` entries, cited from the rules as `(→ RP-nn)`. Append-only.
  - `harness-quality-loop.md` — the AC validation map, bounded M/L assumption challenge, and compact failed-gate feedback record.
  - `spec-change-management.md` — authoritative `/amend`, `/cancel`, supersession, partial-supersession, and `Historic` flows.
  - `seo-lifecycle.md` — the standalone SEO agent's stages, evidence gates, artifact contract, and follow-up cadence.
  - `wiki.md` — the read-first / contribute-back protocol for the shared Obsidian vault.
  - `teammate-protocol.md` — the Agent Team teammate rules in full.
  - `verify-log.md` — header grammar and a worked example for a target project's `specs/verify-log.md` entry.
- `.claude/settings.local.json` — permission allowlist (not committed-as-team-config; local overrides).

**No agent-memory.** This team does not maintain per-agent memory files. Durable learnings live as artifacts instead: postmortems under `collaboration-traces/`, per-target-project conventions in that project's `AGENTS.md`, architectural decisions as ADRs in the target project, and team-wide rules in the agent definitions themselves. If you find yourself wanting to write a memory file, edit one of those instead.

**Use direct programmatic tools by default.** Use the target system's purpose-built API, MCP connector, or authenticated CLI; never route through a browser, GUI, workflow platform, another service's credential, or another indirect tool unless the scenario explicitly requires it or the user approves that exact alternative first. If the normal path is unavailable, report the blocker and request configuration or approval instead of improvising another access path (→ RP-31, RP-33).

**GitLab access.** Before any GitLab API or authenticated Git transport operation, every agent must follow `gitlab-access`; Claude source agents keep an exact-path read fallback for main-session use, while generated Codex and OpenCode prompts enforce runtime-native loading. The skill owns authentication diagnosis, exact-SHA transport verification, and secret handling, with runtime-specific details disclosed only when needed (→ RP-31, RP-33).

**Assign every GitLab issue.** Use `@your-agent-bot` by default; assign `@your-human-operator` only while the current next action requires a direct human operation, then return the issue to `@your-agent-bot` when that action is complete (→ RP-32).

**This repo outranks a target project's `AGENTS.md`.** A target's `AGENTS.md` is authoritative for that project's own conventions — its stack, its layout, its local commands — and nothing here displaces those. But where it contradicts this repo on team process — a role boundary, a gate, an SDD stage, a size lane — this repo wins, and the contradiction is a defect to fix in the target project, never a local exemption to follow. An agent that finds one says so instead of silently picking a side; the check belongs in the review attestation of any diff touching a target's `AGENTS.md`.

**Shared knowledge base (the wiki).** Separately from those per-project artifacts, all seven agents use one persistent, cross-project Obsidian knowledge base — `https://gitlab.com/<your-org>/wiki/<you>` (local: `~/Documents/Projects/obsidian/<you>/`) — as long-lived team memory: each agent consults it before working and contributes durable knowledge back, following that vault's own instruction-file schema (`entities/`, `concepts/`, `sources/`, `queries/` + `index.md` + `log.md`; `raw/` is immutable). That vault is *external, human-curated knowledge* — not per-agent memory files — so the no-memory rule above still holds. The directive lives in each agent as the identical *"Shared knowledge base — the wiki"* block.

## The team

A coordinator delegates work across five specialists. Treat this hierarchy as load-bearing — do not collapse roles or have one agent do another's job.

| Role | File | Model | Authority |
|---|---|---|---|
| `team-lead-coordinator` | `team-lead-coordinator.md` | sonnet | Coordinates only. Never implements. |
| `lead-system-architect` | `lead-system-architect.md` | opus | Decides; read-only on infra. Produces ADRs/tickets. |
| `senior-software-engineer` | `senior-software-engineer.md` | sonnet | Implements application code. Authors and merges MRs; never reviews. Must consult architect + product owner. |
| `code-reviewer` | `code-reviewer.md` | sonnet | Second-party review of M/L application governing-document MRs and application-code MRs. Never authors, never merges. |
| `product-owner` | `product-owner.md` | opus | Defines requirements. Never writes code or picks tech. |
| `devops-infra-expert` | `devops-infra-expert.md` | opus | Owns IaC and Kubernetes manifests (investigates, authors, commits). Read-only by default; state-changing ops (including `git commit`/`git push`) require explicit per-command approval. |

**Mandatory consultation rule**: the engineer always consults the architect (for system/non-functional requirements) and the product owner (for business requirements/acceptance criteria) before implementation. Encode this as task dependencies in the shared task list, not as advice.

**Domain split — application code vs. IaC/manifests.** "Never implement code, IaC, or config directly... always dispatch senior-software-engineer (or the relevant specialist)" (see below) does not mean IaC/config always routes to the engineer. `devops-infra-expert` is the relevant specialist for Terraform, Helm charts, and Kubernetes manifests in `oci-k8s-platform` and `cicd` — it investigates, authors, and commits those changes itself (state-changing git steps still gated on per-action human approval), rather than handing authorship to `senior-software-engineer`. Reserve `senior-software-engineer` for application code. **Review follows the same split**: IaC/manifest MRs are reviewed by a second `devops-infra-expert` instance, never `code-reviewer` — the review-lifecycle and `REVIEW-ATTESTATION` rules are mirrored in `devops-infra-expert.md` ("Review separation of duties (IaC/manifest MRs)"). (Confirmed 2026-08-16: a `revisionHistoryLimit` fix to `cicd` k8s manifests was split across `devops-infra-expert` (investigate) and `senior-software-engineer` (author/commit + review) — an unforced misassignment on both authorship and review, since devops-infra-expert's own charter already claims IaC/manifest authorship and its read-only default only gates state-changing ops, not editing.)

**Nothing lands on a target project's `main` except through an MR** — including post-`/verify` documentation edits, which go through a Tier-0 MR (engineer instance authors, second instance attests); no agent, the coordinator included, pushes to `main` directly (`team-lead-coordinator.md` Core Operating Rule 6; confirmed 2026-08-22, feature 025 closure record pushed direct).

**Two-party review is evidenced by attestation, not by GitLab accounts.** All agent instances share one GitLab identity, so the audit trail cannot distinguish author from reviewer. The reviewer therefore posts a structured `REVIEW-ATTESTATION` note (SHA, files/lines reviewed, findings, spec refs, reviewer instance token) before approving, and `/verify` audits it against the real diff and the approval timestamps; approval without a valid attestation is a self-approval. Full format lives in `code-reviewer.md`; the `/verify` check lives in `team-lead-coordinator.md` (SDD non-negotiable 4).

**Strict delegation, always — including for whoever is driving the team.** This binds the root/orchestrating Claude Code session itself, not only `team-lead-coordinator`: never implement code, IaC, or config directly in a target project, even a small, well-specified, low-risk change you've already fully reasoned through. Always dispatch `senior-software-engineer` (or the relevant specialist) and require independent review before merge — size and confidence are not valid reasons to skip delegation. (Confirmed 2026-08-08, project-a feature 005: a small CSS-only layout fix was implemented directly by the root session instead of being dispatched; an independent review still gated the merge, but authorship had bypassed the team. Never repeat this — dispatch first, always, no carve-outs.) Direct tool use by the root session stays fine for verification, investigation, and git/process operations on an already-approved change (commits, pushes, merges) — never for writing or editing what ships.

**The request bounds the work — this binds the root/orchestrating session too, not only `team-lead-coordinator`.** A finding is not a feature: defects and improvements noticed while investigating are written down and handed back in the closing message, never dispatched, spec'd, or put to the stakeholder mid-task as an offer to fix them now. Offering found work *is* the defect — the stakeholder can ask for it in a later session, with the current job finished. When a finding genuinely belongs to the requested change, it rides that feature's existing MR at that feature's lane weight; it never becomes a second feature with its own spec, spawns, attestation, and `verify-log` entry. (Confirmed 2026-09-04: "remove the nginx app from cicd" produced eight commits on `cicd` `main`, of which one was the request, plus three more here — the other seven were found work the session offered and then built at full per-feature weight; → RP-25. Rule and gates: `team-lead-coordinator.md` Core Operating Rule 16.)

**The dispatch brief states what changes and the constraints — never roles, stages, or artifacts.** Rule 16 bounds how many features a request may create; this bounds how heavy the one requested feature may be. The root/orchestrating session says what the stakeholder asked for, what must not regress, and what evidence settles it; `team-lead-coordinator` assigns the lane from the diff surface (Core Operating Rule 11). Writing "run the full SDD lifecycle" or naming `lead-system-architect` in a brief is tiering up without the stakeholder's approval, and the coordinator classifies from the diff anyway. **Tiering up is no longer free:** a lane above S must name an exclusion from the size-lane table, and bookkeeping volume — supersession restatement, ID counts, retiring an ADR — is not one; restated superseded requirements go to `specs/NNN-<slug>/evidence/superseded-ids.md`, which is why they no longer break a lane-S budget. (Confirmed 2026-09-05: two visual defects drew the full team including the architect, off a brief this session wrote; feature 053 — revert an icon to grey — shipped lane M with a 22.0 KB `plan.md` on an invented rule that retiring an ADR needs one, and 055 — five presentation items — shipped lane L at 69.4 KB across four MRs, its own DEC-1 recording "bookkeeping weight, not design complexity"; the control, 054, was 9.1 KB in one MR; → RP-26. Gates: `team-lead-coordinator.md` Core Operating Rule 11.)

**Coordinator operates as a Claude Code Agent Team lead** (per `https://code.claude.com/docs/en/agent-teams`), which requires:
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Claude Code v2.1.32+
- Coordinator running in the main session (teammates cannot spawn their own teams)

If those preconditions aren't met, the coordinator falls back to the regular `Agent` sub-agent tool.

## The standalone agent

**`seo-specialist`** is a **Claude Code agent** (at `.claude/agents/seo-specialist.md`), **not part of the six-role delivery team** and not coordinated by `team-lead-coordinator`, for organic search and AI answer visibility, including Google, Bing/Copilot, ChatGPT, Claude and Perplexity. It follows `.claude/process/seo-lifecycle.md`: scope → baseline → audit → prioritize → handoff → verify → measure, reusing stable finding IDs and recording dated evidence, missing data and follow-up owners. Its technical checklist and current provider references live in `technical-seo`; it distinguishes search retrieval from training permissions and technical eligibility from observed citations or business outcomes. It writes target-project documentation only, handing implementation to normal delivery intake at the appropriate size lane; live visibility controls still require stakeholder approval of exact final content. Missing private analytics limits dependent checks rather than stopping the public audit, and docs land on main through the existing Tier-0 MR review.

It runs as a spawned agent and preloads the `team-wiki` skill.

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
- **`technical-seo`** — crawlability, indexing and AI retrieval: HTTP semantics, robots/sitemaps, canonicals, metadata, structured data, rendering parity, CDN/WAF access, provider-specific search/training controls and field-versus-lab verification, with dated official references. Mandatory for `senior-software-engineer` crawler-surface work (see that agent's "Crawler-Surface Work" section), and used by `code-reviewer` as the search-visibility dimension of crawler-surface-touching MR reviews.
- **`k8s-debug`** — Kubernetes diagnostic instructions.
- **`image-gen`** — General-purpose raster image generation via a direct Gemini image-model API call (no browser, no screenshot-cropping). Bundles `scripts/generate-ai.mjs`; requires `GEMINI_API_KEY` in the user's shell environment, never in a project repo.

**Design-quality gate (added 2026-08-19, after project-a feature 018 shipped an unstyled zero-CSS form):** UI-touching work — classified by the diff's effect on user-visible DOM, never by task framing — is gated end-to-end: the product owner writes visual ACs (`product-owner.md` Methodology §6), the engineer follows a UI definition-of-done with a mandatory screenshot self-review loop and screenshots attached to the MR (`senior-software-engineer.md` "Frontend and UI Work"), `code-reviewer` checks the design dimension via `web-design-guidelines` in the `REVIEW-ATTESTATION`, and the coordinator blocks `/verify` on missing screenshots or a missing design check (`team-lead-coordinator.md` Core Operating Rule 7). **Screenshots are uploaded to the MR, never committed to `specs/`** — as image files they are the one evidence class git cannot delta-compress, and the reviewer's design dimension rejects a diff that adds one (→ RP-27).

**Scope-integrity gate (added 2026-08-20, after a target-project feature shipped a "Not built yet — notify me" email-capture placeholder in place of the promised alert-delivery behavior and was reported as done):** shipping a stub, waitlist/capture form, mock, or hardcoded output as a stand-in for a spec'd functional requirement is strongly prohibited. **Half-built functionality is never customer-visible, full stop** (tightened 2026-08-21 after feature 024 restyled and re-shipped that same placeholder): phases may be scoped as separate FRs, but any phase whose behavior isn't real ships dark — unmounted or flag-off in production — and a feature that touches a pre-existing placeholder inherits the obligation to hide it (`product-owner.md` Methodology §7). The engineer must flag any such substitution rather than report it as done (`senior-software-engineer.md` "Scope Integrity"), and the coordinator blocks `/verify` unless the merged diff actually implements the linked FR's behavior end-to-end, not just its UI shell (`team-lead-coordinator.md` Core Operating Rule 8).

**Copy-brevity gate (added 2026-08-23, after project-a's email-updates signup shipped four long sentences of copy for a one-field form):** any user-facing string should read in about 2 seconds — plain words, one idea per sentence, no exposed implementation detail — same shape as the design gate. Legal/consent text is exempt. The product owner writes copy ACs (`product-owner.md` Methodology §8), the engineer follows the `ux-copy` skill for every string it writes or touches (`senior-software-engineer.md` "Frontend and UI Work"), `code-reviewer` checks the copy dimension via `ux-copy` in the `REVIEW-ATTESTATION`, and the coordinator blocks `/verify` on a missing copy check for copy-touching work (`team-lead-coordinator.md` Core Operating Rule 10). A required scope-integrity disclosure (the gate above) is never dropped for brevity — only said once, briefly.

**Search-visibility gate (added 2026-08-30, after a live check found `project-a.example.com` answering `200 text/html` for every URL — `/robots.txt` and `/sitemap.xml` included — since launch):** crawler-surface work is gated the same way, on a deliberately different trigger. A change is **crawler-surface-touching** when its diff changes what a crawler receives rather than what a user sees — head metadata, `robots.txt`/`sitemap.xml`, routing/redirects and the status code any URL returns, server-side rendering, structured data — which is **not** a subset of UI-touching, since a routing rule changes it while touching no DOM. That is why three existing gates missed it for thirty-eight features: all of them classify by the user-visible surface, and the site renders perfectly in a browser. The engineer follows `technical-seo` for such work (`senior-software-engineer.md` "Crawler-Surface Work"), `code-reviewer` checks the search-visibility dimension via that skill in the `REVIEW-ATTESTATION`, and the coordinator blocks `/verify` on a missing dimension (`team-lead-coordinator.md` Core Operating Rule 14) — evidenced by status-code and `Content-Type` output, never a screenshot (→ RP-21). Strategy, keyword research, and measurement are not in this gate: they belong to the `seo-specialist` agent, which writes no code.

**Shipped-artifact hygiene gate (added 2026-08-30, after the stakeholder found four HTML comments on the public homepage disclosing feature numbers, FR/AC/DEC/ADR IDs, `main.ts`/`plan.md §3.1` paths, and the `preview/` service's role — one of them added that same day by feature 040, through a passing two-party review):** nothing the client receives may carry internal traceability. The trigger is *any artifact a client receives*, which is broader than both UI-touching and crawler-surface: a comment renders nothing (so the design gate misses it), is read by no user (so the copy gate misses it), and sits outside the status-code/robots/canonical/structured-data checks Rule 14 enumerates — four gates, none wrong, and the defect fell between all of them (→ RP-22). Unlike every other gate here, **the carrier is deliberately not a review dimension**: review passed this three times, so the rule is a build-time assertion over built output that fails CI (`senior-software-engineer.md` "Shipped Artifacts Carry No Internal Traceability"; `team-lead-coordinator.md` Core Operating Rule 15). The reviewer's job is to confirm that test exists and passes, not to read the markup. A constraint worth explaining in a shipped comment is worth asserting in a test instead.

**Harness quality loop (added 2026-09-24):** before implementation, `tasks.md` maps every AC — including non-`[MUST-TEST]` criteria — to a concrete validation method, stage, evidence location, and owner. Lane M/L adds one bounded domain-matched assumption challenge during the existing governing-document review, while failed gates append a compact measured row to the run's postmortem so repeated failures, correction cost, and candidate preventive checks are reviewed before a durable rule is added; the formats and gates live in `.claude/process/harness-quality-loop.md` (→ RP-34).

## Agents — where they live (added 2026-09-05)

Skills need no adaptation: OpenCode reads `.claude/skills/` and `.agents/skills/` natively, so all repository skills are already visible to it. Agents do need it. OpenCode rejects Claude Code's agent frontmatter — `tools` must be an object rather than a comma-separated string, `color` must come from a fixed palette (`primary`/`secondary`/`accent`/`success`/`warning`/`error`/`info`), and `model`, `effort`, and `skills` mean nothing to it. A symlink therefore fails config validation.

`agents/*.md` (symlinked as `.claude/agents/*.md`) stays the single source of truth. `.opencode/agent/*.md` is **generated** from it by `.opencode/sync-agents.py`, which drops `name`/`tools`/`model`/`effort`, maps `color`, sets `mode` (`all` for `team-lead-coordinator`, `subagent` for the rest), and prepends two blocks: a vocabulary map (Agent/Task tool → `task`, `subagent_type` → agent name, Agent Teams → the documented one-shot fallback) and, replacing the unsupported `skills:` preloading, an instruction to load those skills with the `skill` tool.

**Editing an agent means editing `.claude/agents/`, then re-running both `.opencode/sync-agents.py` and `.codex/sync-agents.py`.** The generated files carry a header saying so. Never edit `.opencode/agent/` or `.codex/agents/` directly — the next sync overwrites it.

`.codex/agents/*.toml` is generated deterministically by `.codex/sync-agents.py`. Codex automatically discovers these project-scoped files; do not add absolute `config_file` entries to `~/.codex/config.toml`, and do not require a multi-agent feature flag unless the user has explicitly disabled agents. The generator owns each profile's required `name`, concise `description`, `developer_instructions`, model, reasoning effort, and least-privilege sandbox setting; it also supplies the coordinator's Codex operating-mode adaptation. Run `.codex/sync-agents.py --check` to validate freshly rendered TOML, compare it with generated output, and detect schema, coverage, or drift failures.

## Spec-Driven Development is the team standard

All six delivery-team agents now mandate a **GitHub SpecKit-style** spec-driven workflow when deployed into a target project: `/specify` → `/plan` → `/tasks` → `/implement` → `/verify` → `/archive`, with feature artifacts under `<target-project>/specs/NNN-<feature-slug>/`. **No `specs/` directory ever lives in this config repo** — this repo is team definition only. `.claude/skills/sdd-workflow/SKILL.md` is the authoritative spec of the workflow.

If asked about specs, paths, feature numbering, or sizing, refer to the SDD section in any of the agent files (they're identical). The trivial-fix escape hatch has been replaced by the size lanes below — XS *is* that hatch, with S/M/L between it and the full pipeline.

**Partial supersession** (added 2026-08-23, project-a feature 028, DEC-1): a second post-merge-modification mode alongside full supersession, for when only some of a shipped spec's FR/AC IDs need to change. Full six-invariant definition lives in `team-lead-coordinator.md`; the load-bearing one is that a reused ID must replace that exact ID, and every genuinely new requirement/criterion takes an ID the superseded spec doesn't use — otherwise traceability quietly depends on whether test headers happen to carry a spec tag. `product-owner.md`, `lead-system-architect.md`, `senior-software-engineer.md`, and `devops-infra-expert.md` each carry a shorter pointer to the same rule.

## Size lanes — the spec is weighted to the risk (added 2026-08-27)

`/specify` and `/plan` are tiered by risk, the way review already was. The lane is set by **what the change touches, never by how it is framed** — the same objective test as the design gate (→ `.claude/process/rule-provenance.md` RP-18).

| Lane | Trigger | Artifacts |
|---|---|---|
| **XS** | doc-only, comment-only, or a bugfix with no behavior change | a row in `tasks.md` |
| **S** | presentation, copy, styling, a tuned value, a contained bugfix — and no contract, persisted data, infra/deploy topology, auth, money, legal/GDPR surface, or second deployed artifact | `spec.md` ≤120 lines, five-section S template, **no `plan.md`**, **one MR** |
| **M** | new behavior inside existing contracts, one deployed artifact | `spec.md` ≤250 + `plan.md` ≤250 |
| **L** | any S exclusion | full pipeline, no budget |

- A lane above S must name an exclusion from the table; bookkeeping volume is not one. Tier down only with the stakeholder's explicit approval (→ RP-26).
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

## Rule hygiene (added 2026-08-27)

Agent definitions load in full on every spawn, so their length is a running cost on every task the team runs (→ RP-18). Three constraints, enforced when editing any agent definition here:

1. **A rule body is ≤2 sentences plus a `(→ RP-nn)` citation.** The narrative goes in `.claude/process/rule-provenance.md`, never inline. An agent must be able to comply having read only the rule.
2. **Adding a rule requires naming what it replaces**, generalizes, or — failing both — why it does not overlap an existing one. "It is new" is a claim to check against the file, not an exemption.
3. **A rule with no gate is a suggestion.** Name where it is checked (`/tasks`, `/verify`, the review attestation) or do not add it.

## Editing agent definitions

- Frontmatter `name` must match the filename stem. Renaming an agent means renaming the file and updating references in `team-lead-coordinator.md` (which maps roles → `subagent_type`).
- `tools:` empty means inherit all from the spawner; otherwise it's an explicit allowlist. The five authoring agents have `Bash`, `Read`, `Write`, `Edit` so they can produce their SDD artifacts (spec.md, plan.md, etc.) and push them via `glab` CLI or a configured GitLab MCP. The boundary against architect/PO writing source code is intent-based — enforced by their system prompts and the coordinator's `/verify` gate, NOT by their tool list. Effective git/GitLab read/write scope is governed by the configured auth (MCP scope or `glab` token), not by anything in the agent definitions.
- **Shared blocks live once, as preloaded skills.** An agent definition's body is used verbatim as its system prompt and cannot `@import`, but the `skills:` frontmatter field injects a skill's full content into the agent's context at spawn — verified 2026-09-02 on 2.1.258, including that a *rule* placed in a preloaded skill is actually obeyed. The shared blocks are therefore skills, not copies: `.claude/skills/sdd-workflow/` (the SDD block, which contains the size lanes and the spec-change-management pointer as subsections), `.claude/skills/team-wiki/`, `.claude/skills/teammate-protocol/`, and `.claude/skills/gitlab-access/`. Edit the skill; there is nothing to keep in lockstep and no drift checker to run.
  - One copy remains inline and is intentional: `team-lead-coordinator.md` keeps its own longer SDD variant (its non-negotiables differ structurally).
  - `lead-system-architect.md` keeps one role-specific paragraph inline ("Lane S — your design input has no `plan.md`"); the rest comes from the skill.
  - **Preloading does not apply when an agent runs as the main session** (`claude --agent <name>`), only when it is spawned as a subagent. The GitLab trigger therefore tells that session to read `${CLAUDE_PLUGIN_ROOT}/.claude/skills/gitlab-access/SKILL.md` directly; its procedure remains only in the skill.
- Each agent file also embeds a short **"Durable learnings live as artifacts, not memory"** section pointing learnings at `collaboration-traces/`, the target project's `AGENTS.md`, ADRs, or this agent's definition. The role-specific bullets differ; the spirit is identical. Keep them aligned if you edit one.
- **Seven agents preload the `team-wiki` and `gitlab-access` skills.** The wiki protocol lives in `.claude/process/wiki.md`; its pointer lives in `.claude/skills/team-wiki/SKILL.md`.
- **Never create project-specific artifacts here.** No `specs/`, no source code, no Dockerfiles, no application configs. If a request seems to imply adding such artifacts, push back: those belong in the target project.

## Commands

There is no application to build or test. After editing an agent definition, regenerate both ports and validate Codex output:

```sh
.opencode/sync-agents.py
.codex/sync-agents.py
.codex/sync-agents.py --check
```

Also inspect the generated diff and confirm source frontmatter remains intact.
