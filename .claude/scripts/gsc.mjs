#!/usr/bin/env node
// gsc.mjs — read-only Google Search Console CLI, built for the seo-specialist agent's
// Bash tool. Zero dependencies: Node standard library only (native fetch, node:crypto).
//
// Signs its own service-account JWT (RS256) and exchanges it at Google's OAuth token
// endpoint via the jwt-bearer grant, then calls the Search Console API v3 (sites,
// searchAnalytics, sitemaps) and the separate urlInspection v1 API directly with fetch.
// No googleapis, no jsonwebtoken, no package.json.
//
// Requests ONLY the webmasters.readonly scope. No subcommand here can mutate a
// property — no sitemap submission, no URL removal, no settings change. That is
// intentional: the seo-specialist agent is forbidden from altering live search-
// visibility controls, and this tool makes that structurally true rather than a
// policy that could be forgotten.
//
// Reads the service-account key path from GSC_SERVICE_ACCOUNT_KEY (a filesystem path,
// ~ expanded). The key file, its private key, and the access token it produces are
// never written to disk or printed. See README.md for one-time setup.
//
// Verified against Google's current REST reference (2026-08-30):
//   https://developers.google.com/webmaster-tools/v1/sites/list
//   https://developers.google.com/webmaster-tools/v1/searchanalytics/query
//   https://developers.google.com/webmaster-tools/v1/sitemaps/list
//   https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
//   https://developers.google.com/webmaster-tools/v1/urlInspection.index/UrlInspectionResult
//
// CLI:
//   gsc.mjs sites [--json]
//   gsc.mjs query <siteUrl> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--dim query,page,...]
//                            [--limit 25] [--type web|image|video|news|discover|googleNews]
//                            [--filter <dimension><op><expression>]... [--json]
//   gsc.mjs sitemaps <siteUrl> [--json]
//   gsc.mjs inspect <siteUrl> <pageUrl> [--language-code en] [--json]

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';

const SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly';
const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const WEBMASTERS_BASE = 'https://www.googleapis.com/webmasters/v3';
const INSPECTION_URL = 'https://searchconsole.googleapis.com/v1/urlInspection/index:inspect';

const FILTER_DIMENSIONS = ['country', 'device', 'page', 'query', 'searchAppearance'];
// Checked longest-token-first so "!=~" isn't swallowed by "!=" or "=~".
const FILTER_OPS = [
  ['!=~', 'excludingRegex'],
  ['=~', 'includingRegex'],
  ['!=', 'notEquals'],
  ['==', 'equals'],
  ['!~', 'notContains'],
  ['~~', 'contains'],
];

const USAGE = `gsc.mjs — read-only Google Search Console CLI

Usage:
  gsc.mjs sites [--json]
      List verified properties and permission level. Also the auth smoke test.

  gsc.mjs query <siteUrl> [options]
      Query Search Analytics (clicks/impressions/ctr/position by dimension).
      Every run prints a header stating what was actually measured (site,
      resolved start..end, dimensions, filters, row count) before the table —
      the window is computed silently otherwise, and a bare result is not
      usable as logged evidence without it.
      --start YYYY-MM-DD     default: 28 days ending 3 days ago (GSC data lags)
      --end YYYY-MM-DD
      --dim query,page,...   comma-separated dimensions (default: query)
                             valid: query,page,country,device,date,searchAppearance
                             pass --dim "" for the property-TOTALS PROBE: a
                             single row with no breakdown, the cheapest way to
                             check "is there any data at all" for this window —
                             a genuinely empty property returns no rows even
                             from this probe, which a thin per-dimension slice
                             cannot prove on its own.
      --limit N              default: 25 (API max 25000)
      --type web|image|video|news|discover|googleNews
      --filter <dim><op><expr>   repeatable, ANDed together
                             dims: ${FILTER_DIMENSIONS.join(', ')}
                             ops:  ${FILTER_OPS.map(([t, n]) => `${t} (${n})`).join(', ')}
                             example: --filter page~~/stars
      --json                 emit {request, response}: response is the raw API
                             response (Google's own response never echoes back
                             what was asked), request is the resolved dates/
                             dimensions/filters/type that produced it

  gsc.mjs sitemaps <siteUrl> [--json]
      List submitted sitemaps: last download, warnings/errors, indexed counts.

  gsc.mjs inspect <siteUrl> <pageUrl> [--language-code en] [--json]
      Live URL Inspection: index/coverage status, canonical, last crawl,
      mobile usability, rich-results verdicts.

  gsc.mjs --help

siteUrl is either a domain property ("sc-domain:example.com") or a URL-prefix
property ("https://example.com/") exactly as it appears in Search Console.

Auth: set GSC_SERVICE_ACCOUNT_KEY to the path of a service-account JSON key
that has been added as a user on the property in Search Console. See README.md.
`;

