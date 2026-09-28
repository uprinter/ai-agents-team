---
name: sdd-workflow
description: The team's spec-driven development workflow: the /specify -> /plan -> /tasks -> /implement -> /verify -> /archive stages, the XS/S/M/L size lanes with their artifact budgets, the non-negotiables, and the spec change management pointer. Preloaded into every delivery-team agent.
---

## Spec-Driven Development (team standard)

This team strongly follows **spec-driven development** in the GitHub SpecKit lineage. When the team is deployed into a target project, that project becomes the single source of truth for specs — every feature lives in `<project>/specs/NNN-<feature-slug>/`. The team builds nothing in the target project that isn't traceable to a spec there.

> **Important:** *this configuration repo* contains only the team definition. It does NOT contain project-specific `specs/` artifacts. All paths below are **relative to the working directory of the target project**, never to this config repo.

The workflow has five stages plus a verification gate:

| Stage                | File (in target project)                                                 | Owner                       |
|:---------------------|:-------------------------------------------------------------------------|:----------------------------|
| `/specify`           | `specs/NNN-<feature-slug>/spec.md`                                       | `product-owner`             |
| `/plan`              | `specs/NNN-<feature-slug>/plan.md` (+ `contracts/` for HTTP/data APIs)   | `lead-system-architect`     |
| `/tasks`             | `specs/NNN-<feature-slug>/tasks.md`                                      | `team-lead-coordinator`     |
| `/implement`         | source code + tests                                                      | `senior-software-engineer`  |
| `/implement` (infra) | `specs/NNN-<feature-slug>/deploy.md` + Dockerfile / manifests            | `devops-infra-expert`       |
| `/verify`            | gate; entry appended to `specs/verify-log.md` (batched, never a per-feature MR) | `team-lead-coordinator`     |
| `/archive`           | move to `specs/archive/<year>/NNN-<slug>/`; rides the same batched MR    | `team-lead-coordinator`     |

### Size lanes — spec weight is tiered by risk

**Specification weight is tiered by risk, exactly as review weight is** (Tier 0/1/2, below). The full `/specify` + `/plan` pipeline is priced for a new contract or a new service (→ RP-18).

The coordinator assigns a **size lane** at intake, records it in `tasks.md` and in the spec's `size:` frontmatter field, and classifies by **what the change touches — never by how the request is framed** (the same objective test as the UI-touching rule).

| Lane | Use when the change touches… | Artifacts |
|:--|:--|:--|
| **XS** | nothing user-visible and no behavior: doc-only, comment-only, or a bugfix with no behavior change | one row in `tasks.md`; no spec, no plan |
| **S** | presentation, copy, styling, a tuned value, or a contained bugfix — and **none** of: a contract or API, persisted data or schema, infra/deploy topology, auth or secrets, money, legal/GDPR surface, or a second deployed artifact | **`spec.md` only, ≤120 lines**, S template (`product-owner.md`); design notes are a section in it. **No `plan.md` — and no architect-authored governing document under any other filename** (→ RP-26) |
| **M** | new or changed behavior inside existing contracts, inside one deployed artifact | `spec.md` ≤250 lines + `plan.md` ≤250 lines (+ `contracts/` where applicable) |
| **L** | any of the exclusions listed under S | the full pipeline, no line budget |

Lane rules, all binding:

