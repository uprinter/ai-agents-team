"""Funnel: stages from wide to narrow, centred, each with its name and its value.

Spec: {"type": "funnel", "title", "claim", "stages": [{"label", "value"?, "share"?, "accent"?}]}
A bar is as wide as its "share" (0 to 1, of the first bar); without shares the bars step down evenly to 40%.
The name sits at the left of its bar and the value at the right; a bar too narrow for both carries the value just outside.
A stage may carry "drop" (for example "-92%"): the loss from the stage above, set in the accent colour between the two bars.
Shares are a drawing choice, not data: the values and the drop carry the numbers.
"""
from .prims import Canvas
from .layout import baseline


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad, nf = v["width"], v["pad"], v["node_font"]
    st, n = spec["stages"], len(spec["stages"])
    if n < 3:
        raise ValueError("a funnel needs at least three stages")
    wmax = int((W - 2 * pad) // g) * g
    inpad = c.snap(max(8, pad * 0.75), up=True)
    drops = any(s.get("drop") for s in st)
    ef = v["edge_font"]
    gap = c.snap(max(6, v["gap"] // 2), up=True)
    if drops:
        gap = c.snap(ef + 12, up=True)  # the gap holds the loss between two bars
    bh = c.snap(nf * 2.6, up=True)
    if height:  # a fixed frame: the bars grow, by at most 60%, to fill it
        grown = int((height - 2 * pad - (n - 1) * gap) // n // g) * g
        bh = max(bh, min(grown, c.snap(bh * 1.6, up=True)))
        top = max(0, c.snap((height - (n * bh + (n - 1) * gap)) / 2 - pad))
    r = c.radius_for(wmax, bh)
    y = top + pad
    for i, s in enumerate(st):
        share = s.get("share", 1 - i * 0.6 / (n - 1))
        w = int(max(0.2, min(1, share)) * wmax // g) * g
        x = c.snap((W - w) / 2)
        vw = c.tw(s["value"], nf, True) if s.get("value") else 0
        need = c.tw(s["label"], nf, True) + (vw + inpad if vw else 0) + 2 * inpad
        outside = need > w  # a bar too narrow for its value carries the value just outside its right end
        if outside and (c.tw(s["label"], nf, True) + 2 * inpad > w or x + w + inpad + vw > W - pad):
            raise ValueError(f"stage '{s['label']}' needs {need:.0f}px, its bar is {w}px; shorten the text or raise its share")
        acc = s.get("accent", False)
        if s.get("drop") and i:
            c.text(W / 2, y - gap / 2 + ef * 0.345, s["drop"], ef, 700, "accent", halo=False, role="stage-drop")
        sid = c.shape("node", "node", x, y, w, bh, (r, r, r, r), fill="surface", stroke="accent" if acc else "hair",
                      sw="emphasis" if acc else "outline", group=f"funnel-{i}", accent=acc, cue="weight")
        c.text(x + inpad, y + bh / 2 + nf * 0.345, s["label"], nf, 700, "ink", anchor="start", halo=False, role="node-text", inside=sid, layer="node")
        if s.get("value") and not outside:
            c.text(x + w - inpad, y + bh / 2 + nf * 0.345, s["value"], nf, 700, "accent" if acc else "ink", anchor="end", halo=False, role="node-text", inside=sid, layer="node")
        elif s.get("value"):
            c.text(x + w + inpad, y + bh / 2 + nf * 0.345, s["value"], nf, 700, "accent" if acc else "ink", anchor="start", halo=False, role="stage-value")
        y += bh + gap
    c.W = W
    c.H = height or (y - gap + pad)
    return c.svg()