function expandHome(p) {
  if (p.startsWith('~')) return path.join(os.homedir(), p.slice(1));
  return p;
}

function readServiceAccountKey() {
  const keyPath = process.env.GSC_SERVICE_ACCOUNT_KEY;
  if (!keyPath || !keyPath.trim()) {
    throw new Error(
      'GSC_SERVICE_ACCOUNT_KEY is not set. Point it at your service-account JSON key file, ' +
        'e.g. export GSC_SERVICE_ACCOUNT_KEY=~/.gcp/service-account.json — see ' +
        '.claude/scripts/README.md for one-time setup.'
    );
  }
  const resolved = expandHome(keyPath.trim());
  if (!fs.existsSync(resolved)) {
    throw new Error(
      `GSC_SERVICE_ACCOUNT_KEY points at "${resolved}", which does not exist. See ` +
        '.claude/scripts/README.md for one-time setup.'
    );
  }
  let json;
  try {
    json = JSON.parse(fs.readFileSync(resolved, 'utf8'));
  } catch (err) {
    throw new Error(`Failed to parse service-account key at ${resolved}: ${err.message}`);
  }
  if (!json.client_email || !json.private_key) {
    throw new Error(`Service-account key at ${resolved} is missing client_email or private_key.`);
  }
  return json;
}