- **A tier-up must name a lane-S exclusion from the table above** — a contract or API, persisted data or schema, infra/deploy topology, auth or secrets, money, legal/GDPR surface, or a second deployed artifact. Tiering down still needs the human's explicit approval; tiering up is no longer free, because "tier up freely" became the default resolution for document volume rather than an escape valve for risk (→ RP-26).
- **Bookkeeping volume never sets the lane.** Supersession restatement, ID counts, spec history, and retiring an ADR are not exclusions and do not justify M or L; there is no rule that an ADR needs a `plan.md` to be retired in, and a lane-S spec's Decisions section retires one fine (→ RP-26).
- **The line budgets are `/verify` gates, not advice.** A spec or plan over its lane's budget is a blocker, cleared either by cutting it or by re-classifying the feature up a lane on the record — never by waiving the number.
- **Meet the budget by moving material, not by deleting it.** Measurements, derivations, rejected alternatives, restated superseded requirements (`evidence/superseded-ids.md`, per `spec-change-management.md` rule 2), and evidence go to `specs/NNN-<slug>/evidence/` or the run's `collaboration-traces/` entry, cited by link — a spec states what must be true, it is not the notebook that got you there.
- **S collapses the consultation round-trip:** the mandatory architect and product-owner consultations happen as comments on the single MR thread, not as separately spawned tasks with their own dependencies. If either raises a contract, data, infra, auth, money, or legal question, the feature was never S — re-classify before continuing.
- **S ships as one MR: spec, code, and tests on one branch, reviewed once.** The product owner authors `spec.md` on `feature/NNN-<slug>` (cut from `origin/main`, in its own worktree) and pushes without opening an MR; the engineer then takes that branch in its own worktree, adds code and tests, and opens the single MR covering both. Every review gate still applies in full — attestation, design check, copy check, scope integrity, SHA-pinned merge. Only the document count and the MR count shrink.
- **Artifact type is never a reason to split an MR.** One feature ships in as few MRs as its risk tiers allow: S is one; M defaults to two (governing documents, then implementation, per non-negotiable 1); L splits by risk tier, never by filename.
- **On a shared feature branch the reviewer must be a different instance from *every* instance that committed to it**, not merely from whoever opened the MR. One branch with two authors is still two authors.
- **Rework does not inherit its predecessor's lane** — a follow-up to a shipped feature is classified on its own diff (→ RP-18).

### Non-negotiables (apply in the target project)

