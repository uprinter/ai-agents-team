# SEO improvement lifecycle

Authoritative operating process for `seo-specialist`; technical checks live in
[technical-seo](../../.agents/skills/technical-seo/SKILL.md), with dated
[provider guidance](../../.agents/skills/technical-seo/references/search-and-ai.md).
This replaces the former one-pass audit sequence and artifact prose; the same
stages apply to first audits, focused investigations, and recurring follow-ups.

## Stages and exit evidence

Keep a small stage table in the dated audit: stage, completed/partial/pending/not-due/out-of-scope,
evidence link, next owner/date; a focused request reuses existing evidence and
marks unrelated checks out of scope rather than triggering a full re-audit.
Continue public checks when private tools are unavailable; record the limitation.

| Stage | Work | Exit evidence |
|---|---|---|
| 1. Scope and resume | Read target conventions, ADRs, channel plan if present, and previous SEO artifacts; record domain, audience, locales, business conversion, priority search/AI surfaces and bounds | Scope, assumptions, access inventory, current finding IDs, due work |
| 2. Baseline | Capture available search, traffic/conversion, index coverage, field-performance and AI evidence before changes; refresh relevant official guidance | Source/date/filter/window/sample for each metric, missing data explicitly unknown |
| 3. Audit and research | Sample crawler surface using the skill; assess user intent, content usefulness, citation readiness and legitimate distribution opportunities | Reproducible observations, affected URLs/templates, source-backed guidance and hypotheses separated |
| 4. Prioritize | Rank by business impact/reach, urgency, effort, risk and confidence; distinguish blockers from growth experiments | Stable findings, proposed first batch, acceptance checks, owners and measurement plan |
| 5. Hand off | Send requested/selected work as behavior and evidence to normal delivery intake; keep independent findings in backlog | Finding → issue/spec/MR reference or pending selection; no implementation or unsolicited expansion |
| 6. Verify delivery | On shipped work, recheck actual production behavior and affected controls; connect result to release SHA/date | Technical pass/fail/unknown, regressions and remaining owner; retain awaiting measurement state |
| 7. Measure and iterate | Compare due readings against baseline with matching filters/windows; decide retain, revise, revert proposal or inconclusive | Observations, confounders, decision, next review date and scope |

An audit session can finish with stages 5–7 pending/not-due; report who owns the
next action and when it is due, without pretending implementation or growth happened.
Use the same finding IDs on later runs; do not recommend pending work again as new.

## Baseline and sampling

- Start with homepage, primary conversion/intent pages, one URL per relevant
  template/locale, changed URLs, duplicates/redirects and known missing paths;
  record sample size/selection, and expand only to establish a finding's reach.
- Prefer available read-only Search Console/Bing/analytics data over estimates;
  for the repo's GSC helper use the absolute config-repo path and inspect its usage.
  Distinguish indexed inspection results from live fetch tests; `site:` queries
  alone do not establish index coverage or absence.
- Search baseline: page/query, branded versus nonbranded, country/device, clicks,
  impressions, CTR, average position and business conversions where available;
  retain filters, window, extraction date, property scope and privacy omissions.
- Use a comparable 28-day window by default when enough history exists; adapt to
  volume and seasonality rather than manufacture statistics for a new site.
  Performance uses field p75 with URL/origin and device scope; lab metrics stay separate.
- For AI monitoring choose a bounded, versioned panel (default 10–20 relevant
  questions across priority intents); record exact question, surface/model if shown,
  date/time, locale, search mode, session conditions and response evidence.
  Sample neutral questions without seeding the product's name/URL, keeping branded
  prompts separate; repeat under consistent conditions, recording all runs, not
  only favorable ones, and keep changed panels separate from historical comparisons.
- Record per run: linked citation URL, accurate/unlinked brand mention, absence,
  refusal or unavailable result; summarize citation rate with its denominator and
  sample size, never as population-wide share of voice or a stable LLM rank.
  A URL-paste retrieval test proves a different capability from spontaneous discovery.
- Read Bing AI Performance when available and preserve its scope/definitions;
  separate that from prompt samples and AI referral conversions, and do not invent
  Google AI feature filters or imply every AI impression creates a referral.
  Read Google's dedicated Generative AI performance report when available (see
  current reference), preserving its actual impression dimensions and missingness;
  inspect effective Search generative AI inclusion and inherited settings read-only.
  Record unavailable access, and check known reporting anomalies before attributing
  changes; never assume the existing GSC helper supports this newer report.

## Content and distribution research

