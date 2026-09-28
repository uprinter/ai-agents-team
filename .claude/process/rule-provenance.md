# Rule provenance

Every non-obvious rule in the delivery-team agent definitions was adopted after a specific incident. Those incident narratives used to live inline in the rule bodies, which meant every agent re-read ~9 KB of history on every spawn to arrive at rules it could read in a line. They live here instead.

**How to use this file.** Agent definitions cite provenance as `(→ RP-nn)`. You do **not** need to read this file to follow a rule — the rule text is self-contained. Read the entry when you are about to weaken, generalize, or argue with a rule, when you are writing a postmortem that touches it, or when you need to know whether a new incident is a repeat.

**How to add to it.** A new rule gets a new `RP-nn` entry here (never a narrative inline in the agent file) and a `(→ RP-nn)` citation at the rule. See the rule-hygiene constraint in the repo `AGENTS.md`.

Entries are append-only and immutable once written, except to add a "repeat" line when the same failure recurs.

---

## RP-02 — Coordinator pushed a closure record straight to `main`
**Date:** 2026-08-22 · **Where:** `project-a`, feature 025 · **Rules it backs:** nothing lands on `main` except through an MR, documentation included; post-merge spec edits are Tier-0 MRs.

The coordinator pushed the `/verify` closure record `266c672` directly to `origin/main`, bypassing the flow the same file's T11 fix had followed the day before via MR !61. The content was harmless; the precedent is what must not stand.

## RP-03 — A "capture mechanism" shipped as a zero-CSS form
**Date:** 2026-08-18 · **Where:** `project-a`, feature 018 · **Rules it backs:** design gate end-to-end (PO visual ACs, engineer screenshot loop, reviewer design check, coordinator `/verify` block); UI-touching is classified by the diff, never by framing.

The task was framed as an "email capture mechanism," so nobody classified it as UI work. It shipped a signup form with semantic class names, full test coverage, and zero CSS — browser-default controls on a styled dark page. The 62 KB spec covered GDPR, retries, and copy exhaustively but contained no visual AC, so `/verify` passed it legitimately.

## RP-04 — A placeholder shipped in place of the feature, twice
**Dates:** 2026-08-20, repeat 2026-08-21 · **Where:** `project-a`, features 018 and 024 · **Rules it backs:** scope integrity; half-built functionality is never customer-visible; interim phases ship dark; a feature that touches a pre-existing placeholder inherits the obligation to hide it.

A "Clear-sky alerts" feature — promising an email when a forecast clears — was delivered as a static "Not built yet" page whose only working part was an email-capture form. No forecast-monitoring or alert-delivery logic existed, and it was reported as shipped. **Repeat:** feature 024 then restyled that same placeholder and re-shipped it to production. Nobody flagged it, because the brief said to keep it and the rule as then written allowed a labeled interim phase to be user-visible. It no longer does.

## RP-06 — An unreviewed commit rode into a squash-merge via the branch base
**Date:** 2026-08-21 · **Where:** `project-a`, feature 024, merge `b0d0865` · **Rules it backs:** always `git fetch` and cut branches from `origin/main`, never local `main`; `/verify` diffs the pre-merge tip against the merge commit.

Local `main` was one unpushed comment-only commit ahead when the feature branch was cut. GitLab squash-merges against the *remote* base, so that commit was folded into the merge unreviewed — invisible to the author, the reviewer, the MR description, and the attestation alike, because the `--sha` pin fixes the branch head, not the base. The payload was harmless; the mechanism is not, and it was caught by an ad-hoc re-diff rather than by process.

## RP-08 — Implementation MRs merged before the spec/plan MR that governed them
**Date:** 2026-08-22 · **Where:** `project-a`, feature 027, MRs !65/!66/!67 · **Rules it backs:** "committed to the target project" means merged to `main`, not present on a branch; sequence the spec/plan merge ahead of implementation merges.

