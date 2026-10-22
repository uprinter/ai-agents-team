#!/usr/bin/env python3
"""Rebuild icons/brands.json from the slugs in icons/brands.txt.

Usage: build_brands.py PATH_TO_UNPACKED_simple-icons_PACKAGE
The package comes from https://registry.npmjs.org/simple-icons/-/simple-icons-<version>.tgz.
The SVG files are CC0, the logos are still the owners' trademarks: keep each brand's source and guidelines
link so the build can point at them.
"""
import json, re, sys
from pathlib import Path

here = Path(__file__).parent
pkg = Path(sys.argv[1])
meta = json.loads((pkg / "data" / "simple-icons.json").read_text())
version = json.loads((pkg / "package.json").read_text())["version"]
SUB = {".": "dot", "+": "plus", "&": "and", "đ": "d", "ħ": "h", "ı": "i", "ĸ": "k", "ŀ": "l", "ł": "l", "ß": "ss", "ŧ": "t"}


def slug_of(entry):
    if entry.get("slug"):
        return entry["slug"]
    t = entry["title"].lower()
    for k, v in SUB.items():
        t = t.replace(k, v)
    return re.sub(r"[^a-z0-9]", "", t)


by_slug = {slug_of(e): e for e in meta}
out = {"source": f"simple-icons {version}", "license": "CC0-1.0 files; logos remain the owners' trademarks", "viewBox": 24, "brands": {}}
for slug in [s.strip() for s in (here / "brands.txt").read_text().split() if s.strip()]:
    svg = (pkg / "icons" / f"{slug}.svg").read_text()
    paths = re.findall(r'<path d="([^"]+)"', svg)
    if len(paths) != 1 or re.search(r"<(circle|rect|g|polygon|ellipse|line)\b", svg):
        sys.exit(f"{slug}: expected one plain path")
    e = by_slug.get(slug, {})
    if e.get("license"):
        sys.exit(f"{slug}: licence {e['license'].get('type') or e['license'].get('url')} asks for attribution or share-alike; only plain CC0 brands go in the set")
    item = {"title": e.get("title", slug), "d": paths[0]}
    if e.get("guidelines"):
        item["guidelines"] = e["guidelines"]
    out["brands"][slug] = item
(here / "brands.json").write_text(json.dumps(out, separators=(",", ":")))
(here / "LICENSE-simple-icons.txt").write_text((pkg / "LICENSE.md").read_text() + "\n\n---\n\n" + (pkg / "DISCLAIMER.md").read_text())
print(f"{len(out['brands'])} brands from simple-icons {version}")