Map query clusters and natural-language questions to intent and current/proposed
pages; inspect real search results in the target language/location and identify
useful competing page types, sources cited by AI when observable, and missing facts.
Multiple queries can belong to one useful page; overlapping queries do not alone
justify merging distinct intents, and low volume/strong incumbents are not automatic rejection.

Recommend content the product can substantiate: direct answers in context,
original examples/data with methods and dates, sourced factual claims, descriptive
sections, comparison criteria, clear authorship/organization/contact details, and
honest limitations; do not invent expertise, users, reviews, measurements or freshness.
Treat answer-first formatting, passages that stand alone and tables as usability
and retrieval hypotheses unless a provider explicitly documents the claimed effect.

Check topical gaps, internal linking and accurate entity identity; use relevant
Organization/Product/etc. markup only where truthful and eligible, and check local
profiles or merchant feeds only for applicable businesses.
Avoid mass-produced doorway/location/question pages and purchased authority;
identify credible directories, editorial citations or partnerships with relevance
and an honest contribution.

## Evidence and priority

A finding separates **observation** (`[measured]` command/tool output, timestamp,
URL and environment), **guidance** (`[documented]` official URL/access date), and
**expected effect** (`[inferred]` unless actually demonstrated); several can coexist.
A documented practice is not proof this site violates it or that applying it raises
rankings; an inferred impact cannot be converted into a ranking-factor claim.

Rank business-relevant blockers first (unintended deindexing, inaccessible key pages),
then supported improvements, then bounded experiments; use evidence confidence as
an input rather than automatically prioritizing a trivial documented issue over a
large but uncertain opportunity, and label effort as an estimate.
Every selected finding needs observable acceptance criteria, a metric and baseline
(or explicitly unavailable), a follow-up trigger/date, and rollback considerations
for visibility controls; no finding is ready for handoff without this checklist.

## Persistent artifact contract

All files live in the **target project's** `docs/venture/seo/`; do not create site
execution artifacts in this configuration repo or duplicate data across reports.
Use concise tables and evidence excerpts/links, redacting credentials and personal
query data; retain historical evidence rather than overwriting previous conclusions.

### `audit-YYYY-MM-DD.md`

Include scope/stage table, access limits, source verification dates, URL sample,
provider-purpose matrix, ranked findings, decisions and handoff/follow-up summary;
append another same-day run with a timestamp, rather than replacing history.
Each finding uses this record (table or short subsections):

```text
ID: SEO-001 (retain across audits)
State: proposed | selected | handed-off | shipped-awaiting-verification |
       awaiting-measurement | validated | inconclusive | rejected | superseded
Surface / affected URLs / user intent:
Observation + evidence + date/environment:
Official guidance + source/access date:
Expected effect + evidence class/confidence:
Impact / reach / urgency / effort / risk:
Required behavior + acceptance checks:
Owner / dependency / issue-spec-MR / release SHA and date:
Metric / baseline and filters / success criterion:
Follow-up date or trigger / rollback considerations:
Decision and rationale / supersedes ID (if any):
```

### `keyword-map.md`

Maintain: cluster ID, queries/questions, language/market, intent, business relevance,
observed search result types/source/date, AI cited sources if sampled, current or
proposed owner URL, gap and next action; merge/consolidate only with intent evidence.

### `measurement-log.md`

Append: finding ID, release SHA/date, metric/source, scope/filters/device/window,
baseline with extraction date, current reading with date/sample size, delta where
comparable, confounders, decision, owner and next review date.
Do not backfill an invented baseline; mark unrecoverable history unavailable.

### `ai-visibility-log.md` (when AI discovery is in scope)

Maintain the versioned question panel and append per-run evidence/conditions,
linked citation versus mention versus absence, cited URLs and factual accuracy;
keep provider report metrics and referrals/conversions in labelled separate tables
or link to their rows in the measurement log to avoid duplication.

## Cadence and closure gates

Use risk/data-driven dates: technical verification immediately after deployment,
crawl/index checks typically after days to two weeks, and outcome review typically
4–12 weeks with adequate data; these are planning defaults, not engine SLAs.
Do not wait to investigate a regression, or declare failure because a low-traffic
site has no measurable lift after a few days; mark inconclusive and set the next check.

At session close verify: requested stages addressed, observations sourced, unknowns
explicit, stable IDs updated, no pending work duplicated, selection/handoff state
accurate, next owner/date recorded, and no unauthorized production writes.
Commit the requested docs on a topic branch under target conventions; main remains
MR-only with the repository's Tier-0 documentation review, not a five-role build
ceremony, and report branch/commit/MR status without claiming unperformed operations.
