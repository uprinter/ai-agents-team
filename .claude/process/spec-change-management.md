# Spec change management

**Authoritative definition of the `/amend`, `/cancel`, supersession, partial-supersession, and `Historic` flows.** Agent definitions carry only a trigger-gated pointer here; this file carries the rules. Read it in full before you change, cancel, supersede, or archive any spec — the invariants below are not derivable from the summary in your own definition.

Owners: `product-owner` initiates `/amend`; `team-lead-coordinator` owns `/cancel`, `/archive`, and the status/location invariant; `lead-system-architect` cascades `plan.md`; every implementer is bound by the ID-reuse and test-header rules under partial supersession.

Every `spec.md` opens with a `status:` frontmatter line. Valid values:

| Status | Meaning | Location |
|:-------|:--------|:---------|
| `Draft` | Being written; review not started | `specs/NNN-<slug>/` |
| `Active` | Accepted; implementation in progress or shipped | `specs/NNN-<slug>/` |
| `Withdrawn` | Cancelled before any code merged to main | `specs/archive/<year>/NNN-<slug>/` |
| `Superseded-by: NNN` | Replaced by a newer spec; content frozen | `specs/archive/<year>/NNN-<slug>/` |
| `Historic` | Was shipped; feature subsequently removed | `specs/archive/<year>/NNN-<slug>/` |

**The folder location and the `status:` field must always agree — update both in the same commit.** Post-merge status flips and archive moves are not their own MR: they ride the batched verify-log MR (`team-lead-coordinator.md` Core Operating Rule 12).

Two additional stages handle changes that fall outside the happy path:

| Stage | Trigger | Owner |
|:------|:--------|:------|
| `/amend` | A requirement changes while the feature branch has not yet merged | `product-owner` initiates; `lead-system-architect` and `team-lead-coordinator` must cascade |
| `/cancel` | A feature is abandoned before any code merges to main | `team-lead-coordinator` |

**`/amend` — pre-merge modification**

1. `product-owner` edits `spec.md` in-place and notifies the architect.
2. `lead-system-architect` updates `plan.md` to reflect the change (if scope or design is affected).
3. `team-lead-coordinator` updates `tasks.md` to void, add, or re-sequence tasks accordingly.
4. All three files are committed together in a single commit. Implementation does not resume until all three are consistent. A `plan.md` that references deleted requirements is a broken state — do not leave it that way even temporarily.

**Post-merge modification (supersession)**

When a shipped requirement needs to change (code already on `main`), `spec.md` is immutable — its content does not change. Instead:

1. Open a new spec entry (`NNN-<revised-slug>`) via the normal `/specify` stage.
2. The new `spec.md` must include `supersedes: NNN-<original-slug>` in its frontmatter and a prose explanation of why the change is being made.
3. Update the old `spec.md` `status:` to `Superseded-by: NNN` and move it to `specs/archive/<year>/`.
4. The full workflow runs for the new spec.

**Partial supersession (post-merge modification, scoped)**

Full supersession (above) re-derives every requirement even when only a few actually changed — for a large spec this repeats the transcription hazard of retyping requirements that didn't change, and archiving the whole document asserts something false when most of it still governs. Use **partial supersession** instead when a shipped spec needs only some of its FRs/ACs replaced and the rest remain authoritative. (→ RP-10) Six invariants, all mandatory — this is not a looser version of supersession, it is a stricter one because two documents are authoritative at once:

1. The new spec's frontmatter and a `## Scope` section name the exact FR/AC IDs being replaced, plus the exact IDs of the superseded spec that remain in force. No open-ended phrasing like "the rest is unchanged" — enumerate.
2. Each replaced requirement is restated in full, so no reader has to merge two documents to know current behavior. **Where the restatement would push the spec past its lane's line budget, it goes to `specs/NNN-<slug>/evidence/superseded-ids.md`, linked from the `## Scope` section** — the spec still enumerates every replaced ID inline. Restatement volume is reference material, not new normative content, and never tiers a feature up a lane (→ RP-26).
3. The superseded spec's body is never edited — not even the replaced sections. It stays the historical record of what was originally decided.
4. The superseded spec's `status:` stays `Active` and it stays out of `specs/archive/` — archiving it would claim it no longer governs, which is false while most of its requirements still do.
5. Add short, strictly non-substantive forward pointers at each replaced FR/AC location in the superseded spec (and in any source comment that cites it), reading only "superseded in part by NNN — see that spec for current wording." No summary, no rationale, no wording — a pointer that adds or removes nothing is the same class of permitted post-merge edit as a `status:` flip.
6. **An ID may be reused only where it replaces that exact ID.** Every genuinely new requirement or criterion takes an ID the superseded spec does not use. This is the invariant that keeps the model safe: reused IDs make traceability depend on whether test headers happen to carry a spec tag, not on the IDs themselves — a real gap, not hypothetical (028's own implementation suite has proxy tests citing collision-set AC IDs with no spec attribution). The first draft of 028 got the FR side right (reused `FR-6/7/33`, took fresh `FR-45`) and the AC side wrong (reused `027`'s still-active `AC-4/5/6` range) — caught only by independent review, not by the invariant existing in someone's head. State the rule explicitly in every partial-supersession spec's Decisions section; do not assume the author will infer it from the FR-side example.

Process, otherwise identical to full supersession: `/specify` stage, `supersedes:` (not `Superseded-by:`) frontmatter naming the scoped IDs, cross-check at `/tasks` that every AC-ID header citation in touched test files carries its spec number (`covers AC-1.1 — 028`, not bare `covers AC-1.1`) since both specs are live simultaneously.

**`/cancel` — withdrawing an in-flight feature**

1. `team-lead-coordinator` updates `spec.md` `status:` to `Withdrawn` and adds a `withdrawn_reason:` line in the frontmatter.
2. Prepend a `## VOID — withdrawn <date>` header to both `plan.md` and `tasks.md`.
3. Move the entire `specs/NNN-<slug>/` directory to `specs/archive/<year>/` in a single commit.
4. The feature branch may then be deleted; the archived spec directory must not be.

**Post-merge removal (Historic)**

Removing a shipped feature is itself a new feature requiring its own spec:

1. Open a new spec entry (e.g., `007-remove-legacy-auth`) via the normal `/specify` stage.
2. The new `spec.md` includes `removes: NNN-<original-slug>` in its frontmatter.
3. The original spec's `status:` becomes `Historic`.
4. The full workflow runs for the removal spec.

**Anti-patterns:**
- Never delete a spec directory — archive it. Design rationale must survive indefinitely.
- Never edit `spec.md` content after its feature branch merges to main — create a superseding spec.
- Never leave a cancelled spec sitting in `specs/` (non-archive) — formally withdraw it in the same working session the decision is made.
- Never let `status:` and folder location diverge — both change in one commit, or neither does.
