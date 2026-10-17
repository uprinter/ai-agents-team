#!/usr/bin/env sh
# ste100-check.sh — report sentences over the ASD-STE100 length limits in Markdown prose.
# Usage: ste100-check.sh [-p] FILE...   (-p: procedure limit 20 words; default description limit 25)
# Skips fenced code blocks, headings, tables, front matter, and inline code spans count as one word.
# Exit 1 when any sentence is over the limit, so an author can run it before a push and a reviewer in review.
limit=25
if [ "$1" = "-p" ]; then limit=20; shift; fi
status=0
for f in "$@"; do
  awk -v limit="$limit" -v file="$f" '
    BEGIN { infence=0; infront=0 }
    NR==1 && /^---$/ { infront=1; next }
    infront && /^---$/ { infront=0; next }
    infront { next }
    /^```/ { infence = !infence; next }
    infence { next }
    /^#/ || /^\|/ || /^[[:space:]]*$/ { next }
    {
      line=$0
      gsub(/`[^`]*`/, "CODE", line)
      gsub(/\[\[[^]]*\]\]/, "LINK", line)
      gsub(/\([^)]*\)/, "", line)
      n=split(line, s, /[.!?]([[:space:]]|$)/)
      for (i=1;i<=n;i++) {
        w=split(s[i], words, /[[:space:]]+/)
        c=0; for (j=1;j<=w;j++) if (words[j] ~ /[[:alnum:]]/) c++
        if (c>limit) { printf "%s:%d: %d words (limit %d): %s\n", file, NR, c, limit, s[i]; bad=1 }
      }
    }
    END { exit bad ? 1 : 0 }
  ' "$f" || status=1
done
exit $status
