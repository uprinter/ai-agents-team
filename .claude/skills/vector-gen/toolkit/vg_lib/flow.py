"""Flow diagram: boxes in layers joined by orthogonal arrows. Left-to-right when it fits, top-down when not.

Spec: {"type": "flow", "title", "claim",
       "nodes": [{"id","label","icon"?,"accent"?,"dashed"?,"dim"?}],   icon = name from icons/lucide.json (all nodes or none)
       "edges": [{"from","to","label"?,"accent"?,"dashed"?,"async"?,"back"?}],   back: true = a return to an earlier box, drawn outside (dashed by default)
       "groups": [{"label","nodes":[ids]}]?}
Layer = longest path from a source. An edge may span layers only when its route is a straight line;
a back edge is marked "back": true and runs outside the figure; bent skip edges raise with advice.

Routing rules (craft-rules.md): a fork (one source, several targets) and a join (several sources, one target)
run on a bus: one trunk from the middle of the box, one bar, a straight run into the middle of each other box;
a join ends in one head. A fork and a join may not share the same two layers. An edge that is both part of a
fork and part of a join, or a single edge, keeps its own ports spread along the box side and a bend two heads
before the target. The label rides the run into the box (fork) or out of it (join): above a horizontal run,
on the outer side of a vertical one.
"""
from .prims import Canvas
from .sequence import wrap_lines


def _layers(nodes, edges):
    ids = [n["id"] for n in nodes]
    preds = {i: [e["from"] for e in edges if e["to"] == i] for i in ids}
    memo, stack = {}, set()

    def depth(i):
        if i in memo:
            return memo[i]
        if i in stack:
            raise ValueError(f"cycle through '{i}': flow diagrams need a DAG; draw the loop as a labelled return edge in a sequence diagram")
        stack.add(i)
        memo[i] = 0 if not preds[i] else 1 + max(depth(p) for p in preds[i])
        stack.discard(i)
        return memo[i]

    return {i: depth(i) for i in ids}


