"""Measured gates on a rendered SVG. Returns a list of error strings; empty means every gate passed.

Geometry gates run in Chromium (getBBox on the real render); token gates parse the SVG text.
Gate list and rationale: references/craft-rules.md, section "Gates".
"""
import math, re
import xml.etree.ElementTree as ET

JS = r"""
(args) => {
  const {minpx, grid} = args;
  const svg = document.querySelector('svg');
  const vb = svg.viewBox.baseVal;
  const scale = svg.getBoundingClientRect().width / vb.width;
  const errs = [];
  const bb = e => { if (e.dataset.role === 'icon') { const x = +e.dataset.x, y = +e.dataset.y, z = +e.dataset.size; return {x, y, w:z, h:z, r:x+z, b:y+z}; } const b = e.getBBox(); return {x:b.x, y:b.y, w:b.width, h:b.height, r:b.x+b.width, b:b.y+b.height}; };
  const hit = (a, c, tol=0) => a.x+tol < c.r && c.x+tol < a.r && a.y+tol < c.b && c.y+tol < a.b;
  const near = (a, b) => Math.abs(a - b) < 0.06;
  const q = s => [...svg.querySelectorAll(s)];

  const texts = q('text');
  texts.forEach(t => {
    const px = parseFloat(t.getAttribute('font-size')) * scale;
    if (px < minpx - 0.01 && !t.dataset.fit) errs.push(`text below ${minpx}px at this width: "${t.textContent}" ${px.toFixed(1)}px`);
    const b = bb(t);
    if (b.x < 0 || b.y < 0 || b.r > vb.width || b.b > vb.height) errs.push(`text outside canvas: "${t.textContent}"`);
  });

  // no dead strip: the empty space under the content stays within twice the space above it (plus 8px)
  const content = q('[data-role]').filter(e => !['guide', 'divider'].includes(e.dataset.role)).map(bb);
  if (content.length) {
    const top = Math.min(...content.map(b => b.y)), bot = vb.height - Math.max(...content.map(b => b.b));
    if (bot > 2 * top + 8) errs.push(`dead strip: ${bot.toFixed(0)}px empty under the content, ${top.toFixed(0)}px above`);
  }

  // containment: text inside its owner shape
  const byId = {}; q('[id]').forEach(e => byId[e.id] = e);
  texts.filter(t => t.dataset.in).forEach(t => {
    const o = byId[t.dataset.in]; if (!o) return;
    const b = bb(t), p = bb(o);
    if (b.x < p.x + 1 || b.r > p.r - 1 || b.y < p.y || b.b > p.b) errs.push(`text leaves its shape: "${t.textContent}"`);
  });

  // icons: inside their node, at least the icon floor on screen, clear of text
  const iconMin = parseFloat(svg.dataset.minIconPx || 0);
  const icons = q('[data-role=icon]');
  icons.forEach(ic => {
    const b = bb(ic), px = parseFloat(ic.dataset.size) * scale, o = byId[ic.dataset.in];
    if (iconMin && px < iconMin - 0.01) errs.push(`icon "${ic.dataset.name}" ${px.toFixed(1)}px on screen, below ${iconMin}px`);
    if (o) { const p = bb(o); if (b.x < p.x || b.r > p.r || b.y < p.y || b.b > p.b) errs.push(`icon "${ic.dataset.name}" leaves its shape`); }
    texts.forEach(t => { if (hit(b, bb(t), -3)) errs.push(`icon "${ic.dataset.name}" closer than 3px to text "${t.textContent}"`); });
  });

  // text overlaps text; text touches shapes it does not belong to
  for (let i = 0; i < texts.length; i++) for (let j = i+1; j < texts.length; j++)
    if (hit(bb(texts[i]), bb(texts[j]), 1)) errs.push(`text overlap: "${texts[i].textContent}" / "${texts[j].textContent}"`);
  const solids = q('[data-role=node],[data-role=tab]');
  texts.forEach(t => {
    if (t.dataset.in) return;
    solids.forEach(s => { if (hit(bb(t), bb(s), -3)) errs.push(`text closer than 3px to a ${s.dataset.role}: "${t.textContent}"`); });
  });

  // a group label keeps clear of the top of its container: at least half its font size
  const containers = q('[data-role=group]').map(bb);
  texts.filter(t => t.dataset.role === 'group-label').forEach(t => {
    const b = bb(t), fs = parseFloat(t.getAttribute('font-size'));
    containers.forEach(g => { if (b.x >= g.x && b.r <= g.r && b.y >= g.y && b.y - g.y < 0.5 * fs) errs.push(`group label "${t.textContent}" is ${(b.y - g.y).toFixed(1)}px from the top of its box`); });
  });

  // equal size (and equal gaps for ":x"/":y" groups)
  const groups = {};
  q('[data-group]').forEach(e => (groups[e.dataset.group] ||= []).push(e));
  Object.entries(groups).forEach(([name, els]) => {
    const bs = els.map(bb);
    if (!bs.every(b => near(b.w, bs[0].w) && near(b.h, bs[0].h))) errs.push(`group ${name}: members differ in size`);
    const axis = name.split(':')[1];
    if (axis && bs.length > 2) {
      const s = [...bs].sort((a, b) => axis === 'x' ? a.x - b.x : a.y - b.y);
      const gaps = s.slice(1).map((b, i) => axis === 'x' ? b.x - s[i].r : b.y - s[i].b);
      if (!gaps.every(gp => near(gp, gaps[0]))) errs.push(`group ${name}: gaps differ (${gaps.map(x => x.toFixed(1)).join(', ')})`);
    }
  });

  // grid snap
  const g = grid;
  q('[data-snap]').forEach(e => {
    const b = bb(e);
    [b.x, b.y, b.w, b.h].forEach(v => { const k = v / g; if (Math.abs(k - Math.round(k)) > 0.02) errs.push(`off-grid (${g}px): ${e.dataset.role} at ${b.x},${b.y} ${b.w}x${b.h}`); });
  });

  // arrowheads: length >= 5 strokes, width >= 4 strokes
  q('[data-role=head]').forEach(h => {
    const b = bb(h), sw = parseFloat(h.dataset.sw), L = Math.max(b.w, b.h), Wd = Math.min(b.w, b.h);
    if (L < 5 * sw || Wd < 4 * sw) errs.push(`arrowhead too small: ${L.toFixed(1)}x${Wd.toFixed(1)} for stroke ${sw}`);
  });

  // frames clear of node rows; everything with a frame stays inside the canvas
  q('[data-role=frame],[data-role=group]').forEach(f => {
    const b = bb(f);
    if (b.x < 1 || b.r > vb.width - 1 || b.y < 0 || b.b > vb.height) errs.push('frame touches or leaves the canvas');
  });
  const nodes = q('[data-role=node]').map(n => ({id: n.id, ...bb(n)}));
  q('[data-role=frame]').forEach(f => {
    const b = bb(f);
    nodes.forEach(n => { if (hit(b, n, 0) ) errs.push('frame overlaps a node'); });
  });

  // every arrow keeps a shaft (total path at least three heads) and its head sits on a straight run (last run at least head + 4)
  q('[data-role=edge]').forEach(e => {
    const pts = e.dataset.pts.split(';').map(p => p.split(',').map(Number)), hl = parseFloat(e.dataset.hl);
    const runs = pts.slice(1).map((p, i) => Math.abs(p[0] - pts[i][0]) + Math.abs(p[1] - pts[i][1]));
    const total = runs.reduce((a, b) => a + b, 0);
    if (total < 3 * hl) errs.push(`arrow ${total.toFixed(0)}px long, shorter than three heads (${(3 * hl).toFixed(0)}px)`);
    if (runs[runs.length - 1] < 2 * hl - 0.5) errs.push(`arrow head sits on a ${runs[runs.length - 1].toFixed(0)}px run, shorter than two heads`);
  });

  // edges: segments must not cross foreign nodes; labels must not sit on foreign edges
  const segHit = (a, b, r) => {
    const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]), y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
    return x0 < r.r && x1 > r.x && y0 < r.b && y1 > r.y;
  };
  const edges = q('[data-role=edge]').map(e => ({el: e, pts: e.dataset.pts.split(';').map(p => p.split(',').map(Number))}));
  edges.forEach(({el, pts}) => {
    nodes.forEach(n => {
      if (n.id === el.dataset.src || n.id === el.dataset.dst) return;
      for (let i = 0; i < pts.length - 1; i++) if (segHit(pts[i], pts[i+1], n)) { errs.push(`edge crosses node ${n.id}`); break; }
    });
  });
  texts.filter(t => t.dataset.for).forEach(t => {
    const b = bb(t);
    edges.forEach(({el, pts}) => {
      if (el.id === t.dataset.for) return;
      for (let i = 0; i < pts.length - 1; i++) if (segHit(pts[i], pts[i+1], {x:b.x+1, r:b.r-1, y:b.y+1, b:b.b-1})) { errs.push(`label "${t.textContent}" sits on another edge`); break; }
    });
  });
  return {scale, errs, minFont: Math.min(...texts.map(t => parseFloat(t.getAttribute('font-size')) * scale))};
}
"""


