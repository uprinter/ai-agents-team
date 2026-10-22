"""Swimlanes: who does what, in order. Lanes are columns, time runs down.

Spec: {"type": "swimlanes", "title", "claim", "lanes": [{"id","label"}],
       "steps": [{"id","lane","label","accent"?}]}   in time order, one row each
Consecutive steps are joined by an arrow: straight down in the same lane, otherwise down to a bar, across and down.
"""
from .prims import Canvas
from .flow import _sizes


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad, nf, ef = v["width"], v["pad"], v["node_font"], v["edge_font"]
    lanes, steps = spec["lanes"], spec["steps"]
    k = len(lanes)
    idx = {ln["id"]: i for i, ln in enumerate(lanes)}
    for s in steps:
        if s["lane"] not in idx:
            raise ValueError(f"step '{s['id']}' names an unknown lane '{s['lane']}'")
    lw = int((W - 2 * pad) // k // g) * g
    margin = c.snap(max(8, pad * 0.75), up=True)
    lgap = c.snap(8, up=True)  # lane boxes do not touch, so no outline is drawn twice
    w, h, lines = _sizes(c, steps, max_w=lw - 2 * margin)
    hl = c.t["arrow"]["len_per_stroke"] * c.stroke("connector")
    gy = c.snap(2 * hl + 2 + 1 + 14, up=True)  # a stem, a bar and a last run of two heads
    x0 = c.snap((W - k * lw) / 2)
    head = c.snap(ef * 2.4, up=True)  # the lane name is centred in its header, clear of the outline
    y0 = top + pad
    ybody = y0 + head
    n = len(steps)
    ybot = ybody + margin + n * h + (n - 1) * gy + margin
    r = c.radius_for(lw, 60)
    for i, ln in enumerate(lanes):
        x = x0 + i * lw
        c.shape("container", "group", x + lgap / 2, y0, lw - lgap, ybot - y0, (r, r, r, r), stroke="muted", dash="3 4", snap=False)
        c.text(x + lw / 2, y0 + head / 2 + ef * 0.345, ln["label"], ef, 700, "ink", halo=False, role="group-label", layer="container")
    pos, ids = {}, {}
    for j, s in enumerate(steps):
        x = x0 + idx[s["lane"]] * lw + c.snap((lw - w) / 2)
        y = ybody + margin + j * (h + gy)
        pos[s["id"]] = (x, y)
        ids[s["id"]] = c.node(x, y, w, h, lines[s["id"]], accent=s.get("accent", False), cue="weight" if s.get("accent") else None,
                              sw="emphasis" if s.get("accent") else "outline")
    for a, b in zip(steps, steps[1:]):
        (ax, ay), (bx, by) = pos[a["id"]], pos[b["id"]]
        sx, dx = ax + w / 2, bx + w / 2
        start, end = (sx, ay + h), (dx, by - 1)
        bar = by - 1 - (2 * hl + 2)
        pts = [start, end] if sx == dx else [start, (sx, bar), (dx, bar), end]
        c.edge(pts, src=ids[a["id"]], dst=ids[b["id"]])
    c.W = W
    c.H = height or (ybot + pad)
    return c.svg()
