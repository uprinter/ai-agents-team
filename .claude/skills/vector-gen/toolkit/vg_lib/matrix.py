"""Matrix: a two by two grid with a named axis each way, for sorting things by two measures.

Spec: {"type": "matrix", "title", "claim", "x": "Effort", "y": "Impact",
       "cells": [top left, top right, bottom left, bottom right],   each {"title", "text"?, "accent"?}}
Each axis is an arrow pointing to "more": the y arrow on the left, the x arrow under the grid, the axis name at its head.
"""
from .prims import Canvas
from .layout import wrap, line_height, baseline


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad, nf, ef = v["width"], v["pad"], v["node_font"], v["edge_font"]
    cells = spec["cells"]
    if len(cells) != 4:
        raise ValueError("matrix needs four cells: top left, top right, bottom left, bottom right")
    gap = c.snap(max(8, v["gap"]), up=True)
    gl = c.snap(20, up=True)  # room for the y arrow
    edge = max(pad, v.get("text_margin", 0))
    x0 = edge + gl
    cw = int(((W - edge - x0) - gap) // 2 // g) * g
    lt, lx = line_height(nf), line_height(ef)
    inner = cw - 2 * pad
    if inner < c.t["cards"]["min_text"]:
        raise ValueError(f"matrix cell text is {inner}px wide in variant {c.vname}, under {c.t['cards']['min_text']}px; use a smaller type step")
    parts = [(wrap(c, x["title"], nf, inner, True), wrap(c, x["text"], ef, inner) if x.get("text") else []) for x in cells]
    body = max(len(t) * lt + ((4 + len(x) * lx) if x else 0) for t, x in parts)
    ch = c.snap(2 * pad + body, up=True)
    dy = 0
    head = pad + line_height(ef) + 8 + g  # the y name above the grid
    foot = gl / 2 + ef + 10 + pad  # the x arrow and its name below it
    if height:  # a fixed frame: the cells grow, by at most half, to fill it, with their content centred
        grown = min(int((height - head - foot - gap) // 2 // g) * g, c.snap(ch * 1.5, up=True))
        if grown > ch:
            dy = (grown - ch) / 2
            ch = grown
        top = max(0, c.snap((height - (head + 2 * ch + gap + foot)) / 2))
    ytop = c.snap(top + pad + line_height(ef) + 8, up=True)  # the y name sits above the grid
    r = c.radius_for(cw, ch)
    for i, card in enumerate(cells):
        x, y = x0 + (i % 2) * (cw + gap), ytop + (i // 2) * (ch + gap)
        acc = card.get("accent", False)
        cid = c.shape("node", "node", x, y, cw, ch, (r, r, r, r), fill="surface", stroke="accent" if acc else "hair",
                      sw="emphasis" if acc else "outline", group=f"matrix-{i // 2}", accent=acc, cue="weight")
        cy = y + pad + dy
        t, b = parts[i]
        for j, s in enumerate(t):
            c.text(x + pad, baseline(cy, nf), s, nf, 700, "ink", anchor="start", halo=False, role="node-text", inside=cid, layer="node", cont=j > 0)
            cy += lt
        cy += 4 if b else 0
        for j, s in enumerate(b):
            c.text(x + pad, baseline(cy, ef), s, ef, 400, "muted", anchor="start", halo=False, role="node-text", inside=cid, layer="node", cont=j > 0)
            cy += lx
    gh = 2 * ch + gap
    ybot = ytop + gh
    ax = edge + gl / 2
    c.edge([(ax, ybot), (ax, ytop)], color="muted")  # y arrow, up
    c.text(edge, ytop - 8, spec.get("y_label", "More " + spec["y"].lower()), ef, 700, "ink", anchor="start", halo=False, role="axis-label")
    ay = ybot + gl / 2  # the same distance from the grid as the y arrow
    c.edge([(x0, ay), (x0 + 2 * cw + gap, ay)], color="muted")  # x arrow, right
    c.text(x0 + 2 * cw + gap, ay + ef + 10, spec.get("x_label", "More " + spec["x"].lower()), ef, 700, "ink", anchor="end", halo=False, role="axis-label")
    c.W = W
    c.H = height or (ay + ef + 10 + pad)
    return c.svg()
