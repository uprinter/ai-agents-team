# Repository guidance

This file provides shared guidance to Claude Code, Codex, and OpenCode when working in this repository.

## What this repo is

This is **not an application** — it is a reusable agent-team configuration for Claude Code, Codex, and OpenCode. There is no application build or runtime. `agents/` (symlinked as `.claude/agents/` for the standard Claude Code project convention) is the source of truth; `.codex/agents/` and `.opencode/agent/` are generated ports, and repository skills are shared across runtimes through `.agents/skills/` and `.claude/skills/` (the latter holds every skill's real directory; see *Skills — where they live*).

- `.claude/agents/*.md` — agent definitions, each with YAML frontmatter (`name`, `description`, `tools`, `model`, `color`) followed by the agent's system prompt. Six form the SDD **delivery team** (see *The team*); the rest are standalone (see *Standalone agents*).
- `.claude/collaboration-traces/<date>-<topic>/` — postmortems and traces from team test runs. This is where durable findings about team behavior live.
- `.claude/process/` — shared team process that agent definitions **point to** rather than embed:
  - `rule-provenance.md` — incident narratives behind non-obvious rules, as append-only `RP-nn` entries cited as `(→ RP-nn)`.
  - `gates.md` — full text of the delivery and review gates (design, scope, copy, simulated-user, search-visibility, docs, hygiene).
  - `standalone-agents.md` — full descriptions of the standalone agents.
  - `harness-maintenance.md` — agent ports, skill locations, size-lane detail, partial supersession, closure records, agent-editing detail.
  - `harness-quality-loop.md`, `spec-change-management.md`, `seo-lifecycle.md`, `wiki.md`, `teammate-protocol.md`, `verify-log.md`, `verify-gates.md`, `decision-protocol.md`, `heavy-files.md` — one per topic in its name.
- `.claude/settings.local.json` — permission allowlist (not committed-as-team-config; local overrides).

**No agent-memory.** This team does not maintain per-agent memory files. Durable learnings live as artifacts instead: postmortems under `collaboration-traces/`, per-target-project conventions in that project's `AGENTS.md`, architectural decisions as ADRs in the target project, and team-wide rules in the agent definitions themselves. If you find yourself wanting to write a memory file, edit one of those instead.

**Use direct programmatic tools by default.** Use the target system's purpose-built API, MCP connector, or authenticated CLI; never route through a browser, GUI, workflow platform, another service's credential, or another indirect tool unless the scenario explicitly requires it or the user approves that exact alternative first. If the normal path is unavailable, report the blocker and request configuration or approval instead of improvising another access path. Google services use only the one account set up for AI automation (→ RP-31, RP-33, RP-70).

**GitLab access.** Before any GitLab API or authenticated Git transport operation, every agent must follow `gitlab-access`; Claude source agents keep an exact-path read fallback for main-session use, while generated Codex and OpenCode prompts enforce runtime-native loading. The skill owns authentication diagnosis, exact-SHA transport verification, and secret handling, with runtime-specific details disclosed only when needed (→ RP-31, RP-33).

**Assign every GitLab issue.** Use `@your-agent-bot` by default; assign `@your-human-operator` only while the current next action requires a direct human operation, then return the issue to `@your-agent-bot` when that action is complete (→ RP-32).

**This repo outranks a target project's `AGENTS.md`.** A target's `AGENTS.md` is authoritative for that project's own conventions — its stack, its layout, its local commands — and nothing here displaces those. But where it contradicts this repo on team process — a role boundary, a gate, an SDD stage, a size lane — this repo wins, and the contradiction is a defect to fix in the target project, never a local exemption to follow. An agent that finds one says so instead of silently picking a side; the check belongs in the review attestation of any diff touching a target's `AGENTS.md`.

**Shared knowledge base (the wiki).** All agents use one cross-project Obsidian vault — `https://gitlab.com/<your-org>/wiki/<you>` (local: `~/Documents/Projects/obsidian/<you>/`) — as long-lived team memory. Lane M/L and research work read it first and contribute back; XS, lane S, reviews, `/verify` and UX runs skip it (→ RP-46). It is external, human-curated knowledge, not per-agent memory, so the no-memory rule holds. Protocol: `.claude/process/wiki.md`, loaded via the `team-wiki` skill.

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

**Domain split — application code vs. IaC/manifests.** `devops-infra-expert` investigates, authors and commits Terraform, Helm charts and Kubernetes manifests in `oci-k8s-platform` and `cicd` (state-changing git steps still need per-action human approval); `senior-software-engineer` takes application code only. **Review follows the same split**: IaC/manifest MRs are reviewed by a second `devops-infra-expert` instance, never `code-reviewer` (see "Review separation of duties (IaC/manifest MRs)" in `devops-infra-expert.md`; → RP-55).

**Nothing lands on a target project's `main` except through an MR** — post-`/verify` documentation edits go through a Tier-0 MR (engineer authors, second instance attests); no agent, the coordinator included, pushes to `main` directly (`team-lead-coordinator.md` Core Operating Rule 6; → RP-02).

**Two-party review is evidenced by attestation, not by GitLab accounts.** All agent instances share one GitLab identity, so the audit trail cannot distinguish author from reviewer. The reviewer therefore posts a structured `REVIEW-ATTESTATION` note (SHA, files/lines reviewed, findings, spec refs, reviewer instance token) before approving, and `/verify` audits it against the real diff and the approval timestamps; approval without a valid attestation is a self-approval. Full format lives in `code-reviewer.md`; the `/verify` check lives in `team-lead-coordinator.md` (SDD non-negotiable 4).

**Strict delegation, always — including for whoever is driving the team.** The root/orchestrating session never implements code, IaC or config in a target project, however small or certain the change; it dispatches `senior-software-engineer` (or the relevant specialist) and requires independent review before merge (→ RP-55). Direct tool use stays fine for verification, investigation, and git/process operations on an approved change — never for writing or editing what ships.

**The request bounds the work — this binds the root/orchestrating session too.** A finding is not a feature: found work is never dispatched, spec'd or offered mid-task, and a finding inside the requested change rides that feature's existing MR at its lane weight. Per `.claude/process/decision-protocol.md` §1a, trivial in-change findings are fixed silently and recorded; a real problem is one `Separate task proposed:` line at close, three at most (→ RP-25, RP-52; `team-lead-coordinator.md` Core Operating Rule 16). A branch or MR this session did not create is not touched without its owner's confirmation (Rule 21, → RP-60).

**Backlog status follows the work — this binds the root/orchestrating session too.** On a task from a backlog card, set `Status: In progress` in the same turn as the dispatch and `Done` once the evidence passes; the closing message names the card's status (→ RP-56).

**Decide small things, ask big things in eight lines — this binds the root/orchestrating session too.** A choice one MR reverses with no outside trace (doc wording, naming, styling, test data) is decided and recorded, never put to the stakeholder. A decision with a lasting visible consequence is asked in the eight-line format of `decision-protocol`: one decision, recommended option first, no job IDs, SHAs or paths. A relayed ask is forwarded as is or shorter (→ RP-45; Core Operating Rule 19, the `asks=` field of the `gates:` line).

**A notice with no new data gets no reply — this binds the root/orchestrating session too.** A completion notice whose report was already relayed is answered with nothing; the next message to the stakeholder carries only what changed or what waits on them (→ RP-65).

**The dispatch brief states what changes and the constraints — never roles, stages or artifacts.** The root session says what the stakeholder asked for, what must not regress and what evidence settles it; `team-lead-coordinator` assigns the lane from the diff surface (Core Operating Rule 11). Naming "the full SDD lifecycle" or `lead-system-architect` in a brief is tiering up without approval. A lane above S must name an exclusion from the size-lane table; bookkeeping volume is not one, and restated superseded IDs go to `specs/NNN-<slug>/evidence/superseded-ids.md` (→ RP-26).

**Coordinator operates as a Claude Code Agent Team lead** (per `https://code.claude.com/docs/en/agent-teams`), which requires:
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Claude Code v2.1.32+
- Coordinator running in the main session (teammates cannot spawn their own teams)

If those preconditions aren't met, the coordinator falls back to the regular `Agent` sub-agent tool.

## Standalone agents

Outside the delivery team and not coordinated by `team-lead-coordinator`. Full descriptions: `.claude/process/standalone-agents.md`.

- `seo-specialist` (agent) — organic search and AI visibility audits per `seo-lifecycle.md`; writes docs only.
- `taste-critic` (agent) — screenshot-only judge of visual taste (hierarchy, rhythm, finish, fit); reports only.
- `user-eyes-tester` (agent) — first-time-user UI test from screenshots; reports only.

## Skills — where they live

Every skill is reachable from **both** `.agents/skills/` and `.claude/skills/`: one path holds the real directory, the other a symlink. Installed developer skills are real in `.agents/skills/`; team-process skills authored here are real in `.claude/skills/`. **Adding a skill means creating both entries**, or half the tools cannot see it. Detail: `.claude/process/harness-maintenance.md`.

**Gates.** Each gate has an authoring rule, a reviewer check and a `/verify` block; full text in `.claude/process/gates.md` (→ RP-18). The gates: design-quality, scope-integrity, copy-brevity, simulated-user, search-visibility, documentation-prose, shipped-artifact hygiene, single test verification with fail-fast tooling, harness quality loop.

## Spec-Driven Development is the team standard

All six delivery-team agents now mandate a **GitHub SpecKit-style** spec-driven workflow when deployed into a target project: `/specify` → `/plan` → `/tasks` → `/implement` → `/verify` → `/archive`, with feature artifacts under `<target-project>/specs/NNN-<feature-slug>/`. **No `specs/` directory ever lives in this config repo** — this repo is team definition only. `.claude/skills/sdd-workflow/SKILL.md` is the authoritative spec of the workflow.

If asked about specs, paths, feature numbering, or sizing, refer to the SDD section in any of the agent files (they're identical). The trivial-fix escape hatch has been replaced by the size lanes below — XS *is* that hatch, with S/M/L between it and the full pipeline.

## Size lanes and closure records

The lane is set by what the change touches, never by how it is framed (→ RP-18). Definitions: `.claude/skills/sdd-workflow/SKILL.md`; gate: `team-lead-coordinator.md` Core Operating Rule 11.

| Lane | Trigger | Artifacts |
|---|---|---|
| **XS** | nothing user-visible: doc-only, comment-only, or a bugfix with no behavior change | a row in `tasks.md` |
| **S** | presentation, copy, styling, a tuned value, a contained bugfix — and no contract, persisted data, infra/deploy topology, auth, money, legal/GDPR surface, or second deployed artifact | `spec.md` ≤120 lines, `tasks.md`, no `plan.md`, no architect spawn, one MR |
| **M** | new behavior inside existing contracts, one deployed artifact | `spec.md` ≤250 + `plan.md` ≤250 |
| **L** | any S exclusion | full pipeline, no budget |

A lane above S must name an exclusion; tier down only with stakeholder approval (→ RP-26, RP-47). Partial supersession, lane-S branch rules, and batched `/verify` closure records (`specs/verify-log.md`, Core Operating Rule 12) are in `.claude/process/harness-maintenance.md` and `.claude/process/verify-log.md`.

## Rule hygiene

Agent definitions load in full on every spawn, so their length is a running cost on every task (→ RP-18). Four constraints, enforced when editing an agent definition:

1. **A rule body is ≤2 sentences plus a `(→ RP-nn)` citation.** The narrative goes in `.claude/process/rule-provenance.md`, never inline. An agent must be able to comply having read only the rule.
2. **Adding a rule requires naming what it replaces**, generalizes, or — failing both — why it does not overlap an existing one. "It is new" is a claim to check against the file, not an exemption.
3. **A rule with no gate is a suggestion.** Name where it is checked (`/tasks`, `/verify`, the review attestation) or do not add it.
4. **Size is budgeted.** `AGENTS.md` and each agent file stay within their entry in `.claude/scripts/size-budget.json`, enforced by `check_harness.py`; the `harness-cleaner` skill finds what to merge or remove.

## Editing agent definitions

- Frontmatter `name` must match the filename stem; renaming means updating `team-lead-coordinator.md`.
- Shared blocks live once as preloaded skills (`sdd-workflow`, `team-wiki`, `teammate-protocol`, `gitlab-access`, `decision-protocol`); edit the skill, not copies. Preloading does not apply to a main-session agent, so its GitLab trigger reads `.claude/skills/gitlab-access/SKILL.md` directly.
- Keep each agent's "Durable learnings live as artifacts, not memory" section aligned.
- **Never create project-specific artifacts here** — no `specs/`, source code, Dockerfiles or app configs.
- Full detail (tool allowlists, preload counts, inline exceptions): `.claude/process/harness-maintenance.md`.

## Commands

There is no application to build or test. After editing an agent definition, regenerate both ports (never edit a generated file) and validate Codex output:

```sh
.opencode/sync-agents.py
.codex/sync-agents.py
.codex/sync-agents.py --check
```

Also inspect the generated diff and confirm source frontmatter remains intact.
