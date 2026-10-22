"""Hub: one central node with the others around it, joined by straight bus lines.

Spec: {"type": "hub", "title", "claim", "hub": {"label","icon"?}, "spokes": [{"label","icon"?}],
       "arrows": "none" | "out"}
Two to four spokes sit around the hub in a cross: left and right, with up and down added for three and four.
Five and six spokes, or "layout": "rows", put the first half in a row above the hub and the rest in a row below,
joined by one trunk and one bar each, the same bus as a flow fork. The hub is drawn larger and in the accent.
"out" puts a head on every spoke.
"""
from .prims import Canvas
from .flow import _sizes


SLOTS = {2: ["W", "E"], 3: ["W", "N", "E"], 4: ["N", "E", "S", "W"]}


def _cross(c, spec, top, height):
    v, g = c.v, c.v["grid"]
    W, pad = v["width"], v["pad"]
    slots = SLOTS[len(spec["spokes"])]
    hl = c.t["arrow"]["len_per_stroke"] * c.stroke("connector")
    run = c.snap(3 * hl + 4, up=True)  # an arrow between boxes is at least three heads
    side = "W" in slots or "E" in slots
    nodes = [{"id": f"s{i}", **s} for i, s in enumerate(spec["spokes"])]
    ratio = 1.25  # the hub is a quarter larger than a spoke
    max_w = int((W - 2 * pad - 2 * run) / (2 + ratio) // g) * g if side else int((W - 2 * pad) // g) * g
    w, h, lines = _sizes(c, nodes + [{"id": "hub", **spec["hub"]}], max_w=max_w)
    wc, hc = c.snap(w * ratio, up=True), c.snap(h * ratio, up=True)
    total = (2 * w + wc + 2 * run) if side else wc
    x0 = c.snap((W - total) / 2)
    xc = x0 + (w + run if side else 0)
    has_n, has_s = "N" in slots, "S" in slots
    ym = top + pad + (h + run if has_n else 0)
    hid = c.node(xc, ym, wc, hc, lines["hub"], group="hub", accent=True, cue="weight", sw="emphasis", icon=spec["hub"].get("icon"))
    heads = "filled" if spec.get("arrows", "none") == "out" else "none"
    pos = {"W": (x0, ym + c.snap((hc - h) / 2)), "E": (xc + wc + run, ym + c.snap((hc - h) / 2)),
           "N": (xc + c.snap((wc - w) / 2), top + pad), "S": (xc + c.snap((wc - w) / 2), ym + hc + run)}
    for slot, node in zip(slots, nodes):
        x, y = pos[slot]
        sid = c.node(x, y, w, h, lines[node["id"]], icon=node.get("icon"))
        hx, hy = xc + wc / 2, ym + hc / 2
        a, b = {"W": ((xc, hy), (x + w + 1, hy)), "E": ((xc + wc, hy), (x - 1, hy)),
                "N": ((hx, ym), (hx, y + h + 1)), "S": ((hx, ym + hc), (hx, y - 1))}[slot]
        c.edge([a, b], head=heads, src=hid, dst=sid)
    c.W = W
    c.H = height or (ym + hc + (run + h if has_s else 0) + pad)
    return c.svg()


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad = v["width"], v["pad"]
    n = len(spec["spokes"])
    if not 2 <= n <= 6:
        raise ValueError("hub needs two to six spokes")
    if n <= 4 and spec.get("layout") != "rows":
        try:
            return _cross(Canvas(tok, variant, spec["title"], spec["claim"]), spec, top, height)
        except ValueError:
            if v.get("cross_only"):
                raise  # the feed image tries smaller type before it gives up the cross
            # three columns do not fit this width: fall back to the rows
    nodes = [{"id": f"s{i}", **s} for i, s in enumerate(spec["spokes"])]
    up, down = nodes[: (n + 1) // 2], nodes[(n + 1) // 2:]
    gap = c.snap(max(8, v.get("row_gap", v["gap"])), up=True)
    k = len(up)
    w, h, lines = _sizes(c, nodes + [{"id": "hub", **spec["hub"]}], max_w=int((W - 2 * pad - (k - 1) * gap) // k // g) * g)
    hl = c.t["arrow"]["len_per_stroke"] * c.stroke("connector")
    last = 2 * hl + 3  # the run into a spoke holds two heads
    gy = c.snap(last + 14, up=True)  # last run plus a trunk of at least 14
    heads = "filled" if spec.get("arrows", "none") == "out" else "none"
    wc, hc = min(c.snap(w * 1.25, up=True), int((W - 2 * pad) // g) * g), c.snap(h * 1.25, up=True)  # the hub is a quarter larger
    y_up, y_hub = top + pad, top + pad + h + gy
    y_down = y_hub + hc + gy
    hx0 = c.snap((W - wc) / 2)
    hx = hx0 + wc / 2
    hid = c.node(hx0, y_hub, wc, hc, lines["hub"], group="hub", accent=True, cue="weight", sw="emphasis", icon=spec["hub"].get("icon"))
    for row, y, side in ((up, y_up, -1), (down, y_down, 1)):
        if not row:
            continue
        total = len(row) * w + (len(row) - 1) * gap
        x0 = c.snap((W - total) / 2)
        spots = [(c.node(x0 + i * (w + gap), y, w, h, lines[s["id"]], icon=s.get("icon")), x0 + i * (w + gap) + w / 2) for i, s in enumerate(row)]
        hub_edge = y_hub if side < 0 else y_hub + hc
        spoke_edge = y + h if side < 0 else y
        bar = spoke_edge + side * -last if side > 0 else spoke_edge + last
        bar = spoke_edge + last if side < 0 else spoke_edge - last
        end = spoke_edge + 1 if side < 0 else spoke_edge - 1
        own = min(range(len(spots)), key=lambda i: abs(spots[i][1] - hx))
        for i, (sid, sx) in enumerate(spots):
            pts = [(hx, hub_edge), (hx, bar), (sx, bar), (sx, end)] if i == own else [(hx, bar), (sx, bar), (sx, end)]
            pts = [p for j, p in enumerate(pts) if j == 0 or p != pts[j - 1]]
            c.edge(pts, head=heads, src=hid, dst=sid)
    c.W = W
    c.H = height or ((y_down + h if down else y_hub + hc) + pad)
    return c.svg()
