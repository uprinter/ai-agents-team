# Harness quality loop

This process makes three transitions in the delivery harness explicit: how every acceptance criterion will be checked, how M/L assumptions are challenged before implementation, and how failed gates become measured feedback. It adds no extra challenge round to XS or S work.

## 1. Acceptance-criterion validation map

Before `/implement`, `tasks.md` contains one row for every acceptance criterion in the governing spec:

| AC | Method | Stage | Evidence | Owner |
|---|---|---|---|---|
| `AC-n.n` | the concrete check | `CI`, `review`, or `live` | the exact artifact or result to retain | the role that produces it |

Rules:

- Map every AC, including criteria without `[MUST-TEST]`. XS work with no spec or ACs records the gate as `n/a` in its task row.
- A `[MUST-TEST]` criterion names the automated test and CI job. Other valid methods include a rendered screenshot set, an exact command and expected output, a live probe, a query result, or a named manual review dimension; `review` or `verify manually` alone is too vague.
- `Stage` says when the evidence exists: `CI` before merge, `review` on the MR, or `live` after deployment. `Evidence` says where a later verifier can find it, such as a test path plus job, an MR note or upload, or captured command output.
- `/tasks` blocks implementation while a criterion lacks any field or while its method could pass on the known-broken behavior. `/verify` follows the map and blocks when the promised evidence is missing or does not demonstrate the criterion.

The map is a routing table, not a second specification. It does not restate the AC or add requirements.

## 2. One bounded assumption challenge for M/L

Lane M and L governing documents receive one independent assumption challenge during their existing governing-document MR review. Application work uses a `code-reviewer`; IaC or manifest work uses a second `devops-infra-expert`; the reviewer must be distinct from every spec or plan committer.

The challenge asks only:

1. Which material assumption is unsupported by the supplied evidence?
2. Which failure case could make an AC pass while the requested outcome still fails?
3. Does the proposed work still trace to the verbatim request recorded at intake?

The reviewer posts one MR note before attestation:

```text
ASSUMPTION-CHALLENGE
reviewer-instance: <spawn name / task id>
request-ref: <location of the unchanged verbatim request>
findings: <none with checked evidence, or one line per finding>
disposition: <resolved | accepted with owner and reason | blocking>
```

The note appends findings separately and never rewrites, summarizes, or replaces the recorded request. Findings outside the request remain findings under coordinator Rule 16; unresolved in-scope findings block the governing-document merge and therefore block implementation.

This is one bounded review, folded into the already-required independent review of the governing-document MR. Do not create another review round, MR, or artifact for it, and do not run it for XS or S.

## 3. Failed-gate feedback record

When a `/tasks`, review, or `/verify` gate fails, append one compact row to the current run's `${CLAUDE_PLUGIN_ROOT}/.claude/collaboration-traces/<date>-<topic>/postmortem.md` under `## Harness failures`; create that run-level postmortem only if none exists. Use one postmortem for the run, not one file per failure.

| Failure / repeat key | Introduced | Detected | Correction cost | Candidate preventive check | Disposition |
|---|---|---|---|---|---|
| `<feature/MR> · <stable class>` | stage or commit | gate and evidence | measured elapsed time; if unavailable, review rounds or commits | executable check, instruction change, or `none` | adopted, deferred, or rejected with reason |

Do not invent correction time. Use observed elapsed time when available and otherwise name the closest measured proxy.

Before adding a durable role rule, search prior postmortems for the repeat key and cite the matches in the rule proposal. Prefer an executable check for a repeated deterministic failure, a clearer instruction for a repeated judgment failure, and no harness change when the record does not show recurrence or useful prevention; a single high-impact exception must state why waiting for recurrence is unacceptable.

The process-MR reviewer checks that every new rule names the record reviewed, what it replaces or generalizes, and its enforcement point. `rule-provenance.md` remains the narrative for rules that are adopted; the compact rows also preserve candidates that were rejected, so the team does not repeatedly debate the same unsuccessful control.
