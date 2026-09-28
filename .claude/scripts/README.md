# gsc.mjs — Google Search Console CLI

Read-only, dependency-free Node CLI for the `seo-specialist` agent's `Bash` tool.
It signs its own service-account JWT and talks to the Search Console REST APIs
directly with `fetch` — no `googleapis`, no `package.json`. It requests only the
`webmasters.readonly` scope, so no subcommand can change a live property.

## One-time setup (Google Cloud + Search Console)

1. **Create (or select) a Google Cloud project**, then **enable the API**:
   Google Cloud Console → *APIs & Services* → *Library* → search "**Google
   Search Console API**" → *Enable*. This one product covers all four
   subcommands here — `sites`/`query`/`sitemaps` (`www.googleapis.com/webmasters/v3`)
   and `inspect` (`searchconsole.googleapis.com`) are the same API under two
   REST paths, not two products, so there is nothing further to enable for
   `inspect`. Skipping this step is the single most common failure: every
   call fails with `SERVICE_DISABLED` until it's done, even with a
   perfectly correct key and property permissions.
2. **Create a service account** in that project:
   Google Cloud Console → *IAM & Admin* → *Service Accounts* → *Create Service Account*.
   No IAM roles need to be granted on the project — Search Console access is
   granted separately, in step 4.
3. **Create and download a JSON key** for that service account: open the
   service account → *Keys* tab → *Add Key* → *Create new key* → type **JSON**.
   Save it somewhere outside any git repo, e.g. `~/.gcp/service-account.json`.
4. **Add the service account as a user on the property** in
   [Search Console](https://search.google.com/search-console): open the
   property → *Settings* → *Users and permissions* → *Add user* → paste the
   service account's `client_email` (from the JSON key) → permission level
   **Restricted** is sufficient, since this tool never writes anything.
5. **Set the environment variable** to the key's path:
   ```sh
   export GSC_SERVICE_ACCOUNT_KEY=~/.gcp/service-account.json
   ```
   Put this in `~/.zshenv`, not `~/.zshrc` and not any project repo.
   `.zshrc` only loads in interactive shells, so an export placed there is
   invisible to a non-interactive Bash tool call — exactly the failure mode
   an agent invoking this script hits. `~/.zshenv` loads for every shell,
   interactive or not. The key file itself must never be committed.

Verify with the auth smoke test:

```sh
node .claude/scripts/gsc.mjs sites
```

## Subcommands

### `sites` — list verified properties

```sh
node .claude/scripts/gsc.mjs sites
```

### `query` — Search Analytics (clicks/impressions/ctr/position)

```sh
node .claude/scripts/gsc.mjs query sc-domain:example.com \
  --dim query,page --start 2026-07-01 --end 2026-08-01 --limit 50 \
  --filter page~~/stars
```

Every run prints a header first — property, resolved `start..end`, dimensions,
filters, row count — before the table, so a pasted result is self-contained
evidence in a measurement log even without `--json`. Google's own response
never echoes back what was asked, which is why the header is built from the
resolved request rather than read out of the response.

`--filter <dimension><op><expression>` is repeatable (ANDed). Dimensions:
`country`, `device`, `page`, `query`, `searchAppearance`. Operators:
`==` equals, `!=` notEquals, `~~` contains, `!~` notContains, `=~` includingRegex,
`!=~` excludingRegex.

**The property-totals probe** — `--dim ""` (an empty `--dim` value) — is the
cheapest way to check "is there any data at all for this property in this
window," before drilling into any one dimension:

```sh
node .claude/scripts/gsc.mjs query sc-domain:example.com --dim ""
```

It returns a single row with no breakdown if there is any data at all, and no
`rows` key whatsoever if the property is genuinely empty for the window — the
distinction a thin per-dimension slice can't make on its own, since a filtered
or narrow query returning nothing looks identical to genuine zero data.

`--json` on `query` emits `{request, response}` rather than a bare response:
`response` is the raw Search Analytics API response, and `request` echoes the
resolved `siteUrl`/dates/dimensions/filters/type that produced it — needed
because the API response carries none of that itself. Every other
subcommand's `--json` is the unwrapped raw response, since their inputs are
already fully stated on the command line with nothing resolved silently.

### `sitemaps` — submitted sitemaps and their indexed counts

```sh
node .claude/scripts/gsc.mjs sitemaps sc-domain:example.com
```

### `inspect` — live URL Inspection for one page

```sh
node .claude/scripts/gsc.mjs inspect sc-domain:example.com https://example.com/page
```

Prints `inspectionResultLink` first — the click-through to the same verdict in
the Search Console UI, for handing off to the stakeholder — then only the index
status fields Google actually returned. An unknown-or-uninspected URL (common
for a new or empty property) has most of them absent; they're omitted rather
than printed as `-` noise.

## Flags common to every subcommand

- `--json` — emit the raw API response instead of the compact table, for when
  the agent needs a field the table omits.
- `--help` — usage for every subcommand and flag.

`siteUrl` is either a domain property (`sc-domain:example.com`) or a
URL-prefix property (`https://example.com/`), exactly as it reads in Search
Console — the CLI URL-encodes it for you.
