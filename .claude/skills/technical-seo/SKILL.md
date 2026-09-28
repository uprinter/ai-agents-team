---
name: technical-seo
description: Implement and review crawlability, indexing, and retrieval for Google, Bing, and AI search. Use for head metadata, robots.txt, sitemaps, canonicals, redirects, status codes, structured data, SSR/prerendering, internal links, crawler access through CDNs/WAFs, or technical AI visibility/GEO/AEO work. Covers search versus training bot controls and verification evidence. Keyword research, content strategy, citation monitoring, and the ongoing SEO lifecycle belong to seo-specialist.
---

# Technical SEO and AI retrieval

Check what a crawler can fetch, render, and interpret, then verify affected URLs.
Crawl access, indexing, retrieval, citation, and conversion are separate outcomes;
passing one does not guarantee the next.

## Use and sources

Read [current sources and crawler policy](references/search-and-ai.md) for AI access
work or disputed platform behavior; refresh relevant official pages before
recommending controls, supported schema, or measurement features.
The reference is a dated starting point, not a permanently current bot allowlist.
For full audits/follow-ups, `seo-specialist` follows
[the SEO lifecycle](../../../.claude/process/seo-lifecycle.md); this skill supplies
the implementation/review checklist, not permission to broaden a code change.

## Classify the diff

Apply the crawler-surface review gate when a diff changes head tags, HTTP headers,
robots or sitemaps, URLs/routing, rendering, structured data, crawlable links,
heading semantics, image alternatives, or CDN/WAF/bot controls.
Classify by effect, even if the task was described as visual or infrastructural.

## Checklist

### 1. Fetch and discover

- Sample affected templates, important landing pages, redirects, duplicates,
  and nonexistent paths; record GET status, headers, final URL, and redirect hops.
  Missing pages return 404/410; maintenance uses appropriate temporary errors,
  not a success page; do not redirect unrelated deleted URLs to the homepage.
- Prevent SPA fallbacks from swallowing crawl files and nonexistent routes;
  missing assets must not become HTML app shells.
- Fetch `/robots.txt` for relevant origins: it belongs at each origin's root,
  should be UTF-8 plain text when provided, and must parse as directives.
  An absent robots file is not automatically a defect; assess actual HTTP status,
  valid rules, and provider behavior rather than assuming HTML blocks all bots.
- Discover actual sitemap locations from robots, configuration, or webmaster tools;
  `/sitemap.xml` is a convention, not a mandatory root path.
  Check parseability, correct serving, canonical indexable URLs, accurate
  significant-change `lastmod`, size limits, and child sitemap coverage;
  accepted formats/content types vary, so do not fail solely on `text/xml`.
- Check real `<a href>` links, descriptive anchors, orphan pages, pagination,
  filters/parameters and crawl traps; protect private data with authentication,
  since robots directives are not access control.

### 2. Index and consolidate

- Evaluate matching robots groups per bot and path, not just `User-agent: *`;
  crawl blocking does not reliably remove an indexed URL and can prevent a bot
  seeing `noindex` or a canonical.
- Read HTML robots tags AND `X-Robots-Tag`, including on PDFs/non-HTML resources;
  distinguish indexing controls from snippet/preview controls.
- Align redirects, internal links, sitemap URLs, and canonicals around the intended
  preferred URL; canonical annotations are signals, not guaranteed directives.
  Prefer absolute canonicals on indexable HTML, check HTTP-header canonicals for
  non-HTML files, and avoid conflicts or non-indexable targets.
- Consolidate genuine duplicates, not pages merely sharing query words;
  distinct intents/languages can merit distinct pages.
  Check reciprocal/self `hreflang`, reachable locale URLs and appropriate
  canonicals; do not canonicalize all translations to English.

### 3. Render and represent honestly

- Compare initial HTML with rendered mobile/desktop DOM: meaningful text, headings,
  links, canonicals, robots tags and schema; report specific missing content.
  Google can render JavaScript, but one browser's success does not establish
  retrieval by every search or AI provider.
