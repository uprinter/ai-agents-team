"""Cycle: steps around a loop, each joined to the next by a straight arrow, the last back to the first.

Spec: {"type": "cycle", "title", "claim", "steps": [{"label","icon"?,"accent"?}], "return"?: false, "return_label"?: text}
The arrow from the last step back to the first is drawn in the accent colour and heavier; "return": false turns that off,
"return_label" names it beside the arrow.
Four, five, six or eight steps, clockwise from the top left. The loop is a rectangle of boxes: two columns for
four, six and eight, three columns with a gap in the middle of the bottom row for five.
"""
from .prims import Canvas
from .flow import _sizes

# (row, column) of each step, clockwise from the top left
CELLS = {
    4: [(0, 0), (0, 1), (1, 1), (1, 0)],
    5: [(0, 0), (0, 1), (0, 2), (1, 2), (1, 0)],
    6: [(0, 0), (0, 1), (1, 1), (2, 1), (2, 0), (1, 0)],
    8: [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 0), (2, 0), (1, 0)],
}


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad = v["width"], v["pad"]
    steps, n = spec["steps"], len(spec["steps"])
    if n not in CELLS:
        raise ValueError("cycle supports four, five, six or eight steps")
    cells = CELLS[n]
    cols, rows = 1 + max(col for _, col in cells), 1 + max(r for r, _ in cells)
    hl = c.t["arrow"]["len_per_stroke"] * c.stroke("connector")
    run = c.snap(3 * hl + 4, up=True)  # an arrow between boxes is at least three heads
    nodes = [{"id": f"s{i}", **s} for i, s in enumerate(steps)]
    w, h, lines = _sizes(c, nodes, max_w=int((W - 2 * pad - (cols - 1) * run) // cols // g) * g)
    x0 = c.snap((W - (cols * w + (cols - 1) * run)) / 2)
    y0 = top + pad
    runv = run
    if height and rows > 1:  # a fixed frame: the vertical arrows grow, by at most half, to fill it
        runv = min(c.snap(run * 1.5), c.snap(run + (height - 2 * pad - rows * h - (rows - 1) * run) / (rows - 1)))
        runv = max(run, runv)
        y0 = max(top + pad, c.snap((height - (rows * h + (rows - 1) * runv)) / 2))
    pos = [(x0 + col * (w + run), y0 + r * (h + runv)) for r, col in cells]
    ids = [c.node(x, y, w, h, lines[nodes[i]["id"]], accent=steps[i].get("accent", False),
                  cue="weight" if steps[i].get("accent") else None, icon=steps[i].get("icon"),
                  sw="emphasis" if steps[i].get("accent") else "outline") for i, (x, y) in enumerate(pos)]
    for i in range(n):
        (ax, ay), (bx, by) = pos[i], pos[(i + 1) % n]
        if ay == by:  # same row: across
            a, b = ((ax + w, ay + h / 2), (bx - 1, by + h / 2)) if bx > ax else ((ax, ay + h / 2), (bx + w + 1, by + h / 2))
        else:  # same column: down or up
            a, b = ((ax + w / 2, ay + h), (bx + w / 2, by - 1)) if by > ay else ((ax + w / 2, ay), (bx + w / 2, by + h + 1))
        back = i == n - 1 and spec.get("return", True)  # the arrow that closes the loop is the point of a loop
        eid = c.edge([a, b], src=ids[i], dst=ids[(i + 1) % n], accent=back, cue="weight" if back else None, sw="emphasis" if back else "connector")
        if back and spec.get("return_label"):
            c.edge_label([a, b], spec["return_label"], accent=True, eid=eid, size=v["node_font"], bold=True)
    c.W = W
    c.H = height or (y0 + rows * h + (rows - 1) * runv + pad)
    return c.svg()