def _sizes(c, nodes, max_w=None):
    """One shared box size: wide enough for the longest label, two lines only when max_w forces it."""
    nf, g = c.v["node_font"], c.v["grid"]
    padx = max(c.snap(nf * 0.9, up=True), 2)
    longest = max(c.tw(n["label"], nf) for n in nodes)
    lines = {n["id"]: [n["label"]] for n in nodes}
    w = c.snap(longest + 2 * padx, up=True)
    if max_w is not None and w > max_w:
        w = int(max_w // g) * g
        lines = {n["id"]: wrap_lines(c, n["label"], nf, w - 2 * padx) for n in nodes}
    nl = max(len(x) for x in lines.values())
    icons = [bool(n.get("icon")) for n in nodes]
    if any(icons) and not all(icons):
        raise ValueError("some nodes have an icon and some do not; give every node an icon or none")
    extra = c.v["icon"] + c.icon_gap() if all(icons) else 0
    h = c.snap(nl * nf + (nl - 1) * 3 + 2 * nf + extra, up=True)
    return w, h, lines


def plan(c, panels, avail_w, mode=None):
    """Shared layout for one or more flows: same ids land on the same layer, so panels line up."""
    v, g, pad, ef = c.v, c.v["grid"], c.v["pad"], c.v["edge_font"]
    panels = [{**p, "edges": [e for e in p["edges"] if not e.get("back")]} for p in panels]  # back edges do not take part in the layering
    layer, nodes = {}, {}
    for p in panels:
        for i, d in _layers(p["nodes"], p["edges"]).items():
            layer[i] = max(layer.get(i, 0), d)
        for n in p["nodes"]:
            nodes.setdefault(n["id"], n)
    for p in panels:
        for e in p["edges"]:
            if layer[e["to"]] <= layer[e["from"]]:
                raise ValueError(f"edge {e['from']}->{e['to']} points backwards or sideways; back edges are not supported")
    nl = max(layer.values()) + 1
    lw = [0.0] * nl
    for p in panels:
        for e in p["edges"]:
            if layer[e["to"]] - layer[e["from"]] == 1 and e.get("label"):
                lw[layer[e["from"]]] = max(lw[layer[e["from"]]], c.tw(e["label"], ef))
    per = [[sum(layer[n["id"]] == k for n in p["nodes"]) for k in range(nl)] for p in panels]
    tall = max(max(r) for r in per)
    w, h, lines = _sizes(c, list(nodes.values()))
    hl0, lc = c.t["arrow"]["len_per_stroke"] * c.stroke("connector"), v.get("label_clear", 5)
    forky = any(sum(e["from"] == n for e in p["edges"]) > 1 or sum(e["to"] == n for e in p["edges"]) > 1 for p in panels for n in (x["id"] for x in p["nodes"]))
    gx = [c.snap(max(48, lw[k] + 2 * lc + 2 * hl0 + 10, 4 * hl0 + 3 if forky else 0), up=True) for k in range(nl - 1)]  # label, bus and a last run of two heads
    need = 2 * pad + nl * w + sum(gx)
    mode = mode or v.get("mode", "auto")
    if mode == "auto":
        mode = "lr" if need <= avail_w else "tb"
    if mode == "lr" and need > avail_w:
        raise ValueError(f"variant {c.vname}: left-to-right needs {need}px, only {avail_w} available")
    if mode == "tb":
        gap_h = c.snap(max(8, v.get("row_gap", v["gap"])), up=True)
        room = avail_w - 2 * pad - (tall - 1) * gap_h
        w, h, lines = _sizes(c, list(nodes.values()), max_w=int(room // tall // g) * g)
        if tall * w + (tall - 1) * gap_h + 2 * pad > avail_w:
            raise ValueError(f"variant {c.vname}: {tall} boxes in a row do not fit {avail_w}px")
        labelled = any(e.get("label") for p in panels for e in p["edges"])
        run = max(2 * hl0 + 2, ef + 2 * lc) if labelled else 2 * hl0 + 2  # a labelled run holds the label with lc clear each side
        bus = run + 1 + 2 * hl0 + 2 if forky else 0  # labelled run, bus, a last run of two heads
        gy = [c.snap(max(48, ef + 24, 2 * hl0 + ef + 1 + 2 * lc, bus), up=True)] * (nl - 1)
        return dict(layer=layer, nodes=nodes, w=w, h=h, lines=lines, mode="tb", gap_h=gap_h, gy=gy, tall=tall, nl=nl, avail=avail_w, need=avail_w)
    return dict(layer=layer, nodes=nodes, w=w, h=h, lines=lines, mode="lr", gx=gx, tall=tall, nl=nl, avail=avail_w, need=need)


def draw(c, spec, x0, y0, pl):
    """Draw one flow into canvas c at (x0, y0) using plan pl. Returns (right, bottom)."""
    v, pad, ef = c.v, c.v["pad"], c.v["edge_font"]
    w, h, lines, layer, mode = pl["w"], pl["h"], pl["lines"], pl["layer"], pl["mode"]
    nodes = spec["nodes"]
    edges = [e for e in spec["edges"] if not e.get("back")]
    backs = [e for e in spec["edges"] if e.get("back")]
    cols = [[n for n in nodes if layer[n["id"]] == k] for k in range(pl["nl"])]
    pos = {}
    if mode == "lr":
        gx, row_gap = pl["gx"], c.snap(24, up=True)
        full = pl["tall"] * h + (pl["tall"] - 1) * row_gap
        xk = x0 + pad
        for k, col in enumerate(cols):
            col_h = len(col) * h + (len(col) - 1) * row_gap
            yk = y0 + pad + c.snap((full - col_h) / 2)
            for j, n in enumerate(col):
                pos[n["id"]] = (xk, yk + j * (h + row_gap))
            xk += w + (gx[k] if k < pl["nl"] - 1 else 0)
        right, bottom = x0 + pl["need"], y0 + pad + full + pad
    else:
        gy, gap_h = pl["gy"], pl["gap_h"]
        yk = y0 + pad
        for k, col in enumerate(cols):
            row_w = len(col) * w + (len(col) - 1) * gap_h
            xk = x0 + pad + c.snap((pl["avail"] - 2 * pad - row_w) / 2)
            for j, n in enumerate(col):
                pos[n["id"]] = (xk + j * (w + gap_h), yk)
            yk += h + (gy[k] if k < pl["nl"] - 1 else 0)
        right, bottom = x0 + pl["avail"], yk + pad

    for gr in spec.get("groups", []):
        xs = [pos[i][0] for i in gr["nodes"]]; ys = [pos[i][1] for i in gr["nodes"]]
        gp, head = c.snap(12, up=True), c.snap(ef + 12, up=True)
        gx0, gy0 = min(xs) - gp, min(ys) - gp - head
        r = c.t["radius"]["m"]
        c.shape("container", "group", gx0, gy0, max(xs) + w + gp - gx0, max(ys) + h + gp - gy0, (r, r, r, r),
                stroke="muted", dash="3 4", snap=False)
        c.text(gx0 + gp, gy0 + gp + ef * 0.8, gr["label"], ef, 700, "muted", anchor="start", halo=False,
               role="group-label", layer="container")

    ids = {}
    for n in nodes:
        x, y = pos[n["id"]]
        cue = "dash" if n.get("dashed") else ("weight" if n.get("accent") else None)
        ids[n["id"]] = c.node(x, y, w, h, lines[n["id"]], accent=n.get("accent", False), cue=cue,
                              dashed=n.get("dashed", False), dim=n.get("dim", False), icon=n.get("icon"),
                              sw="emphasis" if n.get("accent") else "outline")

    # ports: each edge owns one point on the source side and one on the target side, spread evenly
    cross = (lambda i: pos[i][1]) if mode == "lr" else (lambda i: pos[i][0])
    side = h if mode == "lr" else w
    outs = {n["id"]: sorted([e for e in edges if e["from"] == n["id"]], key=lambda e: cross(e["to"])) for n in nodes}
    ins = {n["id"]: sorted([e for e in edges if e["to"] == n["id"]], key=lambda e: cross(e["from"])) for n in nodes}

    hl = c.t["arrow"]["len_per_stroke"] * c.stroke("connector")
    hw = 2 * c.t["arrow"]["half_width_ratio"] * c.t["arrow"]["len_per_stroke"] * c.stroke("connector")

    def port(lst, e):
        """Ports span two thirds of the box side; neighbours stay three head widths apart (and a label height apart in rows)."""
        m = len(lst)
        if m == 1:
            return 0
        need = max(3 * hw, ef + 8 if mode == "lr" and any(x.get("label") for x in lst) else 0)
        pg = min(v.get("port_gap", 40), (2 * side / 3) / (m - 1))
        if pg < need:
            raise ValueError(f"{m} edges on one box side do not fit {need:.0f}px apart; merge them or enlarge the box")
        return (lst.index(e) - (m - 1) / 2) * pg

    # forks and joins run on a bus: one trunk, one bar, a straight run into each centre
    lc = v.get("label_clear", 5)

    def ext(i):
        x, y = pos[i]
        return (x, x + w, y + h / 2) if mode == "lr" else (y, y + h, x + w / 2)

    def P(a, k):
        return (a, k) if mode == "lr" else (k, a)

    def room(es):
        """Room along the flow that a run needs: the two heads, or the label when the run carries one."""
        labs = [c.tw(x["label"], ef) for x in es if x.get("label")]
        return max(2 * hl + 2, (max(labs) + 2 * lc + 6) if mode == "lr" else ef + 2 * lc) if labs else 2 * hl + 2

    def dedupe(pts):
        out = [pts[0]]
        for q in pts[1:]:
            if q != out[-1]:
                out.append(q)
        return out

    bus_fork = {s: [e for e in outs[s] if len(ins[e["to"]]) == 1 and layer[e["to"]] - layer[s] == 1] for s in outs}
    bus_join = {d: [e for e in ins[d] if len(outs[e["from"]]) == 1 and layer[d] - layer[e["from"]] == 1] for d in ins}
    bus_fork = {s: es for s, es in bus_fork.items() if len(es) > 1}
    bus_join = {d: es for d, es in bus_join.items() if len(es) > 1}
    clash = {layer[s] for s in bus_fork} & {layer[d] - 1 for d in bus_join}
    if clash:
        raise ValueError(f"a fork and a join sit between the same two layers ({sorted(clash)[0]} and the next); add a node between them")
    owner = {}
    for s, es in bus_fork.items():
        o = min(es, key=lambda x: (ext(x["to"])[2] != ext(s)[2], bool(x.get("dashed")), not x.get("accent"), edges.index(x)))
        owner[id(o)] = ("fork", s)
    for d, es in bus_join.items():
        o = min(es, key=lambda x: (ext(x["from"])[2] != ext(d)[2], not x.get("accent"), bool(x.get("dashed")), edges.index(x)))
        owner[id(o)] = ("join", d)

    for e in edges:
        s_, d_ = e["from"], e["to"]
        fk, jn = e in bus_fork.get(s_, []), e in bus_join.get(d_, [])
        if fk or jn:
            s_lo, s_hi, s_k = ext(s_)
            d_lo, d_hi, d_k = ext(d_)
            acc = e.get("accent", False)
            cue = "dash" if e.get("dashed") else ("label" if acc else None)
            if fk:
                bar = d_lo - 1 - room(bus_fork[s_])
                if bar - s_hi < 10:
                    raise ValueError(f"fork from '{s_}': the trunk is {bar - s_hi:.0f}px; add space between the layers")
                J, K, end = P(bar, s_k), P(bar, d_k), P(d_lo - 1, d_k)
                pts = dedupe([P(s_hi, s_k), J, K, end]) if owner.get(id(e)) else dedupe([J, K, end])
                head, seg = "open" if e.get("async") else "filled", len(pts) - 2
                side = -1 if d_k < s_k else 1
            else:
                bar = s_hi + room(bus_join[d_])
                if d_lo - 1 - bar < 2 * hl - 0.5:
                    raise ValueError(f"join into '{d_}': the last run is {d_lo - 1 - bar:.0f}px, shorter than two heads; add space between the layers")
                first = owner.get(id(e))
                pts = dedupe([P(s_hi, s_k), P(bar, s_k), P(bar, d_k)] + ([P(d_lo - 1, d_k)] if first else []))
                head, seg = ("open" if e.get("async") else "filled") if first else "none", 0
                side = -1 if s_k < d_k else 1
            eid = c.edge(pts, dashed=e.get("dashed", False), accent=acc, head=head, cue=cue, src=ids[s_], dst=ids[d_])
            if e.get("label"):
                c.edge_label(pts, e["label"], accent=acc, eid=eid, seg=seg, side=side)
            continue
        (sx, sy), (dx, dy) = pos[e["from"]], pos[e["to"]]
        oa, ob = port(outs[e["from"]], e), port(ins[e["to"]], e)
        # bent edges that approach from the same side share a channel zone: the farthest source bends lowest, one step of 8px each
        same = sorted([x for x in ins[e["to"]] if cross(x["from"]) != cross(x["to"])
                       and (cross(x["from"]) < cross(x["to"])) == (cross(e["from"]) < cross(e["to"]))],
                      key=lambda x: -abs(cross(x["from"]) - cross(x["to"])))
        j = same.index(e) if cross(e["from"]) != cross(e["to"]) else 0
        if mode == "lr":
            a, b = (sx + w, sy + h / 2 + oa), (dx - 1, dy + h / 2 + ob)
            ch = dx - 1 - 2 * hl - j * 8
            pts = [a, b] if a[1] == b[1] else [a, (ch, a[1]), (ch, b[1]), b]
        else:
            a, b = (sx + w / 2 + oa, sy + h), (dx + w / 2 + ob, dy - 1)
            ch = dy - 1 - 2 * hl - j * 8
            pts = [a, b] if a[0] == b[0] else [a, (a[0], ch), (b[0], ch), b]
        if layer[e["to"]] - layer[e["from"]] > 1 and len(pts) > 2:
            raise ValueError(f"edge {e['from']}->{e['to']} skips a layer with a bend; add an intermediate node or align the boxes")
        acc = e.get("accent", False)
        eid = c.edge(pts, dashed=e.get("dashed", False), accent=acc, head="open" if e.get("async") else "filled",
                     cue="dash" if e.get("dashed") else ("label" if acc else None), src=ids[e["from"]], dst=ids[e["to"]])
        if e.get("label"):
            # top-down: the label sits on the outer side of the line, so a fork and its join mirror each other
            sib = outs[e["from"]] if len(outs[e["from"]]) > 1 else ins[e["to"]]
            c.edge_label(pts, e["label"], accent=acc, eid=eid, seg=0, side=-1 if (mode == "tb" and len(sib) > 1 and sib[0] is e) else 1)
    for k, e in enumerate(backs):
        _back_edge(c, e, k, pos, ids, w, h, mode, ef)
    return right, bottom


def back_room(c, spec):
    """Room the back edges need outside the figure: one lane each plus the widest label (or its height)."""
    backs = [e for e in spec["edges"] if e.get("back")]
    if not backs:
        return 0, 0
    lanes = 30 + 14 * len(backs)  # the first lane is two heads and a margin from the boxes, the next ones 14px apart
    label = max((c.tw(e["label"], c.v["edge_font"]) + 12 for e in backs if e.get("label")), default=0)
    return lanes + label, lanes + c.v["edge_font"] + 8


def _back_edge(c, e, k, pos, ids, w, h, mode, ef):
    """A back edge runs outside the figure: down the right side in a top-down flow, along the bottom in a left-to-right one,
    and enters the earlier box from outside. It may not cross another box."""
    (sx, sy), (dx, dy) = pos[e["from"]], pos[e["to"]]
    if mode == "tb":
        xg = max(x + w for x, _ in pos.values()) + 30 + 14 * k
        pts = [(sx + w, sy + h / 2), (xg, sy + h / 2), (xg, dy + h / 2), (dx + w + 1, dy + h / 2)]
    else:
        yg = max(y + h for _, y in pos.values()) + 30 + 14 * k
        pts = [(sx + w / 2, sy + h), (sx + w / 2, yg), (dx + w / 2, yg), (dx + w / 2, dy + h + 1)]
    for name, (x, y) in pos.items():
        if name in (e["from"], e["to"]):
            continue
        for a, b in zip(pts, pts[1:]):
            if min(a[0], b[0]) < x + w and max(a[0], b[0]) > x and min(a[1], b[1]) < y + h and max(a[1], b[1]) > y:
                raise ValueError(f"back edge {e['from']}->{e['to']} would cross box '{name}'; put the two boxes where nothing lies between them and the outside")
    acc = e.get("accent", False)
    eid = c.edge(pts, dashed=e.get("dashed", True), accent=acc, cue="label" if acc else ("dash" if e.get("dashed", True) else None),
                 src=ids[e["from"]], dst=ids[e["to"]], head="open" if e.get("async") else "filled")
    if e.get("label"):
        if mode == "tb":
            c.edge_label(pts, e["label"], accent=acc, eid=eid, seg=1, side=1)
        else:
            c.edge_label(pts, e["label"], accent=acc, eid=eid, seg=1, below=True)


def build(spec, tok, variant, top=0, height=None):
    """top and height are set by the social build to centre the figure on a fixed-ratio canvas."""
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    rx, by = back_room(c, spec)
    pl = plan(c, [spec], c.v["width"])
    if rx and pl["mode"] == "tb":
        pl = plan(c, [spec], c.v["width"] - rx, mode="tb")  # the right side is kept for the back edges
    c.W, c.H = draw(c, spec, 0, top, pl)
    if rx:
        c.W, c.H = (c.W + rx, c.H) if pl["mode"] == "tb" else (c.W, c.H + by)
    c.H = height or c.H
    return c.svg()
