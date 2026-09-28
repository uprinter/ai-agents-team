# Search and AI discovery reference

Last verified: **2026-09-06**. Refresh the official pages relevant to each engagement;
record access dates and changed guidance in the audit, and label unavailable sources
as unverified rather than presenting cached advice as current.

## Provider and purpose matrix

This is a starting inventory, not a robots.txt template; evaluate existing groups,
public/private paths, publishing preferences, and edge policy before proposing changes.

| Surface | Search/retrieval | Training or other control | Official reference |
|---|---|---|---|
| Google Search, AI Overviews, AI Mode | Googlebot, indexing/snippet eligibility, plus the Search Console Search generative AI inclusion control | Google-Extended does not control inclusion/ranking in Google Search | [AI features](https://developers.google.com/search/docs/appearance/ai-features) |
| Gemini Apps / applicable Vertex AI uses | Grounding may be governed by Google-Extended | Google-Extended covers specified Gemini training AND grounding uses; not a standalone HTTP user-agent | [Google crawler documentation](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers#google-extended) |
| Bing / Copilot | Bingbot and Bing indexing; check current preview directives for each use | Do not assume Google's controls apply to Microsoft | [Bing guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) |
| ChatGPT search | OAI-SearchBot; ChatGPT-User serves user-triggered fetches, not automated search indexing | GPTBot is a separate training preference | [OpenAI bots](https://developers.openai.com/api/docs/bots) |
| Claude search | Claude-SearchBot; Claude-User retrieves for user requests | ClaudeBot concerns model development/training | [Anthropic bots](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) |
| Perplexity | PerplexityBot supports search; Perplexity-User supports requested retrieval | These are not foundation-model training crawlers | [Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) |

OpenAI documents independent search/training settings; blocking OAI-SearchBot can
exclude content from search answers while navigational links may still appear.
User-requested fetchers do not necessarily follow automated-crawl rules: OpenAI
says robots rules may not apply to ChatGPT-User, Perplexity says its user fetcher
generally ignores them, while Anthropic documents robots controls for Claude-User.
Verify provider-specific behavior; robots.txt is never a confidentiality barrier.

Record one row per provider/purpose with desired policy, effective robots rule,
edge result, evidence date, and verified/unknown state; preserve training opt-outs.
A robots allow rule does not override a WAF challenge, prove indexing, or establish
that a future answer will cite the site; never infer training inclusion from access.

## Practices and corrections

| Topic | Practical rule | Source |
|---|---|---|
| Google AI eligibility | Ordinary search foundations apply; no required AI text file or special schema | [AI features](https://developers.google.com/search/docs/appearance/ai-features) |
| Robots | Crawl control differs from indexing/removal and authentication | [Robots introduction](https://developers.google.com/search/docs/crawling-indexing/robots/intro), [parsing/status rules](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec) |
| Sitemaps | Discover actual location; valid canonical URLs, truthful update dates; submission is a hint | [Sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) |
| Canonicals | Align signals; engines may choose a different canonical | [Canonicalization](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) |
| Rendering | Similar-content dynamic rendering is not automatically cloaking, but is discouraged; this team prefers rendering for everyone | [Dynamic rendering](https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering) |
| Mobile | Preserve substantive content; accordions/tabs are compatible with mobile-first indexing | [Mobile-first guidance](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing) |
| Search copy | No hard title/description character limits; truncation and rewriting vary | [Titles](https://developers.google.com/search/docs/appearance/title-link), [snippets](https://developers.google.com/search/docs/appearance/snippet) |
| Structured data | Visible truthful claims, valid syntax and supported feature eligibility are separate checks | [Structured data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) |
| Field performance | Assess LCP/INP/CLS at p75 with device and reporting scope; lab results diagnose | [Web Vitals](https://web.dev/articles/vitals) |
| Useful content | Original evidence, demonstrated experience, clear sourcing and ownership; no word-count or E-E-A-T score target | [People-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) |
| Abuse | No scaled low-value pages, link schemes, doorway content, fabricated evidence, or instructions intended to manipulate AI answers | [Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies), [Bing guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) |
| Freshness notification | Consider IndexNow for additions/updates/deletions on participating engines; accepted submission is not indexed status | [IndexNow protocol](https://www.indexnow.org/documentation) |

## Recent changes that supersede older summaries

Google's [Search generative AI control](https://support.google.com/webmasters/answer/16908024?hl=en)
adds property-level inclusion/exclusion, including inherited parent settings;
inspect the effective setting read-only, alongside robots/snippet controls.
It is separate from ordinary Search ranking/inclusion and training permissions;
a change is a live visibility action needing exact-content approval, not a default
audit step, and an unknown setting must not be assumed enabled.

Google's [Generative AI performance report](https://support.google.com/webmasters/answer/16984139?hl=en)
now reports AI Overviews/AI Mode impressions; the documentation announces global
rollout on August 31, 2026, while access/data may still be absent for a property.
Inspect actual availability and preserve page/country/device/date scope, aggregation,
Pacific Time reporting and preliminary-data status; do not invent clicks, queries,
CTR, position or separate feature breakdowns the report does not supply.
Exports can turn unavailable values into zeros, so retain missingness from the UI;
do not assume the existing GSC helper/API exposes this report.

Check [Search Console data anomalies](https://support.google.com/webmasters/answer/6211453?hl=en)
before attributing trend changes; this page also records that Google FAQ rich
results stopped appearing from May 7, 2026, so do not propose FAQ markup for that
benefit (useful visible FAQs can still serve readers).
These newer help pages qualify the older AI-features guide; preserve the newer
specific behavior rather than treating one overview as complete forever.

## Measurement limits

- Google AI data remains part of overall Web reporting as well as its dedicated
  report; do not add the two together or invent an unsupported dimension.
- Bing's AI Performance report exposes citations on its supported experiences;
  capture availability, date range and metric definitions, not universal LLM rank.
  See [report documentation](https://www.bing.com/webmasters/help/ai-performance-9f8e7d6c)
  and [launch explanation](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview).
- Observed AI referrals/conversions, visible citations, unlinked mentions, bot visits,
  and manual prompt samples measure different things; keep them separate.
  Missing referrers, sampling, personalization and model changes limit attribution.
- `llms.txt` can serve particular documentation consumers, but is not a universal
  discovery standard or proven citation/ranking boost; special formats, answer-first
  sections and tables need user value, not claims of a guaranteed AI ranking factor.

## Maintenance rule

Before each audit, recheck platform controls, bots, spam policies, schema eligibility,
and reporting features used in recommendations; update this reference when material
facts change, with the official URL and verification date.
Retain useful stable principles, and document uncertainty instead of chasing every
new SEO/GEO label; no practice guarantees placement in search or LLM responses.
