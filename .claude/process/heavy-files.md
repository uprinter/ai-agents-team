# Heavy files live in cloud storage, not in git

**Rule.** A file over 2 MB never enters a target project's git history. Sources, masters and raw exports go to Google Drive. The repository holds a web-sized derivative and one pointer row (→ RP-70).

## Drive layout

`Heavy files / <repository name> / <area or NNN-feature> / <file name as exported>`

Example: `Heavy files / <repository> / brand-3d / <generator>_<model name>_<date>.blend`. Keep the original file name. Do not overwrite a file: add a dated suffix to a new version.

## Pointer row

Each target project keeps `docs/heavy-files.md`: one table, one row per file.

| Column | Content |
|---|---|
| File | original name |
| Drive link | share link, no public sharing |
| Size, SHA-256 | of the Drive file |
| Source | tool or generator, with date and prompt or settings |
| Licence | exact terms, for example `CC BY 4.0, credit "<generator>"` or `Private (paid plan)` |
| Derivative | path in the repository, or `none` |

The row is the audit trail. A file with no licence entry is not used.

## Account and upload path

**All AI automation uses one Google account, set up for that purpose and named in your own deployment's instructions.** The Drive connector and every Drive for desktop folder an agent writes to must belong to it; an agent never writes to the owner's other accounts. Before the first write, confirm the `owner` field of a Drive listing shows that account.

Upload with the connector (`create_file`: folders freely; a file only when its base64 fits the call, in practice a few MB). A larger file goes through the owner: they drop it into the named folder and return the link. No other route (browser automation, another service, another account) without the owner's approval of that exact route (→ RP-31).

## Derivative

Commit only what a client or a build needs: a web-sized export, a decimated model, a compressed texture. Size budget per file: 2 MB; images published to the web follow the project's own size table.

## Checks

- **Author, before `git add`:** `find . -size +2M -not -path './.git/*'` shows nothing staged. A file committed and then deleted still lives in history; if it happens, stop and report, never rewrite history alone.
- **Reviewer:** the attestation states `heavy-files: no blob over 2 MB; pointer row present` and names the row. A new binary with no pointer row is a finding.
- **`/verify`:** `git diff --numstat <base>..<head>` plus `git cat-file -s` on each added blob. Any added blob over 2 MB fails the gate.