function base64url(buf) {
  return Buffer.from(buf).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function signJwt(key) {
  const header = { alg: 'RS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const claims = {
    iss: key.client_email,
    scope: SCOPE,
    aud: TOKEN_URL,
    iat: now,
    exp: now + 3600,
  };
  const signingInput = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(claims))}`;
  const signature = crypto.createSign('RSA-SHA256').update(signingInput).sign(key.private_key);
  return `${signingInput}.${base64url(signature)}`;
}

function formatApiError(status, bodyText, context) {
  let message = bodyText;
  let serviceDisabled = false;
  try {
    const json = JSON.parse(bodyText);
    if (json.error && typeof json.error === 'object') {
      message = json.error.message || JSON.stringify(json.error);
      const details = Array.isArray(json.error.details) ? json.error.details : [];
      serviceDisabled =
        details.some((d) => d.reason === 'SERVICE_DISABLED') ||
        /has not been used in project|it is disabled/i.test(message);
    } else if (json.error_description) {
      message = json.error_description;
    }
  } catch {
    // not JSON — use the raw body as-is
  }
  const lines = [`${context} failed: HTTP ${status} — ${message}`];
  if (status === 403 && serviceDisabled) {
    lines.push(
      'This means the Google Search Console API is not enabled in the Google Cloud project the ' +
        'service account belongs to (a one-time setup step, separate from Search Console property ' +
        'access). Enable it: Google Cloud Console > APIs & Services > Library > search "Google ' +
        'Search Console API" > Enable. See .claude/scripts/README.md.'
    );
  } else if (status === 403) {
    lines.push(
      'A 403 here is often a siteUrl mismatch rather than a missing grant: a domain property ' +
        '("sc-domain:example.com") and a URL-prefix property ("https://example.com/") are not ' +
        'interchangeable, and a service account granted on one gets a 403 on the other even for the ' +
        'same site. Run `gsc.mjs sites` first to see exactly which properties this service account can ' +
        'read and in which form. Only if the property genuinely is not listed there: add the service ' +
        'account as a user on it in Search Console — Settings > Users and permissions > Add user, using ' +
        'the client_email from the key file. Restricted (read-only) access is sufficient for this tool.'
    );
  }
  return lines.join('\n');
}

async function getAccessToken(key) {
  const jwt = signJwt(key);
  const body = new URLSearchParams({
    grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
    assertion: jwt,
  });
  let response;
  try {
    response = await fetch(TOKEN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    });
  } catch (err) {
    throw new Error(`Network error exchanging JWT for an access token: ${err.message}`);
  }
  const text = await response.text();
  if (!response.ok) {
    throw new Error(formatApiError(response.status, text, 'OAuth token exchange'));
  }
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`Token endpoint returned a non-JSON response (HTTP ${response.status}).`);
  }
  if (!json.access_token) {
    throw new Error(`Token endpoint response had no access_token: ${text}`);
  }
  return json.access_token;
}

async function apiGet(url, accessToken) {
  let response;
  try {
    response = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } });
  } catch (err) {
    throw new Error(`Network error calling ${url}: ${err.message}`);
  }
  const text = await response.text();
  if (!response.ok) throw new Error(formatApiError(response.status, text, `GET ${url}`));
  return text ? JSON.parse(text) : {};
}

async function apiPost(url, accessToken, body) {
  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
  } catch (err) {
    throw new Error(`Network error calling ${url}: ${err.message}`);
  }
  const text = await response.text();
  if (!response.ok) throw new Error(formatApiError(response.status, text, `POST ${url}`));
  return text ? JSON.parse(text) : {};
}

function formatTable(headers, rows) {
  if (rows.length === 0) return '(no rows)';
  const widths = headers.map((h, i) => Math.max(String(h).length, ...rows.map((r) => String(r[i]).length)));
  const line = (cells) => cells.map((c, i) => String(c).padEnd(widths[i])).join('  ').trimEnd();
  return [line(headers), ...rows.map(line)].join('\n');
}

function isoDate(d) {
  return d.toISOString().slice(0, 10);
}

// GSC data typically lags 2-3 days behind today, so a naive "last N days" window
// including today or yesterday returns thin or empty rows.
function defaultDateRange() {
  const end = new Date();
  end.setUTCDate(end.getUTCDate() - 3);
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - 27);
  return { start: isoDate(start), end: isoDate(end) };
}

function parseFilter(raw) {
  const dim = FILTER_DIMENSIONS.find((d) => raw.startsWith(d));
  if (!dim) {
    throw new Error(
      `--filter "${raw}" must start with one of: ${FILTER_DIMENSIONS.join(', ')}`
    );
  }
  const rest = raw.slice(dim.length);
  const opEntry = FILTER_OPS.find(([token]) => rest.startsWith(token));
  if (!opEntry) {
    throw new Error(
      `--filter "${raw}" is missing a recognized operator after "${dim}" (one of: ` +
        `${FILTER_OPS.map(([t]) => t).join(', ')})`
    );
  }
  const [token, operator] = opEntry;
  const expression = rest.slice(token.length);
  if (!expression) {
    throw new Error(`--filter "${raw}" has an empty expression after the operator.`);
  }
  return { dimension: dim, operator, expression };
}

function nextArg(argv, i, flag) {
  if (i + 1 >= argv.length) throw new Error(`${flag} requires a value`);
  return argv[i + 1];
}

function parseSitesArgs(argv) {
  const opts = { json: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--json') opts.json = true;
    else throw new Error(`Unknown argument for "sites": ${argv[i]}`);
  }
  return opts;
}

function parseQueryArgs(argv) {
  if (argv.length === 0 || argv[0].startsWith('-')) {
    throw new Error('Usage: gsc.mjs query <siteUrl> [options]');
  }
  const defaults = defaultDateRange();
  const opts = {
    siteUrl: argv[0],
    start: defaults.start,
    end: defaults.end,
    dim: 'query',
    limit: 25,
    type: undefined,
    filters: [],
    json: false,
  };
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--start') opts.start = nextArg(argv, i++, a);
    else if (a === '--end') opts.end = nextArg(argv, i++, a);
    else if (a === '--dim') opts.dim = nextArg(argv, i++, a);
    else if (a === '--limit') opts.limit = Number(nextArg(argv, i++, a));
    else if (a === '--type') opts.type = nextArg(argv, i++, a);
    else if (a === '--filter') opts.filters.push(parseFilter(nextArg(argv, i++, a)));
    else if (a === '--json') opts.json = true;
    else throw new Error(`Unknown argument for "query": ${a}`);
  }
  if (!Number.isInteger(opts.limit) || opts.limit < 1 || opts.limit > 25000) {
    throw new Error('--limit must be an integer between 1 and 25000');
  }
  return opts;
}

function parseSitemapsArgs(argv) {
  if (argv.length === 0 || argv[0].startsWith('-')) {
    throw new Error('Usage: gsc.mjs sitemaps <siteUrl> [--json]');
  }
  const opts = { siteUrl: argv[0], json: false };
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === '--json') opts.json = true;
    else throw new Error(`Unknown argument for "sitemaps": ${argv[i]}`);
  }
  return opts;
}

function parseInspectArgs(argv) {
  if (argv.length < 2 || argv[0].startsWith('-') || argv[1].startsWith('-')) {
    throw new Error('Usage: gsc.mjs inspect <siteUrl> <pageUrl> [--language-code en] [--json]');
  }
  const opts = { siteUrl: argv[0], pageUrl: argv[1], languageCode: undefined, json: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--language-code') opts.languageCode = nextArg(argv, i++, a);
    else if (a === '--json') opts.json = true;
    else throw new Error(`Unknown argument for "inspect": ${a}`);
  }
  return opts;
}

async function cmdSites(accessToken, opts) {
  const json = await apiGet(`${WEBMASTERS_BASE}/sites`, accessToken);
  if (opts.json) {
    console.log(JSON.stringify(json, null, 2));
    return;
  }
  const rows = (json.siteEntry || []).map((s) => [s.siteUrl, s.permissionLevel]);
  console.log(formatTable(['siteUrl', 'permissionLevel'], rows));
}

// Prints what was actually measured — site, resolved window, dimensions, filters,
// row count — so a pasted result is self-contained evidence even without --json.
// Google's response never echoes the request back, which is why this is built from
// `opts`/`dims` rather than from the API response.
function formatQueryHeader({ siteUrl, start, end, type, dims, filters, rowCount }) {
  const lines = [
    `site: ${siteUrl}`,
    `window: ${start}..${end}  type: ${type || 'web'}`,
    `dimensions: ${dims.length > 0 ? dims.join(',') : '(none — property totals)'}`,
  ];
  if (filters.length > 0) {
    lines.push(`filters: ${filters.map((f) => `${f.dimension} ${f.operator} "${f.expression}"`).join(' AND ')}`);
  }
  lines.push(`rows: ${rowCount}`);
  return lines.join('\n');
}

// A bare "(no rows)" conflates three different facts (genuinely zero data, a filter
// that matched nothing, and a window predating the property) that look identical in
// the API response. Restate the request so the reader can tell which case they're in,
// and point at the property-totals probe (--dim "") as the cheapest way to settle it.
function formatEmptyQueryMessage(dims, filters) {
  if (filters.length > 0) {
    return (
      '(no rows) — either the filter(s) matched nothing, or there is genuinely no data in this ' +
        'window. Rerun without --filter to tell them apart, or with --dim "" for the property-totals ' +
        'probe: it returns a single row with no breakdown if there is any data at all, and no `rows` ' +
        'key whatsoever if the property is genuinely empty for this window.'
    );
  }
  if (dims.length > 0) {
    return (
      '(no rows) — this could be genuinely zero data, or just this dimension breakdown coming up ' +
        'empty. Rerun with --dim "" (the property-totals probe) to confirm: it returns a single row ' +
        'with no breakdown if there is any data at all in this window.'
    );
  }
  return (
    '(no rows) — this was already the property-totals probe (--dim ""), and the response had no ' +
      '`rows` key at all: Google has no recorded data for this property in this window, full stop.'
  );
}

async function cmdQuery(accessToken, opts) {
  const dims = opts.dim.split(',').map((d) => d.trim()).filter(Boolean);
  const body = {
    startDate: opts.start,
    endDate: opts.end,
    rowLimit: opts.limit,
  };
  if (dims.length > 0) body.dimensions = dims;
  if (opts.type) body.type = opts.type;
  if (opts.filters.length > 0) {
    body.dimensionFilterGroups = [{ groupType: 'and', filters: opts.filters }];
  }
  const url = `${WEBMASTERS_BASE}/sites/${encodeURIComponent(opts.siteUrl)}/searchAnalytics/query`;
  const json = await apiPost(url, accessToken, body);
  const rows = json.rows || [];

  if (opts.json) {
    const request = {
      siteUrl: opts.siteUrl,
      startDate: opts.start,
      endDate: opts.end,
      dimensions: dims.length > 0 ? dims : null,
      type: opts.type || 'web',
      filters: opts.filters,
      rowLimit: opts.limit,
    };
    console.log(JSON.stringify({ request, response: json }, null, 2));
    return;
  }

  console.log(
    formatQueryHeader({
      siteUrl: opts.siteUrl,
      start: opts.start,
      end: opts.end,
      type: opts.type,
      dims,
      filters: opts.filters,
      rowCount: rows.length,
    })
  );
  console.log('');

  if (rows.length === 0) {
    console.log(formatEmptyQueryMessage(dims, opts.filters));
    return;
  }

  const tableRows = rows.map((r) => [
    ...(dims.length > 0 ? r.keys : ['ALL']),
    Math.round(r.clicks),
    Math.round(r.impressions),
    `${(r.ctr * 100).toFixed(1)}%`,
    r.position.toFixed(1),
  ]);
  console.log(formatTable([...(dims.length > 0 ? dims : ['(total)']), 'clicks', 'impr', 'ctr', 'pos'], tableRows));
}

async function cmdSitemaps(accessToken, opts) {
  const url = `${WEBMASTERS_BASE}/sites/${encodeURIComponent(opts.siteUrl)}/sitemaps`;
  const json = await apiGet(url, accessToken);
  if (opts.json) {
    console.log(JSON.stringify(json, null, 2));
    return;
  }
  const rows = (json.sitemap || []).map((s) => {
    const submitted = (s.contents || []).reduce((sum, c) => sum + Number(c.submitted || 0), 0);
    const indexed = (s.contents || []).reduce((sum, c) => sum + Number(c.indexed || 0), 0);
    return [
      s.path,
      s.type || '-',
      s.lastDownloaded || 'never',
      s.isPending ? 'yes' : 'no',
      s.warnings ?? 0,
      s.errors ?? 0,
      submitted,
      indexed,
    ];
  });
  console.log(formatTable(['path', 'type', 'lastDownloaded', 'pending', 'warn', 'err', 'submitted', 'indexed'], rows));
}

function formatInspection(result) {
  const idx = result.indexStatusResult || {};
  const lines = [];
  // inspectionResultLink is the click-through to the same verdict in the Search Console
  // UI — the natural handoff artifact for the stakeholder — and is otherwise dropped.
  if (result.inspectionResultLink) lines.push(`inspectionResultLink: ${result.inspectionResultLink}`);

  // An unknown-or-uninspected URL — the common case for a new/empty property — has most
  // of these fields absent. Printing "field: -" for eight of nine is exactly the noise
  // this is meant to avoid; only print what Google actually returned.
  const idxFields = [
    ['verdict', idx.verdict],
    ['coverageState', idx.coverageState],
    ['robotsTxtState', idx.robotsTxtState],
    ['indexingState', idx.indexingState],
    ['pageFetchState', idx.pageFetchState],
    ['lastCrawlTime', idx.lastCrawlTime],
    ['crawledAs', idx.crawledAs],
    ['googleCanonical', idx.googleCanonical],
    ['userCanonical', idx.userCanonical],
  ];
  let idxFieldsPrinted = 0;
  for (const [label, value] of idxFields) {
    if (value === undefined || value === null || value === '') continue;
    lines.push(`${label}: ${value}`);
    idxFieldsPrinted++;
  }
  if (idx.sitemap && idx.sitemap.length > 0) {
    lines.push(`sitemap: ${idx.sitemap.join(', ')}`);
    idxFieldsPrinted++;
  }
  if (idx.referringUrls && idx.referringUrls.length > 0) {
    lines.push(`referringUrls: ${idx.referringUrls.length} (${idx.referringUrls.slice(0, 3).join(', ')}${idx.referringUrls.length > 3 ? ', ...' : ''})`);
    idxFieldsPrinted++;
  }
  if (idxFieldsPrinted === 0) {
    lines.push('indexStatusResult: (empty — Google has no index status recorded for this URL)');
  }

  if (result.mobileUsabilityResult) {
    const mob = result.mobileUsabilityResult;
    lines.push('');
    lines.push(`mobileUsability.verdict: ${mob.verdict ?? '-'}`);
    for (const issue of mob.issues || []) {
      lines.push(`  [${issue.severity ?? '-'}] ${issue.issueType ?? '-'}: ${issue.message ?? ''}`);
    }
  }

  if (result.richResultsResult) {
    const rich = result.richResultsResult;
    lines.push('');
    lines.push(`richResults.verdict: ${rich.verdict ?? '-'}`);
    for (const detected of rich.detectedItems || []) {
      lines.push(`  ${detected.richResultType ?? '-'}: ${(detected.items || []).length} item(s)`);
      for (const item of detected.items || []) {
        for (const issue of item.issues || []) {
          lines.push(`    [${issue.severity ?? '-'}] ${item.name ?? '-'}: ${issue.issueMessage ?? ''}`);
        }
      }
    }
  }

  if (result.ampResult) {
    const amp = result.ampResult;
    lines.push('');
    lines.push(`amp.verdict: ${amp.verdict ?? '-'}, ampUrl: ${amp.ampUrl ?? '-'}`);
    for (const issue of amp.issues || []) {
      lines.push(`  [${issue.severity ?? '-'}] ${issue.issueMessage ?? ''}`);
    }
  }

  return lines.join('\n');
}

async function cmdInspect(accessToken, opts) {
  const body = { inspectionUrl: opts.pageUrl, siteUrl: opts.siteUrl };
  if (opts.languageCode) body.languageCode = opts.languageCode;
  const json = await apiPost(INSPECTION_URL, accessToken, body);
  if (opts.json) {
    console.log(JSON.stringify(json, null, 2));
    return;
  }
  console.log(formatInspection(json.inspectionResult || {}));
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || argv[0] === '--help' || argv[0] === '-h') {
    console.log(USAGE);
    return;
  }

  const [cmd, ...rest] = argv;
  const commands = { sites: 1, query: 1, sitemaps: 1, inspect: 1 };
  if (!commands[cmd]) {
    console.error(`Unknown command: ${cmd}\n`);
    console.error(USAGE);
    process.exitCode = 1;
    return;
  }

  let opts;
  if (cmd === 'sites') opts = parseSitesArgs(rest);
  else if (cmd === 'query') opts = parseQueryArgs(rest);
  else if (cmd === 'sitemaps') opts = parseSitemapsArgs(rest);
  else if (cmd === 'inspect') opts = parseInspectArgs(rest);

  const key = readServiceAccountKey();
  const accessToken = await getAccessToken(key);

  if (cmd === 'sites') await cmdSites(accessToken, opts);
  else if (cmd === 'query') await cmdQuery(accessToken, opts);
  else if (cmd === 'sitemaps') await cmdSitemaps(accessToken, opts);
  else if (cmd === 'inspect') await cmdInspect(accessToken, opts);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(`gsc.mjs failed: ${err.message}`);
    process.exit(1);
  });
}

export {
  parseFilter,
  signJwt,
  formatTable,
  formatInspection,
  formatApiError,
  formatQueryHeader,
  formatEmptyQueryMessage,
  defaultDateRange,
  base64url,
};
