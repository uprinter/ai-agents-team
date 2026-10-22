"""Before/after comparison: the same flow drawn once per panel on one shared layout, changes marked by more than colour.

Spec: {"type": "compare", "title", "claim",
       "panels": [{"label", "nodes": [...], "edges": [...], "groups"?: [...]}]}
A node or edge may carry "delta": "add" | "remove". add -> accent + heavy outline; remove -> dashed + dimmed.
An edge may carry "async": true -> open arrowhead (sender does not wait); other edges keep the filled head.
The key under the figure is generated from the encodings the figure uses, so it never promises a mark that is absent.
A node with the same id sits at the same place in every panel.
"""
from .prims import Canvas
from . import flow


def _mark(items, used):
    out = []
    for it in items:
        it = dict(it)
        d = it.pop("delta", None)
        if d == "add":
            it["accent"] = True
        elif d == "remove":
            it["dashed"] = True
            it["dim"] = True
        if d:
            used.add(d)
        if it.get("async"):
            used.add("async")
        out.append(it)
    return out


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v = c.v
    pad, tf, ef = v["pad"], v["title_font"], v["edge_font"]
    used = set()
    panels = [{"label": p["label"], "nodes": _mark(p["nodes"], used), "edges": _mark(p["edges"], used),
               "groups": p.get("groups", [])} for p in spec["panels"]]
    pl = flow.plan(c, panels, v["width"], mode=v.get("compare_mode"))
    y, right = top, 0
    for i, p in enumerate(panels):
        if i:
            c.guide(pad, y, max(right, v["width"] if pl["mode"] == "tb" else right) - pad, y, dash=None)
        c.text(pad, y + pad + tf, p["label"], tf, 700, "ink", anchor="start", halo=False, role="title")
        r, y = flow.draw(c, p, 0, y + pad + tf + 8, pl)
        right = max(right, r)
    key = [t for d, t in (("add", "Blue, heavy outline = added"), ("remove", "Dashed = removed"), ("async", "Open arrowhead = sender does not wait")) if d in used]
    if key:
        one = "; ".join([key[0]] + [t[0].lower() + t[1:] for t in key[1:]])
        rows = [one] if c.tw(one, ef) <= right - 2 * pad else key  # one entry per line when the key does not fit the figure
        right = max(right, max(c.tw(t, ef) for t in rows) + 2 * pad)
        for k, t in enumerate(rows):
            c.text(pad, y + ef + k * (ef + 4), t, ef, 400, "muted", anchor="start", halo=False, role="key")
        y += ef + (len(rows) - 1) * (ef + 4) + pad
    c.W, c.H = right, height or y
    return c.svg()