1. **No `/implement` work begins until the lane's governing documents are committed to the target project** — `spec.md`, plus `plan.md` for lanes M and L. "Committed" means merged to `main`, not merely pushed to a feature branch (→ RP-08). Hard ordering, encoded as a task-list dependency. **Lane S is the exception by construction:** its spec and its code ship in one MR, so the ordering is internal to that MR and there is no separate spec merge to sequence.
2. **Every test file references the AC IDs it covers** in a header comment (e.g., `# covers AC-1.1, AC-2.3, FR-4`).
3. **Every code module is traceable to a `plan.md` element.** If you cannot point to the plan element your code implements, you are off-spec — stop and clarify with the architect.
4. **The coordinator's `/verify` step is the only path to "done."** It confirms every `[MUST-TEST]` AC has a passing test and every plan element has corresponding code — **and, whenever the change ships via anything not rebuilt automatically by the same CI run as the code (a container image, a manually-published data/asset bundle, a CDN-fronted static file, a separately-deployed service), that the fix is confirmed against the actually deployed/live system, not just a green test suite and a merged MR.** Passing tests and a merged MR are necessary, not sufficient: caching, deployment-sequencing, and artifact-publish drift can each mask a correct fix indefinitely and make "still broken" and "confirmed fixed" reports both look plausible depending purely on which client or cache state the report came from. "Merged" is not "done" until live behavior is checked from a clean/uncached client. **`/verify` also blocks on a stale MR description:** if review-round commits changed what the MR does after the description was first written, the author must update the description to match the final diff before merge — a description that still describes an earlier, superseded version of the change is a `/verify` blocker, since future agents (and future you) will trust that text over re-reading the diff. **Merges must be SHA-pinned to the reviewed commit:** `glab mr merge <id> --sha <reviewed-sha> --squash --remove-source-branch` — GitLab refuses the merge if the branch head has moved past the SHA a `REVIEW-ATTESTATION` named, turning that check from an audit-time assertion into a server-enforced one (confirmed 2026-08-15, feature 016: an MR sat approved against a stale attestation after two post-approval pushes, caught only by agents manually re-checking SHAs).
5. **Task breakdown must enumerate every deployed artifact affected by a changed shared contract, not just the one the feature is nominally about.** When a change alters a contract, interface, path scheme, or shared build-context dependency consumed by more than one independently-deployed artifact (sibling services in the same repo, or a consumer in another repo entirely), `/tasks` must include one explicit task per affected artifact to rebuild/republish and repoint its deploy manifest — found by checking every consumer of the changed contract, never assumed from the feature's primary framing. Within a single repo, `git diff <last-deployed-sha>..<merge-sha> --stat` per build context is the recommended concrete technique for finding affected artifacts; across repos, the equivalent is an explicit consumer inventory. A GitOps manifest pinned to an immutable image SHA does not move on its own — nothing rebuilds or repoints it except an explicit task. Tests passing and CI green for the one artifact you were focused on do not imply the others were updated.
6. **Size lanes replace the old trivial-fix escape hatch** (see "Size lanes" above). XS *is* that hatch; S, M, and L sit between it and the full pipeline. The coordinator assigns the lane, and the default is no longer full ceremony — it is the lightest lane the change's actual surface allows.
7. **Push your artifacts to the target project's remote.** Every artifact you produce (spec.md, plan.md, tasks.md, source code, deploy.md, Dockerfiles, manifests, etc.) is committed and pushed to a feature branch in the target project's git repository — typically `feature/NNN-<slug>`. Use a **GitLab MCP server** or authenticated **`glab` CLI** by default; if neither works, halt and request configuration or explicit approval for a named alternative, never route through a browser, workflow platform, or another service's credential merely because it is available. Effective scope comes from the selected tool's configured authentication, and missing GitLab access never permits silently skipping the push (→ RP-31, RP-33).
8. **Map every AC before implementation.** `tasks.md` names each criterion's validation method, stage, evidence location, and owner, including ACs without `[MUST-TEST]`; `/tasks` blocks incomplete maps and `/verify` checks the promised evidence. XS with no ACs records `n/a`. (→ RP-34)
9. **Challenge assumptions once for M/L.** During the existing governing-document MR review, a domain-matched independent reviewer posts the bounded `ASSUMPTION-CHALLENGE` defined in `${CLAUDE_PLUGIN_ROOT}/.claude/process/harness-quality-loop.md`; it preserves the verbatim request, adds no extra review round, and blocks implementation on unresolved in-scope findings. XS and S do not run this challenge. (→ RP-34)
10. **Measure failed gates before changing the harness.** Append the compact failure record to the run's existing postmortem, then review matching repeat keys before proposing a durable rule; `${CLAUDE_PLUGIN_ROOT}/.claude/process/harness-quality-loop.md` defines the formats and decision rule. (→ RP-34)

Feature numbering is sequential and immutable per target project (NNN = `001`, `002`, …). Once assigned, never renumber. Feature slug is short kebab-case (`weather-forecast`, `user-onboarding`).

If the target project does not yet have a `specs/` directory, the coordinator creates one as the first action of the first feature — and at the same time updates the target project's `AGENTS.md` (or equivalent) to note that SDD is now the convention there.

### Spec Change Management

`spec.md` is immutable once its feature branch merges to `main`. Statuses run `Draft` → `Active`, then `Withdrawn` / `Superseded-by: NNN` / `Historic` in `specs/archive/<year>/`; **`status:` and folder location always change in the same commit, or neither does.** Never delete a spec directory — archive it.

**Before you `/amend`, `/cancel`, supersede, partially supersede, remove, or archive any spec, read `${CLAUDE_PLUGIN_ROOT}/.claude/process/spec-change-management.md` in full.** It is the authoritative flow and carries invariants you cannot infer from this summary. The one that most often bites implementers: under **partial supersession** an ID may be reused only where it replaces that exact ID, every genuinely new requirement or criterion takes an ID the superseded spec does not use, and every test header cites the spec number alongside the AC ID (`covers AC-1.1 — 028`, never bare) because both specs are authoritative at once (→ RP-10).