The spec/plan branch's own MR was still open and under Tier-0 review while the two implementation MRs it governed were dispatched, reviewed, and merged to `main`. The engineer read correct, stable spec/plan content off the open branch throughout, so nothing was implemented off-spec — the consultation *intent* held; the literal ordering rule did not. Blocking the implementation MRs at the point this was noticed would have added delay with no correctness benefit, since !67's block was about documentation consistency and nothing !65/!66 depended on.

## RP-09 — An MR sat approved against a stale attestation
**Date:** 2026-08-15 (user-approved) · **Where:** `project-a`, feature 016 · **Rules it backs:** merges must be SHA-pinned (`glab mr merge <id> --sha <reviewed-sha> --squash --remove-source-branch`).

An MR remained approved after two post-approval pushes, so the approved SHA no longer matched the branch head. Only manual agent re-checking caught it before merge, and the checking agent had no server-side backstop if it had not. The `--sha` pin converts this from an audit-time discovery into a server-side refusal — which matters because GitLab never re-opens approval state after a merge (`user_can_approve: false` once `state: merged`, confirmed 2026-08-16, feature 004, MRs !18/!23), so after merge only half the fix is available.

## RP-10 — Partial supersession, and its own invariant violated on first draft
**Date:** 2026-08-23 · **Where:** `project-a`, feature 028, DEC-1 · **Rules it backs:** the six partial-supersession invariants, in particular that an ID may be reused only where it replaces that exact ID.

