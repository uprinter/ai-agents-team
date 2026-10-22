#!/usr/bin/env python3
"""Rebuild icons/lucide.json from the names in icons/icons.txt.

Usage: build_icons.py PATH_TO_UNPACKED_lucide-static_PACKAGE
The package comes from https://registry.npmjs.org/lucide-static/-/lucide-static-<version>.tgz (ISC licence).
Only shape elements and the attributes below are kept; anything else in the source is dropped.
"""
import json, shutil, sys
from pathlib import Path

KEEP = {"path": {"d"}, "circle": {"cx", "cy", "r"}, "ellipse": {"cx", "cy", "rx", "ry"}, "line": {"x1", "y1", "x2", "y2"},
        "polyline": {"points"}, "polygon": {"points"}, "rect": {"x", "y", "width", "height", "rx", "ry"}}
here = Path(__file__).parent
pkg = Path(sys.argv[1])
nodes = json.loads((pkg / "icon-nodes.json").read_text())
tags = json.loads((pkg / "tags.json").read_text())
version = json.loads((pkg / "package.json").read_text())["version"]
names = [n.strip() for n in (here / "icons.txt").read_text().split() if n.strip()]
missing = [n for n in names if n not in nodes]
if missing:
    sys.exit(f"not in lucide-static {version}: {', '.join(missing)}")
out = {"source": f"lucide-static {version}", "license": "ISC, see LICENSE-lucide.txt", "viewBox": 24, "icons": {}}
for n in names:
    shapes = []
    for tag, attrs in nodes[n]:
        if tag not in KEEP:
            sys.exit(f"{n}: unexpected element {tag}")
        shapes.append([tag, {k: v for k, v in attrs.items() if k in KEEP[tag]}])
    out["icons"][n] = {"tags": tags.get(n, [])[:8], "shapes": shapes}
(here / "lucide.json").write_text(json.dumps(out, separators=(",", ":")))
shutil.copy(pkg / "LICENSE", here / "LICENSE-lucide.txt")
print(f"{len(names)} icons from lucide-static {version}")