def _lum(hexc):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def token_gates(svg_text, tok):
    errs = []
    root = ET.fromstring(svg_text)
    ns = "{http://www.w3.org/2000/svg}"
    pal = {v.lower(): k for k, v in tok["colors"].items()}
    bg = tok["colors"]["bg"]
    strokes, fills = set(tok["stroke"].values()), {}
    seen_sw = set()
    allowed_r = set(tok["radius"].values()) | {0}
    fonts = set(tok["type"]["scale"]) | {tok["type"]["fit_min"]}
    byid = {e.get("id"): e for e in root.iter() if e.get("id")}
    in_icon = {id(x) for g in root.iter() if g.get("data-role") == "icon" for x in g.iter()}  # an icon's own drawing is not ours to scale
    for e in root.iter():
        tag = e.tag.replace(ns, "")
        role = e.get("data-role", "")
        for attr in ("fill", "stroke"):
            val = e.get(attr)
            if val and val != "none" and val.lower() not in pal:
                errs.append(f"colour {val} is not a token ({tag} {role})")
        if role == "icon":
            if float(e.get("data-size")) not in tok["icon"]["scale"]:
                errs.append(f"icon size {e.get('data-size')} is not on the icon scale")
            if e.get("data-kind") != "brand":
                esw = float(e.get("data-sw"))
                seen_sw.add(esw)
                if esw not in strokes:
                    errs.append(f"icon stroke {esw} is not in the stroke scale")
            ratio = contrast(e.get("fill") if e.get("data-kind") == "brand" else e.get("stroke"), bg)
            if ratio < tok["contrast"]["graphic"]:
                errs.append(f"icon \"{e.get('data-name')}\" contrast {ratio:.1f}:1 below {tok['contrast']['graphic']}")
            continue
        sw = e.get("stroke-width")
        if sw and tag != "text":
            seen_sw.add(float(sw))
            if float(sw) not in strokes:
                errs.append(f"stroke width {sw} is not in the stroke scale ({role})")
        if tag == "rect" and e.get("rx") and not role and id(e) not in in_icon and float(e.get("rx")) not in allowed_r:
            errs.append(f"corner radius {e.get('rx')} is not in the radius scale (rect)")
        if tag == "path" and e.get("d") and role:
            for r in re.findall(r"A([\d.]+) ", e.get("d")):
                if float(r) not in allowed_r:
                    errs.append(f"radius {r} is not in the radius scale ({role})")
        if tag == "text" and role in ("node-text", "edge-label", "title", "tab-text", "group-label", "key", "axis-label") and not e.get("data-cont") and e.text and e.text[0].isalpha() and e.text[0].islower():
            errs.append(f"text \"{e.text}\" starts with a lowercase letter; use sentence case (first letter capital)")
        if tag == "text":
            fs = float(e.get("font-size"))
            if fs not in fonts:
                errs.append(f"font size {fs} is not in the type scale")
            owner = byid.get(e.get("data-in"))
            back = (owner.get("fill") if owner is not None and owner.get("fill") != "none" else bg)
            ratio = contrast(e.get("fill"), back)
            if ratio < tok["contrast"]["text"]:
                errs.append(f"text contrast {ratio:.1f}:1 below {tok['contrast']['text']} (\"{e.text}\")")
        if role in ("edge", "frame", "group", "divider") and e.get("stroke"):
            ratio = contrast(e.get("stroke"), bg)
            if ratio < tok["contrast"]["graphic"]:
                errs.append(f"{role} stroke contrast {ratio:.1f}:1 below {tok['contrast']['graphic']}")
        if e.get("data-accent") == "1" and not e.get("data-cue"):
            errs.append(f"accent colour on a {role} without a second cue (weight, dash, label or fill)")
    if len(seen_sw) > 4:
        errs.append(f"{len(seen_sw)} stroke weights in one figure; keep four at most")
    return errs


