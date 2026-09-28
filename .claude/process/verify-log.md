# `specs/verify-log.md` — format and worked example

One append-only log per target project, at the root of its `specs/`. It replaces the per-feature closure record that used to be appended to a merged `tasks.md` and shipped as its own Tier-0 MR (→ RP-18). Entries accumulate on the batch branch `docs/verify-log-<YYYY-MM>` and merge together; the rule is `team-lead-coordinator.md` Core Operating Rule 12.

## Why the log and not `tasks.md`

Three things fall out of moving the record:

- **No per-feature MR.** One batched Tier-0 MR carries five closure records, the archive moves, and the status flips due in the same window.
- **Merged spec artifacts stop being edited.** `tasks.md` is written once, on the feature branch, reviewed with the feature. Nothing amends it afterwards, so the post-merge-immutability rules stop firing on routine bookkeeping.
- **One place to read the project's delivery history.** Lane, MR count, and result are on every header line, in one file, in order.

## Header and gates grammar

```
## NNN-<slug> — PASSED <date> · lane <XS|S|M|L> · <n> MR(s) (!iid, …)
## NNN-<slug> — BLOCKED <date> · lane <X> · <n> MR(s) (!iid) — <one-line reason>

gates: lane=<X> budget=<lines>/<limit> tasks.md=<yes|no> status=<Active|…> mrs=<n>/<expected> worktrees=<clean|n left> design=<pass|n/a> copy=<pass|n/a> live=<pass|n/a> ci=<pass|n/a> tier=<0|1|2> gap=<elapsed>/<floor>|n/a
```

**The `NNN-` prefix applies whenever the entry closes a numbered `specs/NNN-<slug>/` feature.** A standalone XS docs/cleanup MR that never went through `/specify` has no feature number to carry, so its header is the bare `<slug>` — e.g. `## offline-manifest-validation — PASSED …`, not `## NNN-offline-manifest-validation`. Do not invent a number to force the prefix; an absent prefix on a non-featured entry is not a defect.

**The `ci`, `tier`, and `gap` fields are mandatory on every entry, not optional additions.** `ci` is `pass`/`n/a` per §4 of the cover list below — `n/a` means checked and genuinely not applicable (no pipeline configured), never "skipped". `tier` is the review tier from `team-lead-coordinator.md`'s tier table (`0`, `1`, or `2`); `gap` is the measured attestation-to-approval-eligible interval against that tier's floor, or `n/a` for Tier 0 (no floor exists). When an entry covers more than one MR at different tiers, key both fields per MR IID rather than picking one: `tiers=!53:0,!54:2 gap=!53:n/a,!54:285.7s/120s`.

**The entry is what makes `/verify` complete** — no entry, no "done." Both lines are fixed. Every `gates:` field is answered explicitly, including `n/a`; an omitted field reads as unchecked, which is the failure this line exists to prevent (→ RP-20). A field that is not passing is a blocker, not a note — resolve it, or record the human's explicit waiver inline (`budget=125/120 waived-by-stakeholder`).

The header never varies. The bullets below it scale with the lane: an XS or S entry may be four lines; an L entry with a live-deploy surface will be longer. State evidence **you derived yourself**, with the identifier you actually ran a command to obtain — never a teammate's self-report, and never an identifier recalled rather than re-derived.

Cover, in this order, omitting only what genuinely does not apply:

1. **Branch-base / merge cleanliness** — the Rule 9 diff of the pre-merge `origin/main` tip against the merge commit, and what it showed.
2. **Attestation** — note id, reviewer instance (and that it differs from *every* instance that committed to the branch), `reviewed-sha` against the merge pin, ordering and elapsed gap for the tier.
3. **Merge** — the SHA-pinned squash commit, source branch deleted.
4. **CI** — pipeline id and result.
5. **Live confirmation** — required whenever the change ships via anything not rebuilt by the same CI run; say who confirmed and what they observed from a clean/uncached client. If not required, say so and why in one clause.
6. **Accepted caveats** — anything waived, who accepted it, and whether it is scoped to this feature or sets a precedent.
7. **Open follow-ups** — or `none`.

## Worked example

```markdown
## 029-signup-copy-round-2 — PASSED 2026-08-24 · lane S · 1 MR (!79)

gates: lane=S budget=112/120 tasks.md=yes status=Active mrs=1/1 worktrees=clean design=pass copy=pass live=pass ci=pass tier=1 gap=142s/15s

- **Branch base / merge cleanliness:** `git diff f5e464d..30c66bf --stat` shows exactly the 7 files in T1–T7's scope. No unrelated content rode along.
- **Attestation:** note `3722231165`, reviewer-instance `engineer-reviewer`, distinct from the only committer `engineer-author`; `reviewed-sha 683efdf4…` equals the SHA the merge was pinned to; posted before approval.
- **Merge:** SHA-pinned squash `30c66bf` on `main`, source branch deleted.
- **CI:** pipeline 2783672056, 9/9 green on `30c66bf3`.
- **Live confirmation:** devops-infra-expert confirmed the cicd manifest bumps for proxy/spa/preview reconciled to `30c66bf3` and ArgoCD synced, then read production uncached — label hidden via `.visually-hidden` with `for`/`id` intact, disclosure line absent, fine print exactly "Unsubscribe anytime — deletes your address."
- **Accepted caveat:** T10's manual screen-reader pass substituted with Chrome accessibility-tree evidence; accepted by team lead, scoped to this MR only (plain label-for association, no custom widget), explicitly not a precedent. Rationale in !79's description.
- **Open follow-ups:** none.
```

That entry is ~9 lines for a lane-S feature. The same content previously cost a branch, an authoring instance, a reviewing instance, an attestation, and a merge — per feature.
