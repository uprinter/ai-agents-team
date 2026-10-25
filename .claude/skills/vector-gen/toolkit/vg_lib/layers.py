"""Layers: a stack of layers, top to bottom, grouped into tinted containers, one tone per group.

Spec: {"type": "layers", "title", "claim",
       "groups": [{"label", "tone": "warm" | "cool", "icon"?: "brand:SLUG" | "NAME",
                   "layers": [{"title", "text"?, "step"?, "base"?}   a bar: a layer with its name, a short caption and a step number
                                                       (give every bar a step or none); "base" marks the layer everything
                                                       rests on with a heavier tone outline and a tone number
                              | {"chips": ["Name" | {"label", "href"}, ...]}   modules on one level, in a grid]}]}
Groups and layers are listed in the order they are drawn, top first, so the layer everything rests on is last.
Two tones keep two kinds of layer apart (a platform and the system on top of it): "warm" and "cool" are colour
tokens (`warm`, `warm_fill`, `cool`, `cool_fill`). A group's icon sits at the right end of its header, in the
tone colour. Bars share one height across the figure; chips share one size within a layer and fill the width
in the most even grid (nine chips make three by three, not five and four). A short arrow with a label (spec "runs_on", default "Runs on";
"" for none) joins each group to the one below it, so the stack reads as one thing. A caption sits beside its name in an
aligned column when every bar fits that way, else under it. The build refuses a layer where some chips wrap to two
lines and others do not. A chip with an "href" is a link: its name is underlined and only the name is the <a>, never the box.
Links work only when the SVG is inline in the page (an <img> shows the drawing without them), so such a figure is
a group of links (role "group", its name from the claim, no <title>, which browsers show as a hover tip on every part) and its ids carry the variant name, to stay unique when
all four variants are inline at once. No feed image: set "no_social".
"""
from .prims import Canvas
from .layout import wrap, line_height, baseline


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad, nf, ef, tf = v["width"], v["pad"], v["node_font"], v["edge_font"], v["title_font"]
    groups = spec["groups"]
    # a chip is a name or {"label", "href"}: a chip with an href is a link, its name underlined
    for gr in groups:
        for ly in gr["layers"]:
            if "chips" in ly:
                ly["chips"] = [{"label": x} if isinstance(x, str) else x for x in ly["chips"]]
                c.links = c.links or any(x.get("href") for x in ly["chips"])
    for gr in groups:
        if gr.get("tone") not in ("warm", "cool"):
            raise ValueError(f"group '{gr.get('label')}': tone must be 'warm' or 'cool'")
    m = c.snap(2, up=True)                            # canvas margin: just the outline, so the figure is flush with its column
    bp = c.snap(max(8, pad * 0.75), up=True)          # padding inside a bar
    ip = bp                                           # padding inside a group container, the same as in its bars
    cp = c.snap(max(5, pad * 0.4), up=True)           # padding inside a chip
    lg = c.snap(max(6, v["gap"] // 2), up=True)       # gap between layers of one group
    hl = c.t["arrow"]["len_per_stroke"] * c.stroke("connector")
    gg = c.snap(max(2 * lg + 4, 3 * hl + 8), up=True)  # gap between groups: holds the "runs on" arrow, three heads long
    cg = c.snap(max(6, v["gap"] // 2), up=True)       # gap between chips
    iw = int((W - 2 * m - 2 * ip) // g) * g           # inner width of a container
    lt, lx = line_height(nf), line_height(ef)

    # bars: one height for all, from the tallest title + caption
    bars = [l for gr in groups for l in gr["layers"] if "chips" not in l]
    if any(l.get("step") for l in bars) and not all(l.get("step") for l in bars):
        raise ValueError("some bars carry a step number and some do not; number every bar or none")
    ncol = (max(c.tw(l["step"], nf, True) for l in bars) + bp) if bars and all(l.get("step") for l in bars) else 0
    bar_inner = iw - 2 * bp - ncol

    def bar_lines(l):
        t = wrap(c, l["title"], nf, bar_inner, True)
        x = wrap(c, l["text"], ef, bar_inner) if l.get("text") else []
        return t, x

    # inline: name and caption share one line, captions aligned in a column, when every bar fits that way
    tcol = max((c.tw(l["title"], nf, True) for l in bars), default=0)
    inline = bool(bars) and all(l.get("text") for l in bars) and \
        tcol + 2 * bp + max(c.tw(l["text"], nf) for l in bars) <= bar_inner
    cf = nf if inline else ef                         # caption size: as large as the name when they share a line

    def bar_block(l):
        if inline:
            return lt
        t, x = bar_lines(l)
        return len(t) * lt + ((3 + len(x) * lx) if x else 0)

    bar_h = c.snap(2 * bp + max(bar_block(l) for l in bars), up=True) if bars else 0

    def chip_grid(l):
        n = len(l["chips"])

        def cw(k):
            return int((iw - (k - 1) * cg) // k // g) * g

        feasible = [k for k in range(1, n + 1) if cw(k) - 2 * cp >= c.t["layers"]["min_text"]] or [1]
        even = [k for k in feasible if n % k == 0 and k > 1]
        k = max(even) if even else max(feasible, key=lambda k: ((n % k or k) / k >= 0.6, k))
        w = cw(k)
        lines = [wrap(c, s, nf, w - 2 * cp) for s in [x["label"] for x in l["chips"]]]
        two = [s["label"] for s, x in zip(l["chips"], lines) if len(x) > 1]
        if two and len(two) < n:
            raise ValueError(f"chips {', '.join(two)} wrap to two lines and the others do not, in variant {c.vname}; shorten the labels so all fit one line")
        h = c.snap(2 * cp + (max(len(x) for x in lines) - 1) * (nf + 3) + nf * 1.14 + cp, up=True)
        return k, w, h, lines

    grids = {id(l): chip_grid(l) for gr in groups for l in gr["layers"] if "chips" in l}

    def layer_h(l):
        if "chips" not in l:
            return bar_h
        k, w, h, lines = grids[id(l)]
        rows = -(-len(l["chips"]) // k)
        return rows * h + (rows - 1) * cg

    hh = c.snap(max(line_height(tf), v["icon"] if any(gr.get("icon") for gr in groups) else 0), up=True)  # header row
    y = top + m
    for gi, gr in enumerate(groups):
        tone = gr["tone"]
        body = sum(layer_h(l) for l in gr["layers"]) + (len(gr["layers"]) - 1) * lg
        gh = c.snap(ip + hh + ip + body + ip, up=True)
        gx = m
        r = c.radius_for(W - 2 * m, gh)
        cid = c.shape("container", "group", gx, y, W - 2 * m, gh, (r, r, r, r), fill=f"{tone}_fill", stroke=tone,
                      sw="outline", group=None)
        hy = y + ip
        c.text(gx + ip, hy + hh / 2 + tf * 0.345, gr["label"], tf, 700, "ink", anchor="start", halo=False,
               role="group-label", inside=cid, layer="node")
        if gr.get("icon"):
            isz = v["icon"]
            c.icon(gr["icon"], gx + (W - 2 * m) - ip - isz, c.snap(hy + (hh - isz) / 2), isz, fill=tone,
                   group="group-icons", inside=cid)
        ly = hy + hh + ip
        for li, l in enumerate(gr["layers"]):
            if "chips" in l:
                k, w, h, lines = grids[id(l)]
                n = len(l["chips"])
                for i, s in enumerate(lines):
                    row, col = divmod(i, k)
                    cx = gx + ip + col * (w + cg)
                    href = l["chips"][i].get("href")
                    c.node(cx, ly + row * (h + cg), w, h, s, group=f"chips-{gi}-{li}", size=nf, underline=bool(href), href=href)
                ly += layer_h(l) + lg
            else:
                t, x = bar_lines(l)
                base = bool(l.get("base"))                # the layer everything rests on: tone outline and tone number
                bid = c.shape("node", "node", gx + ip, ly, iw, bar_h, (c.radius_for(iw, bar_h),) * 4, fill="surface",
                              stroke=tone if base else "hair", sw="emphasis" if base else "outline", group="bars")
                cy = ly + (bar_h - bar_block(l)) / 2
                tx = gx + ip + bp + ncol
                if ncol:
                    c.text(gx + ip + bp, ly + bar_h / 2 + nf * 0.345 if inline else baseline(cy, nf), l["step"], nf, 700, tone if base else "muted",
                           anchor="start", halo=False, role="node-text", inside=bid, layer="node")
                if inline:
                    base = ly + bar_h / 2 + nf * 0.345
                    c.text(tx, base, l["title"], nf, 700, "ink", anchor="start", halo=False,
                           role="node-text", inside=bid, layer="node")
                    c.text(tx + tcol + 2 * bp, base, l["text"], cf, 400, "muted", anchor="start", halo=False,
                           role="node-text", inside=bid, layer="node")
                    ly += bar_h + lg
                    continue
                for j, s in enumerate(t):
                    c.text(tx, baseline(cy, nf), s, nf, 700, "ink", anchor="start", halo=False,
                           role="node-text", inside=bid, layer="node", cont=j > 0)
                    cy += lt
                if x:
                    cy += 3
                for j, s in enumerate(x):
                    c.text(tx, baseline(cy, ef), s, ef, 400, "muted", anchor="start", halo=False,
                           role="node-text", inside=bid, layer="node", cont=j > 0)
                    cy += lx
                ly += bar_h + lg
        if gi < len(groups) - 1 and spec.get("runs_on", "Runs on"):  # the group above rests on the group below
            pts = [(W / 2, y + gh + 2), (W / 2, y + gh + gg - 2)]
            eid = c.edge(pts, color="muted")
            c.edge_label(pts, spec.get("runs_on", "Runs on"), eid=eid)
        y += gh + gg
    c.W = W
    c.H = y - gg + m
    return c.svg()
