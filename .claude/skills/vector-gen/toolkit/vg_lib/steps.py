"""Steps: numbered steps in order, a vertical list or, when it fits, a horizontal timeline.

Spec: {"type": "steps", "title", "claim", "steps": [{"title", "text"?}]}
Each step gets a numbered badge. A list runs top-down with a line joining the badges; a timeline puts the
badges in one row with the title and text under each. The timeline is used when every column is at least
tokens "steps.min_column" wide.
"""
from .prims import Canvas
from .layout import wrap, line_height, baseline


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad, nf, ef = v["width"], v["pad"], v["node_font"], v["edge_font"]
    steps, n = spec["steps"], len(spec["steps"])
    bsz = c.snap(max(24, nf * 2), up=True)
    br = c.radius_for(bsz, bsz)
    lt, lx = line_height(nf), line_height(ef)
    row = (W - 2 * pad) // n >= c.t["steps"]["min_column"]

    def badge(i, x, y):
        bid = c.shape("node", "badge", x, y, bsz, bsz, (br, br, br, br), fill="accent", stroke="accent", group="badges")
        c.text(x + bsz / 2, y + bsz / 2 + nf * 0.36, str(i + 1), nf, 700, "bg", halo=False, role="badge-text", inside=bid, layer="node")

    def lines(i, w):
        s = steps[i]
        return wrap(c, s["title"], nf, w, True), (wrap(c, s["text"], ef, w) if s.get("text") else [])

    def put(i, x, y, tl, xl):
        """Title and text, left aligned at x, first line box at y."""
        for j, s in enumerate(tl):
            c.text(x, baseline(y, nf), s, nf, 700, "ink", anchor="start", halo=False, role="node-text", layer="node", cont=j > 0)
            y += lt
        y += 4 if xl else 0
        for j, s in enumerate(xl):
            c.text(x, baseline(y, ef), s, ef, 400, "muted", anchor="start", halo=False, role="node-text", layer="node", cont=j > 0)
            y += lx

    if row:
        cw = int((W - 2 * pad) // n // g) * g
        x0 = c.snap((W - n * cw) / 2)
        wr = cw - c.snap(12, up=True)
        ps = [lines(i, wr) for i in range(n)]
        y = top + pad
        for i in range(n):
            x = x0 + i * cw
            badge(i, x, y)
            if i < n - 1:
                c.guide(x + bsz + 6, y + bsz / 2, x + cw - 6, y + bsz / 2, dash=None)
            put(i, x, y + bsz + 10, *ps[i])
        body = max(len(t) * lt + ((4 + len(x) * lx) if x else 0) for t, x in ps)
        natural = top + 2 * pad + bsz + 10 + body
    else:
        gt = c.snap(12, up=True)
        wr = W - 2 * pad - bsz - gt
        ps = [lines(i, wr) for i in range(n)]
        used = max(c.tw(s, nf, True) for t, _ in ps for s in t[:1] + t[1:])
        used = max([used] + [c.tw(s, ef) for _, x in ps for s in x])
        bx = max(pad, c.snap((W - (bsz + gt + used)) / 2))  # the list sits centred as one block
        tx = bx + bsz + gt
        first = (bsz - lt) / 2
        rowh = max(max(bsz, first + len(t) * lt + ((4 + len(x) * lx) if x else 0)) for t, x in ps)
        vgap = c.snap(max(12, pad), up=True)
        pitch = c.snap(rowh + vgap, up=True)
        y0 = top + pad
        for i in range(n):
            y = y0 + i * pitch
            badge(i, bx, y)
            if i < n - 1:
                c.guide(bx + bsz / 2, y + bsz + 4, bx + bsz / 2, y + pitch - 4, dash=None)
            put(i, tx, y + first, *ps[i])
        natural = y0 + (n - 1) * pitch + rowh + pad
    c.W, c.H = W, height or natural
    return c.svg()