- Prefer important public content/navigation in initial HTML for broad retrieval
  reliability, with equivalent substantive content for people and crawlers;
  SSR/static generation is a project choice, not a universal ranking requirement.
- Preserve ADR boundaries around social-unfurl user-agent branches: do not extend
  them to search bots; prefer rendering for everyone as team policy.
  Google does not classify equivalent-content dynamic rendering as cloaking, but
  discourages this complex workaround; deceptive crawler-only content is prohibited.
- Verify mobile content parity and that essential text does not require a click
  or interaction-triggered network load; an accessible accordion whose text is
  already rendered is not automatically an indexing defect.
- Write distinctive, descriptive titles and useful page-specific descriptions;
  60/155 characters are preview heuristics, not limits or ranking requirements,
  and search engines may rewrite both.
- Use meaningful headings and accurate image alternatives; avoid keyword stuffing
  and do not manufacture FAQ blocks to target more query variants.
- Validate structured data syntax AND current provider feature eligibility;
  claims must match visible, accurate content and the running product.
  Rich results are not guaranteed, schema is not an AI citation shortcut, and
  Open Graph/Twitter previews are separate from search eligibility.

### 4. Check AI access separately

- Build the provider/purpose matrix from the reference: search indexing, user
  retrieval, and training are distinct; preserve the owner's training preference
  when improving search access, and mark unknown preferences for decision.
- Check robots, CDN/WAF policy, challenge pages, rate limits, and origin responses;
  HTTP 200 can still contain a challenge or empty shell.
  A synthetic user-agent request is diagnostic, not proof the actual provider
  can fetch: use verified bot logs or provider inspection where available.
- Use current provider-published verification methods/IP feeds where applicable;
  never treat a claimed user-agent alone as permission to bypass security.
  Scope proposed exceptions to verified providers and public resources.
- Assess `noindex`, `nosnippet`, `max-snippet`, and `data-nosnippet` against each
  provider's rules and the owner's publishing choices; do not blindly remove them.
  For Google AI eligibility also inspect the effective Search Console Search
  generative AI control and parent inheritance when read access is available;
  this is separate from Google-Extended and ordinary Search inclusion.
- Do not require `llms.txt`, AI-only pages, hidden instructions to assistants, or
  special AI schema; optional machine-readable exports need a specific documented
  consumer or a bounded experiment with a measurable benefit.
- Consider IndexNow for changed public URLs on participating engines when useful;
  it is notification, not guaranteed indexing, ranking, or Google submission.

### 5. Measure experience correctly

Use field data (CrUX/PageSpeed Insights or site RUM) for Core Web Vitals, labelled
with device, URL versus origin scope, period, and sample availability; good p75
thresholds are LCP ≤2.5s, INP ≤200ms, CLS ≤0.1.
Use Lighthouse/DevTools traces to diagnose lab behavior, not claim a field pass;
a page-load trace alone cannot establish INP for real users, and missing field
data means unknown rather than zero or passing.

## Verification evidence before review

Use GET (HEAD can behave differently), bounded timeouts, and retain headers/body;
record initial status before following redirects, for example:

```sh
curl -sS --max-time 30 -D /tmp/seo-headers.txt -o /tmp/seo-body.html 'https://example.com/page'
curl -sS --max-time 30 -L --max-redirs 5 -o /dev/null -w '%{http_code} %{url_effective} %{num_redirects}\n' 'https://example.com/page'
```

Substitute an actual public URL; parse full HTML/XML/JSON rather than treating a
regex match as validation, compare rendered mobile content, and test changed paths.
Label local/staging evidence accurately: production access/indexing remains
unverified until checked there; `site:` searches cannot prove full index coverage.

## Reviewer gate

In `REVIEW-ATTESTATION`, record checklist sections, sampled URLs/environment,
commands/tools and observed results, expected behavior, pass/fail/unknown, and
remaining production verification owner; AI controls also need the before/after
provider-purpose policy and evidence for edge access.
A browser screenshot or Lighthouse SEO score alone cannot pass this dimension;
implementation success is not a claim of ranking or citation improvement.