DEC-1 was drafted by `product-owner` and refined across two review rounds after the first draft violated its own invariant 6: it got the FR side right (reused `FR-6/7/33`, took a fresh `FR-45`) and the AC side wrong (reused `027`'s still-active `AC-4/5/6` range). Independent review caught it; the invariant existing in someone's head did not. 028's own implementation suite has proxy tests citing collision-set AC IDs with no spec attribution, which is why the rule must be restated explicitly in every partial-supersession spec rather than inferred from the FR-side example.

## RP-13 — Clickops where the Terraform resource already existed
**Date:** 2026-08-20 · **Where:** `project-a`, feature 018 Lane A · **Rules it backs:** IaC first; no console/CLI provisioning with a "codify later" follow-up.

A runbook created an OCI email domain and DKIM via `oci email domain create` / `oci email dkim create`, with an explicit "follow-up owed" to codify into Terraform later — even though `oci_email_email_domain` and `oci_email_dkim` were already fully supported in the installed provider version. The stakeholder caught it and asked "why not terraform, no clickops" before any DNS was published; it was redone as IaC.

## RP-14 — A spec's own copy AC was stricter than the skill, and trapped compliant work
**Date:** 2026-08-23 · **Where:** `project-a`, feature 028 · **Rules it backs:** a copy AC restates the `ux-copy` bar, never tightens it.

The spec's copy AC demanded one sentence per string. Two of that same spec's own compliant strings failed it. Because the reviewer is required to check against the spec's AC rather than the skill, an over-strict AC sets a trap for a correct implementation.

## RP-16 — The approval-timing floor was skipped, not absent
**Date:** 2026-08-16 · **Where:** feature 004 retrospective · **Rules it backs:** risk-tiered review weight (Tier 0/1/2); the Tier 1 floor is symbolic (15s), not a diligence proxy.

11 of 19 MRs cleared the SHA and attestation checks but went from attestation to approval in 1–3 seconds. Across every violation found, the old 120-second floor was either missed by seconds or cleared by minutes — it never once caught a genuine near-miss, so shortening it to a symbolic floor loses nothing real while keeping full ceremony where it earns its cost (Tier 2).

## RP-18 — Small features cost as much as large ones
**Date:** 2026-08-27 · **Where:** repo-wide review against `project-a`, `cicd`, `project-b` · **Rules it backs:** size lanes XS/S/M/L; spec and plan line budgets as `/verify` gates; S ships as one MR; the rule-hygiene constraint.

Review weight had been tiered by risk since 2026-08-16 (RP-16); specification weight never was, and the only escape hatch covered pure bugfixes and doc-only changes with `default is no`. Making a header logo smaller (`032`) cost 94.7 KB of spec and plan — 15,490 words — against one CSS rule; shortening four strings (`028`) cost 1,054 lines across four MRs. Meanwhile 29 of the last 60 commits on `main` were `docs`, three consecutive specs (`027→028→029`) reworked the same signup copy, and `team-lead-coordinator.md` had grown from 20.9 KB to 57.8 KB by pure append.

## RP-20 — Integrity gates held; bookkeeping gates were skipped unnoticed
**Date:** 2026-08-29 · **Where:** `project-a` `!86`–`!100` (features 032–038) · **Rules it backs:** the verify-log entry is `/verify`'s completion condition and carries a fixed `gates:` roll-call.

An audit of the fifteen most recent merges found every integrity gate held — 15/15 on attestation, `reviewed-sha` matching the merge head, squash-and-delete, and Rule 9 branch-base cleanliness on all seven spot-checked. Every bookkeeping gate failed instead: `specs/verify-log.md` was never created; `036`/`037`/`038` sat at `status: Draft` while live on `main`; `037` merged at 125 lines against lane S's 120 with no cut and no re-classification; nine consecutive features shipped with no `tasks.md`, leaving Rules 7 and 10's labelling step with no carrier; and `038` closed with six separate post-merge documentation MRs — four of them amending the same file within 105 minutes — one day after Rule 12 required them batched.

The pattern is the diagnosis: the gates that held are checked at the MR, where someone stops. The gates that failed were checked nowhere anyone stops, and `/verify` left no artifact, so "was it run?" was unanswerable after the fact. Making the log entry `/verify`'s completion condition closes that; the `gates:` line forces each skipped item to be answered explicitly rather than omitted.

## RP-21 — Every gate watched the user-visible surface; nothing watched the crawler-visible one
**Date:** 2026-08-30 · **Where:** `project-a` / `project-a.example.com`, live · **Rules it backs:** crawler-surface work carries an implementation and review dimension against `technical-seo`; a nonexistent URL must not answer `200`.

A live check of the deployed site found every URL answering `200 text/html`, including `/robots.txt`, `/sitemap.xml`, `/this-page-does-not-exist`, and `/a/b/c/nonsense` — the nginx `try_files … /index.html` catch-all serving the app shell for every path. So `robots.txt` was not missing but malformed (a crawler receives HTML where it must receive `text/plain`), and every mistyped or stale inbound link became a distinct 200-OK near-duplicate page, an unbounded soft-404 surface. The 2,938 bytes of markup a crawler receives before JavaScript runs carried no `rel="canonical"` and no structured data at all.

This had been true since launch, across thirty-eight shipped features, and no gate could have caught it. The design gate (→ RP-03), the scope-integrity gate (→ RP-04), and the copy gate all classify by *what a user sees* — and by that test this defect is invisible, because the site renders perfectly in a browser. Nothing in the pipeline read a status code or a `Content-Type`. This is RP-20's diagnosis in a new place: the gates that hold are the ones checked where someone stops, and no one was stopping at the crawler's view of the site. The fix is a trigger classified by the diff's effect on the crawler surface rather than the user surface, which is deliberately not a subset of "UI-touching" — a routing rule or a redirect changes it while touching no DOM.

## RP-22 — Internal traceability shipped to the public document, and review added more of it
**Date:** 2026-08-30 · **Where:** `project-a` / `project-a.example.com`, live · **Rules it backs:** shipped artifacts carry no internal traceability; the check is a build-time assertion, not a review item.

The stakeholder opened view-source on the homepage and found four HTML comments disclosing feature numbers, `FR-`/`AC-`/`DEC-`/`ADR-` identifiers, internal file paths (`main.ts`, `plan.md §3.1`), the existence and role of the `preview/` service, and how the client bootstraps its DOM. Three had been served since features 002, 010 and 016/033. **The fourth was added that same day by feature 040** — through a full two-party review that checked the search-visibility dimension against `technical-seo` and passed, with an attestation recording no findings.

Every gate had a reason to miss it, and the pattern is the point. The design gate classifies by *user-visible DOM* and a comment renders nothing. The copy gate classifies by *strings a user reads* and a comment is not read. Rule 14 has the only correct trigger — a comment is unambiguously part of what a crawler receives — but its checks enumerate status codes, `robots.txt`, canonicals and structured data, so a reviewer following it literally finds nothing to look at. Scope integrity is about placeholders. Four gates, none of which was wrong, and the defect fell between all of them.

It also contradicted a standing stakeholder instruction — no decision-history comments in source, that belongs in commits and spec docs — which existed as a preference recorded nowhere the team reads at review time. That is the hygiene constraint's own prediction: a rule with no gate is a suggestion. The remedy is deliberately not another review dimension, because review demonstrably passed this three times: it is a build-time assertion over the built artifacts, which fails CI before a human is asked to notice anything.

## RP-24 — A project already had a token dictionary, and the new component ignored it
**Date:** 2026-09-02 · **Where:** `project-a` feature 051 (darkness legend restoration), live · **Rules it backs:** the UI definition-of-done and the design-dimension review must trace new values to the project's own token documentation, not judge them by whether they "look consistent."

The stakeholder flagged a visually broken legend: rounded corners with zero inset from the viewport edge, unlike the map's other floating control (`#location-control`, inset `0.5rem`). The project already had the dictionary needed to catch this — a documented `--space-*`/`--radius-*` scale in `DESIGN.md`, kept in CI-enforced sync with `style.css` (`designTokens.test.ts`), with its own §12 "How to add a component" checklist: use an existing token for every spacing/radius/colour/font decision, read the document rather than the stylesheet to pick one. Feature 051's `.darkness-legend` shipped `padding: 0.45rem 0.6rem` (matches no token in the scale) and `border-radius: 0.375rem` (numerically equals `--radius-md`, but hardcoded instead of `var()`), and its container inherited the zero-inset position built for an unrelated, deliberately flat design (046's link row) instead of the `--space-sm` inset the project's other floating card already uses. `designTokens.test.ts` only catches a token declared in one file and absent from the other; it has no way to see a raw literal that should have been a `var()` reference.

Both the engineer's and reviewer's gates existed and were satisfied on paper — "visually consistent with the components around it" and "UI visibly inconsistent with the surrounding design system [is blocking]" — and both are unfalsifiable as worded, since neither names what to check the diff's values *against*. `frontend-design` is a greenfield, page-level skill (palette/typeface/layout for a new brief) with no step for auditing consistency with an already-shipped system. `web-design-guidelines` fetches a fixed external checklist with no concept of a project's own internal token scale. The fix was neither skill's job — it was the project's own `DESIGN.md` §12 checklist, already written, never run against this diff.

## RP-25 — One request became eight, because found work was offered instead of recorded
**Date:** 2026-09-04 · **Where:** `cicd`, nginx demo-app removal · **Rules it backs:** the request bounds the session's work; work found while investigating is recorded as text, never dispatched.

The stakeholder asked for one thing: remove the nginx demo ArgoCD Application from the repo and the cluster. Eight commits landed on `cicd` `main`, of which exactly one — `51562ca` — is that request; three more landed in this config repo. The rest was work the session generated for itself: an orphaned `apps/keycloak/` directory, a decision ticket on `prune: true` and two GitLab settings, two rounds of `kubectl --dry-run` documentation corrections, five `verify-log` entries across two batch MRs, a collaboration trace, an extension to that trace, and a process-file update the trace's own entries revealed was needed.

The origin is a single decision. Having found three unrelated defects while investigating the nginx removal, the session put them to the stakeholder mid-task as an `AskUserQuestion` offering to fix them now. The stakeholder's answer selected all three options **and** "Neither — nginx removal only" in the same response — a contradiction that is itself the signal, and it was resolved toward more work rather than less. Offering found work at all is the defect; the ambiguous answer only decided how much of it got built.

Everything downstream followed mechanically. Each accepted item was classified as its own feature, so each drew a spec, an authoring spawn, a reviewing spawn, an attestation, a SHA-pinned merge, and its own closure entry — five entries for one request. Review rounds on the wording of a documentation sentence exceeded the rounds spent on deleting the manifests, and several of those rounds were findings on previous findings, a loop with no natural stop. Meta-work then bred more meta-work: a defective attestation became a trace, the trace was extended, and the closure entries exposed a stale process file that was then also updated. When the stakeholder said "wind it down and stop," it could not take effect, because five obligations were already open and every later "continue" was them unblocking a loop the session had created.

No existing rule was violated. That is the point: every rule here governs *how* a unit of work is done — its lane, its gates, its review, its closure record — and none governs *how many units a request is allowed to create*. Size lanes (Rule 11) already weight process to the surface, and by that table the doc-only changes were XS, which prescribes a row in `tasks.md`, not a spec and a closure entry of their own; the weight rule existed and was bypassed upstream, by treating each found item as a new feature at intake. So the missing rule sits before lane classification, not beside it: a finding is not a feature, and the human's request is the only thing that authorizes one.

## RP-26 — Tiering up was free, so bookkeeping — not risk — set the lane
**Date:** 2026-09-05 · **Where:** `project-a` features 053, 055, and the 056 dispatch · **Rules it backs:** a tier-up must name a lane-S exclusion; restated superseded requirements live in `evidence/`; the dispatch brief never pre-assigns lane weight.

The stakeholder asked for two visual defects to be fixed and got the full team, the architect included. Three separate causes, all on the record.

The first is the dispatch brief. The orchestrating session's brief told the coordinator to "run the full SDD lifecycle" and named `lead-system-architect` as owner of a CSS byte-budget decision. Core Operating Rule 11 gives lane assignment to the coordinator and lane S needs no architect spawn, but nothing in the team definition constrained what a brief may contain, so a brief written above the coordinator overrode the rule beneath it. Rule 16 already bounds *how many* features a request may create; nothing bounded *how heavy* the one requested feature is allowed to be.

The second and third are older and cost more. Feature 053 — revert an icon to grey and drop its box — shipped as **lane M with a 22.0 KB `plan.md`**, tiered up because "it retires a shipped `ADR-0083`, and an ADR needs a `plan.md` to be retired in." No such rule exists; the search that should have found it returns nothing in `lead-system-architect.md`, `sdd-workflow/SKILL.md`, or `spec-change-management.md`. Feature 055 — five presentation items on one panel — shipped as **lane L, 69.4 KB of `spec.md` + `plan.md` across four MRs**, and its own DEC-1 states the diagnosis plainly: the risk surface is M-shaped, "the *document* budget is what does not fit," and "this is bookkeeping weight, not design complexity." It replaced 27 IDs across three live specs, and `spec-change-management.md` rule 47 requires each replaced requirement restated in full. At 120 lines that restatement alone breaks lane S, and the budget rule permits exactly two resolutions — cut, or tier up — so the system funnels every change to a heavily-spec'd surface upward regardless of its risk.

Compare 054, the control: remove a white border, lane S, 9.1 KB, one MR, correct. The difference between 054 and 053 is not risk. It is that 053's surface had accumulated an ADR and 055's had accumulated 27 IDs.

RP-18 built size lanes to stop precisely this, and two bookkeeping mechanisms routed around them within nine days. The leak is the phrase "tier up freely." It was written as an escape valve for genuine uncertainty and became the default resolution for document volume, because tiering up has a stated cost of zero while cutting a document is work and needs judgment. A lane test that classifies by risk cannot hold while a separate rule sets document length by spec history, so the restatement moves to `evidence/` — where the lane rules already send reference material — and the lane returns to being a function of what the diff touches.

**Recurrence the same day, after the lane was corrected.** Told to run 056 at lane S with no architect, the coordinator produced a correct 120-line `spec.md` — and beside it a 220-line `decisions.md` carrying a new `ADR-0097` that raised the stylesheet ceiling, opening with "this file exists because `056` is lane S and therefore has no `plan.md`". 496 lines of documents and no CSS. The spec's own `NFR-Stylesheet-budget` had deferred the question to "the **architect's** call" by name, inherited from the same defective brief. So the lane label moved and the weight did not: forbidding `plan.md` forbids a filename, and a spec that names the architect re-summons the stage the lane removed. Hence the rule is on the role and the deferral, not the filename.

## RP-27 — The evidence the design gate demands was being committed, and it does not compress
**Date:** 2026-09-05 · **Where:** `project-a` `specs/`, features 016 through 057 · **Rules it backs:** design-gate screenshots are uploaded to the MR, never committed to `specs/`.

A cleanup pass measured `specs/` at 109 MB across 150 PNGs, against a repository whose entire text history is a few MB. `024-design-system` alone holds 48.9 MB, `027-email-updates-list` 13.9 MB, `031`/`032` a further 16 MB between them; `.git` had reached 197 MB. Nothing was wrong with any individual feature — the design gate (→ RP-03) requires screenshot evidence, and each feature supplied it. The gate simply never said where the files live, so they went where every other artifact goes.

The correction is only ever preventive. Deleting the files now recovers nothing: the objects are already in history, so clone size is unchanged, and the only way to shrink the repository is a history rewrite that renumbers every commit. This team pins merges to reviewed SHAs and records those SHAs in `REVIEW-ATTESTATION` notes and in `specs/verify-log.md`, so a rewrite would void the entire audit trail to reclaim 100 MB. The screenshots already paid for stay; the rule stops the next ones.

## RP-28 — A stale approval survived a push, and re-approving was a silent no-op
**Date:** 2026-09-05 · **Where:** `project-a` `!135` (feature 056) and `!138` (bookkeeping) · **Rules it backs:** re-approval after a push requires `unapprove` first, and the reviewer confirms `approved_at` postdates the attestation.

Two reviewers, hours apart and without knowing of each other's case, hit the same thing: after the author pushed a fix-up, GitLab still reported `approved: true` from before the push, and `glab mr approve` failed with a `401` instead of registering. Each independently worked it out — `unapprove`, then `approve` — and each flagged it as a process gap.

The cause is not a bug. `reset_approvals_on_push` is a GitLab Premium setting and this namespace is on the free plan; the API accepts a write to it and silently keeps `false`, which was confirmed by reading the value back twice after two attempted enables. So the setting cannot be turned on and the exposure is permanent at this tier.

What it exposes matters more than the workaround. Every merge here is SHA-pinned to a reviewed commit precisely so approval and reviewed content cannot drift apart, and `/verify` audits the `REVIEW-ATTESTATION` against the approval timestamps. A stale `approved: true` defeats both: the approval object reads as valid against a SHA nobody looked at, and the timestamp predates the attestation it supposedly followed. The existing rule already said to post a fresh approval after a push (→ RP-16); what it did not say was that the obvious way to do that does nothing. A rule whose mechanism silently fails is worse than no rule, because it produces a confident report of compliance.

## RP-29 — SEO audit heuristics became invariants, and follow-up had no operating contract
**Date:** 2026-09-06 · **Where:** requested review of `technical-seo` and `seo-specialist` · **Rules it backs:** shared SEO lifecycle gates, provider-purpose separation and current-source verification.

The existing skill required root `/sitemap.xml` with one MIME type, treated mobile-hidden content as unindexed, called all crawler-dependent markup cloaking, and made title lengths/query ownership categorical. The agent also blurred field Core Web Vitals with browser traces and contradicted itself about continuing without Search Console. Official documentation checked during this review supports narrower claims; project policies such as rendering for everyone remain policies, not invented search-engine requirements.

The lifecycle replaces the agent's one-pass audit sequence, input/artifact prose and repeated evidence rules. Its stage exits, handoff checklist and session closure check now enforce stable findings, baselines, production verification and dated outcome reviews; provider-purpose separation generalizes the previous crawl-surface checks to AI search, user fetches and training without treating access as proof of citation. The technical reviewer gate remains in the skill, so the agent does not duplicate it or take over implementation. Existing account, live-control, delivery-role and outreach boundaries are retained; documentation delivery is aligned with the standing MR-only-main rule.

Validation uses three fictional scenarios against old and revised instructions, with supplied evidence rather than a live site; it tests instruction behavior, not SEO growth.

## RP-31 — A browser was used after a programmatic GitLab path was available
**Date:** 2026-09-12 · **Where:** `ai`, delivery-tracking MR creation · **Rules it backs:** APIs, MCP connectors, and authenticated CLIs take priority over browser automation.

The branch was already pushed through Git, but MR creation moved to an authenticated browser after `glab auth status` failed. That checked only one CLI authentication path and did not first exhaust GitLab push options, direct API access, or configured MCP connectors.

Browser automation adds UI state, confirmation, and session failure modes to an operation with a stable programmatic interface. The correction is a routing rule: check purpose-built APIs and MCP connectors before browser use, and treat failure in one client as failure of that client rather than proof that no programmatic path exists.

## RP-32 — Issues were created without an accountable GitLab assignee
**Date:** 2026-09-12 · **Where:** `project-a`, initial delivery board · **Rules it backs:** every open issue has one assignee; default to `@your-agent-bot` and use `@your-human-operator` only for a current direct human operation.

The first tracked issues had labels, owners in their Markdown bodies, and concrete next actions, but no GitLab assignee. A role written inside the issue does not create GitLab ownership, so the board could show the work without showing who must act next.

This tightens Rule 17's existing handoff update rather than creating a separate ownership system. The service account remains responsible for ordinary agent work; temporary assignment to the stakeholder is reserved for a current action that requires the stakeholder directly, and the next handoff returns ownership to the service account.

## RP-33 — A credential in an unrelated automation system became an unapproved access workaround
**Date:** 2026-09-12 · **Where:** `project-a`, work-item assignee verification · **Rules it backs:** direct API/MCP/CLI access is the default; indirect tools require scenario necessity or explicit user approval.

GitLab CLI and direct API authentication were unavailable, but an n8n credential search found a GitLab credential. The session created a temporary n8n workflow to use that credential even though the request did not involve workflow automation and the user had not approved n8n as an access path; execution was stopped before any GitLab issue changed, and the workflow was archived.

The failure was treating technical availability as authorization. A tool that can reach the same destination is not automatically an acceptable substitute: when the normal target-system API, MCP, or CLI path is blocked, the correct state is blocked until the user configures it or approves a named alternative, unless the task itself clearly requires that alternative tool.

## RP-34 — The harness named gates but left three feedback links implicit
**Date:** 2026-09-24 · **Where:** review of this team harness against Ivo Kund's "Loops, graphs, harnesses" model and the team's prior incidents · **Rules it backs:** every AC has a validation route before implementation; M/L receives one bounded assumption challenge against the unchanged request; failed gates record correction cost and candidate prevention before a rule is added.

The audit found that non-`[MUST-TEST]` criteria could reach implementation without a named method, stage, evidence location, or owner; the M/L artifact cross-check reconciled product and architecture but did not ask an independent reviewer to challenge their shared assumptions; and postmortems explained adopted rules without a compact record of rejected or recurring preventive checks. RP-03 is the concrete visual example of the first gap, but this rule generalizes the missing-verifier problem to every AC while retaining the stronger design gate.

The assumption challenge extends RP-25's unchanged verbatim request into a pre-implementation gate without changing its scope rule. The failed-gate record does not replace rule provenance: it supplies the recurrence and correction-cost evidence used to decide whether a future failure needs code, clearer instructions, or no harness change; `/tasks`, the M/L governing-document review, `/verify`, and process-MR review are the enforcement points.
