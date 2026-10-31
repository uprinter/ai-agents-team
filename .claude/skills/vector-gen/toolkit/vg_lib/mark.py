"""Mark: a logo, symbol or tile built from traced layers and a wordmark set from font outlines.

Spec: {"type": "mark", "title", "claim", "view": [w, h], "background"?: token,
       "layers": [{"name", "d" | "union": [LAYER, ...], "fill": token-or-hex, "part"?: true}],
       "wordmark"?: {"text", "font": FONT.ttf, "size", "x", "y", "fill", "tracking"?, "kern"?: {"AB": units}, "axes"?: {"wght": 600}},
       "tile"?: {"grid": 16|24|32, "palette": {"a": hex}, "rows": ["aab.", ...]},
       "sizes"?: [16, 24, 32, 48, 96]}
Unlike the diagram forms a mark has no width variants and no Canvas; it is built by `vg.py mark`. The wordmark is
turned into paths with fontTools (`uv run --with fonttools`), so no font is needed where the SVG is shown. `union`
merges layer paths into one outline and needs skia-pathops (`--with skia-pathops`); a layer marked
`part` only feeds a union and is not drawn. Both tools are named in
references/logo-craft.md and need the founder's approval before first use.
"""
import re

MAX_FILLS = 6


def _tool(name):
    try:
        return __import__(name, fromlist=["x"])
    except ImportError:
        raise ValueError(f"this spec needs {name}: run with `uv run --with {'fonttools' if name == 'fontTools' else 'skia-pathops'}` after the tool is approved (references/logo-craft.md)")


def _fill(tok, v):
    return tok["colors"].get(v, v)


def wordmark_path(w):
    """Outline of the text as one SVG path; advance, tracking and kerning pairs apply in font units."""
    _tool("fontTools")
    from fontTools import ttLib as ttlib
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    font = ttlib.TTFont(w["font"])
    if w.get("axes") and "fvar" in font:
        from fontTools.varLib import instancer
        font = instancer.instantiateVariableFont(font, w["axes"])
    upem, cmap, gs = font["head"].unitsPerEm, font.getBestCmap(), font.getGlyphSet()
    k = w["size"] / upem
    pen, x, text, kern = SVGPathPen(gs), 0.0, w["text"], w.get("kern", {})
    for i, ch in enumerate(text):
        name = cmap[ord(ch)]
        gs[name].draw(TransformPen(pen, (k, 0, 0, -k, w["x"] + x * k, w["y"])))
        x += gs[name].width + w.get("tracking", 0) + (kern.get(text[i:i + 2], 0) if i < len(text) - 1 else 0)
    return pen.getCommands(), x * k


def union(paths):
    pathops = _tool("pathops")
    out = pathops.Path()
    for d in paths:
        p = pathops.Path()
        _parse_into(p, d)
        out = pathops.op(out, p, pathops.PathOp.UNION)
    from fontTools.pens.svgPathPen import SVGPathPen
    pen = SVGPathPen(None)
    out.draw(pen)
    return pen.getCommands()


def _parse_into(path, d):
    from fontTools.svgLib.path import parse_path
    parse_path(d, path.getPen())


def build(spec, tok, background=True):
    """Returns (svg text, list of fill colours used). Raises ValueError with the gate that failed.
    background=False leaves the canvas transparent, which the size gates measure."""
    W, H = spec["view"]
    by_name, parts, fills = {}, [], []
    if background and spec.get("background"):
        parts.append(f'<rect width="{W}" height="{H}" fill="{_fill(tok, spec["background"])}"/>')
        fills.append(_fill(tok, spec["background"]))
    for l in spec.get("layers", []):
        d = union([by_name[n] for n in l["union"]]) if "union" in l else l["d"]
        by_name[l["name"]] = d
        if l.get("part"):
            continue
        f = _fill(tok, l["fill"])
        fills.append(f)
        parts.append(f'<path data-layer="{l["name"]}" d="{d}" fill="{f}"/>')
    if spec.get("wordmark"):
        d, adv = wordmark_path(spec["wordmark"])
        f = _fill(tok, spec["wordmark"]["fill"])
        fills.append(f)
        parts.append(f'<path data-layer="wordmark" d="{d}" fill="{f}"/>')
    if spec.get("tile"):
        t = spec["tile"]
        n = t["grid"]
        if n not in (16, 24, 32):
            raise ValueError(f"tile grid {n} is not 16, 24 or 32")
        if len(t["rows"]) != n or any(len(r) != n for r in t["rows"]):
            raise ValueError(f"tile rows are not {n}x{n}")
        for ch, hexv in t["palette"].items():
            runs = [(y, m.start(), m.end()) for y, r in enumerate(t["rows"]) for m in re.finditer(re.escape(ch) + "+", r)]
            if runs:
                fills.append(hexv)
                rects = "".join(f'<rect x="{a}" y="{y}" width="{b - a}" height="1"/>' for y, a, b in runs)
                parts.append(f'<g data-layer="tile-{ch}" fill="{hexv}" shape-rendering="crispEdges">{rects}</g>')
        W = H = n
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" role="img" aria-label="{spec["claim"]}">'
           f'<title>{spec["title"]}</title>{"".join(parts)}</svg>')
    return svg, sorted(set(fills))


def gates(fills, sizes_png, symbol=True):
    """fills: distinct colours; sizes_png: {px: PIL image RGBA}. Returns error strings.
    The size gates read a square symbol; a spec with a wordmark is wide, so only the colour count applies."""
    errs = []
    if len(fills) > MAX_FILLS:
        errs.append(f"{len(fills)} flat colours, more than {MAX_FILLS}")
    for px, im in (sizes_png.items() if symbol else ()):
        a = im.getchannel("A")
        filled = sum(1 for v in a.getdata() if v > 127) / (px * px)
        if filled < 0.08:
            errs.append(f"at {px}px the mark covers {filled:.0%} of the box: it disappears")
        if px <= 32 and filled >= 0.08:
            opaque = [p[:3] for p in im.getdata() if p[3] > 127]
            top = max(opaque.count(c) for c in set(opaque)) / len(opaque)
            if top > 0.9:
                errs.append(f"at {px}px one colour is {top:.0%} of the mark: no shape left to read")
    return errs