def geometry_gates(svg_text, display_width, png=None, scale=2, minpx=None, grid=None):
    from playwright.sync_api import sync_playwright
    if minpx is None:
        minpx = float(re.search(r'data-min-px="([\d.]+)"', svg_text).group(1))
    if grid is None:
        grid = float(re.search(r'data-grid="([\d.]+)"', svg_text).group(1))
    html = f'<body style="margin:0;background:#000">{svg_text}<style>svg{{width:100%;height:auto;display:block}}</style>'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": math.ceil(display_width), "height": 10}, device_scale_factor=scale)
        pg.set_content(html)
        r = pg.evaluate(JS, {"minpx": minpx, "grid": grid})
        if png:
            pg.screenshot(path=str(png), full_page=True)
        b.close()
    return r["errs"], r["minFont"]


def run(svg_text, tok, display_width, png=None, scale=2):
    errs = token_gates(svg_text, tok)
    g, minfont = geometry_gates(svg_text, display_width, png, scale)
    return sorted(set(errs + g)), minfont


def social_gates(svg_text, tok, png, valid_from):
    """The feed image: ratio inside the range the feed shows whole, pixel width, file size, readable at the narrowest phone."""
    from PIL import Image
    s = tok["social"]
    w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg_text).groups())
    errs = []
    if not s["ratio_min"] - 1e-6 <= h / w <= s["ratio_max"] + 1e-6:
        errs.append(f"ratio {h / w:.3f} is outside {s['ratio_min']}..{s['ratio_max']} (height / width)")
    if valid_from > w + 0.5:
        errs.append(f"text too small for a {w:g}px-wide phone feed: valid from {valid_from:.0f}px")
    with Image.open(png) as im:
        if im.size != (round(w * s["scale"]), round(h * s["scale"])):
            errs.append(f"PNG is {im.size[0]}x{im.size[1]}, expected {round(w * s['scale'])}x{round(h * s['scale'])}")
    if png.stat().st_size > s["max_bytes"]:
        errs.append(f"PNG is {png.stat().st_size} bytes, over the {s['max_bytes']} byte upload limit")
    return errs


def run_external(svg_text, tok, display_width=None, png=None):
    """Gates that apply to an SVG the toolkit did not build: palette, stroke, type scale, contrast, text size at the display
    width, text outside the canvas and overlapping text. Gates that need the toolkit's data-* marks (arrowheads, grid,
    equal groups, icon and edge rules) cannot run, so a PASS here is partial. Returns (errors, display width, smallest text px)."""
    m = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"\s', svg_text) or re.search(r'viewBox="[^"]*?([\d.]+)\s+[\d.]+"', svg_text)
    width = display_width or (float(m.group(1)) if m else 600)
    errs = token_gates(svg_text, tok)
    g, minfont = geometry_gates(svg_text, width, png, 2, minpx=float(tok["type"]["min"]), grid=1)
    return sorted(set(errs + g)), width, minfont
