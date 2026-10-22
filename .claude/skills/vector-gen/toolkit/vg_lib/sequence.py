"""Sequence diagram: participants across the top, messages down, optional frames (groups of messages).

Spec: {"type": "sequence", "title", "claim", "participants": [{"id","label","icon"?}],
       "steps": [message | row | frame]}
message: {"from","to","label","return": bool, "accent": bool}
row:     {"row": [message, message]}  two messages at the same height that share a source (fan-out)
         or a destination (fan-in): the picture says "at the same time"
frame:   {"frame": "label", "accent": bool, "steps": [...] | "lanes": [[...], [...]],
          "repeat": [i, j]}  lanes are split by a dashed rule (UML par); repeat draws a return arrow
         from message i back to message j of the frame, on the right of their shared participant.
"""
from .prims import Canvas


def wrap_lines(c, text, size, maxw):
    if c.tw(text, size) <= maxw:
        return [text]
    words = text.split()
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if c.tw(a, size) <= maxw and c.tw(b, size) <= maxw:
            return [a, b]
    raise ValueError(f"label '{text}' does not fit {maxw:.0f}px at {size}px in variant {c.vname}; shorten it")


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    parts = spec["participants"]
    n, m, gap = len(parts), v["margin"], v["gap"]
    bw = int((v["width"] - 2 * m - (n - 1) * gap) / n // g) * g
    c.W = n * bw + (n - 1) * gap + 2 * m
    pad = v["label_pad"]
    nf, ef, tf = v["node_font"], v["edge_font"], v["tab_font"]
    # participant names stay on one line: step the shared size down to fit_min, then squeeze the
    # glyphs by up to fit_squeeze, before wrapping
    avail, sq = bw - 2 * pad, c.t["type"]["fit_squeeze"]
    room = avail - 1  # the containment gate keeps 1px inside each side
    sizes = sorted({*c.t["type"]["scale"], c.t["type"]["fit_min"]}, reverse=True)
    fit = next((z for z in sizes if z <= nf and all(c.tw(p["label"], z) <= avail for p in parts)), None)
    if fit is None:
        z = c.t["type"]["fit_min"]
        if all(c.tw(p["label"], z) * sq <= room for p in parts):
            fit = z
    nf = fit or nf
    lines = {p["id"]: [p["label"]] if fit else wrap_lines(c, p["label"], nf, avail) for p in parts}
    nl = max(len(x) for x in lines.values())
    icons = [bool(p.get("icon")) for p in parts]
    if any(icons) and not all(icons):
        raise ValueError("some participants have an icon and some do not; give every participant an icon or none")
    extra = v["icon"] + c.icon_gap() if all(icons) else 0
    bh = c.snap(nl * nf + (nl - 1) * 3 + 2 * nf + extra, up=True)
    cx = {p["id"]: m + bw / 2 + i * (bw + gap) for i, p in enumerate(parts)}
    for p in parts:
        c.node(cx[p["id"]] - bw / 2, m + top, bw, bh, lines[p["id"]], group="participants:x", size=nf, fit_width=room if fit else None, icon=p.get("icon"))

    rf, rs = c.t["radius"]["m"], c.t["radius"]["s"]
    tab_h = tf + 10
    drawn = []  # (message, arrow y) in drawing order, for repeat cues
    tail = [0]  # height a step hangs below its last arrow (labels set under a line)
    end = [0]  # bottom of the content drawn last

    def pts_of(s, ay):
        x1, x2 = cx[s["from"]], cx[s["to"]]
        sg = 1 if x2 > x1 else -1
        return [(x1 + sg * 4, ay), (x2 - sg, ay)]

    def clear_run(s, pts):
        """The part of the arrow the label rides: the whole run, or, when a lifeline would cut through the
        label, the longest stretch between lifelines (the rightmost on a tie, so labels of neighbouring arrows share a column)."""
        (xa, ay), (xb, _) = pts
        w = c.tw(s["label"], ef) + 6
        lo, hi = sorted((xa, xb))
        stops = sorted(x for x in cx.values() if lo + 1 < x < hi - 1)
        if not stops or all(not (lo + (hi - lo) / 2 - w / 2 < x < lo + (hi - lo) / 2 + w / 2) for x in stops):
            return pts
        edges = [lo] + stops + [hi]
        runs = [(a + 4, b - 4) for a, b in zip(edges, edges[1:]) if b - a - 8 >= w]
        if not runs:
            return pts
        best = max(runs, key=lambda r: (round((r[1] - r[0]) / 10), r[1]))
        return [(best[0], ay), (best[1], ay)]

    def message(s, y0):
        ay = y0 + ef + 10
        pts = pts_of(s, ay)
        acc = s.get("accent", False)
        eid = c.edge(pts, dashed=s.get("return", False), accent=acc, cue="label" if acc else None)
        c.edge_label(clear_run(s, pts), s["label"], accent=acc, eid=eid)
        drawn.append((s, ay))
        tail[0] = 0
        end[0] = ay + 4
        return y0 + v["row"]

    def concurrent(row, y0):
        a, b = row
        if a["from"] == b["from"]:
            fan_in = False
        elif a["to"] == b["to"]:
            fan_in = True
        else:
            raise ValueError("a row needs two messages that share a source or a destination")
        ay = y0 + ef + 10
        span = lambda s: abs(cx[s["to"]] - cx[s["from"]])
        short, long_ = sorted(row, key=span)
        for s in row:
            c.edge(pts_of(s, ay), dashed=s.get("return", False), accent=s.get("accent", False),
                   cue="label" if s.get("accent") else None, from_tip=fan_in)
        # the short message labels above its own run; the long one labels below, on the part beyond the short one
        eid_s = None
        c.edge_label(pts_of(short, ay), short["label"], accent=short.get("accent", False), eid=eid_s)
        shared = cx[long_["to"]] if fan_in else cx[long_["from"]]
        far = cx[long_["from"]] if fan_in else cx[long_["to"]]
        near = cx[short["from"]] if fan_in else cx[short["to"]]
        c.edge_label([(near, ay), (far, ay)], long_["label"], accent=long_.get("accent", False), below=True)
        drawn.extend([(a, ay), (b, ay)])
        tail[0] = ef + 4
        end[0] = ay + ef + 8
        return y0 + v["row"] + ef + 4

    def step(s, y0):
        if "row" in s:
            return concurrent(s["row"], y0)
        if "frame" in s:
            return frame(s, y0)
        return message(s, y0)

    def frame(s, y0):
        lanes = s.get("lanes") or [s["steps"]]
        flat = [t for lane in lanes for t in lane]
        flat = [x for t in flat for x in (t["row"] if "row" in t else [t])]
        ids = [i for t in flat for i in (t["from"], t["to"])]
        lo, hi = min(cx[i] for i in ids) - bw / 2, max(cx[i] for i in ids) + bw / 2
        top, first = y0, len(drawn)
        y0 += tab_h + 6
        last = y0
        for k, lane in enumerate(lanes):
            for t in lane:
                y0 = step(t, y0)
            last = drawn[-1][1] + tail[0]
            if k < len(lanes) - 1:
                c.divider(lo, hi, last + 14)
                y0 = last + 14 + 8
        y0 = last + 14
        end[0] = y0
        acc = s.get("accent", False)
        # tabbed container: the left edge runs straight from tab to bottom, so bottom-left is square
        c.shape("container", "frame", lo, top, hi - lo, y0 - top, (rf, rf, rf, 0),
                stroke="accent" if acc else "muted", dash=None if acc else "3 4", snap=False,
                accent=acc, cue="solid-outline+tab-fill" if acc else None)
        tw_ = c.tw(s["frame"], tf, True) + 14
        tid = c.shape("container", "tab", lo, top, tw_, tab_h, (rf, 0, rs, 0),
                      fill="accent" if acc else "surface", stroke="accent" if acc else "muted", snap=False)
        c.text(lo + tw_ / 2, top + tab_h - 6, s["frame"], tf, 700, "bg" if acc else "ink", anchor="middle",
               halo=False, role="tab-text", inside=tid, layer="container")
        if s.get("repeat"):
            i, j = s["repeat"]
            (mi, yi), (mj, yj) = drawn[first + i], drawn[first + j]
            shared = {mi["from"], mi["to"]} & {mj["from"], mj["to"]}
            if not shared:
                raise ValueError("repeat needs two messages that share a participant")
            x = max(cx[p] for p in shared)
            # a bracket from the tip of the last message to the tip of the first, kept 8px inside the frame
            off = min(30, bw / 2 - 8)
            c.edge([(x, yi), (x + off, yi), (x + off, yj), (x, yj)], accent=acc, cue="elbow-shape" if acc else None, head="none")
        return y0 + 10

    y = m + top + bh + 16
    for s in spec["steps"]:
        y = step(s, y)
    c.H = height or end[0] + max(m, 8)
    # lifelines break where an arrow or a label crosses them, so dashes never run into an arrow or a word
    for p in parts:
        x, y1, y2 = cx[p["id"]], m + top + bh, end[0] + max(m, 8) - 4
        cuts = [(ay - 5, ay + 5) for s_, ay in drawn if min(cx[s_["from"]], cx[s_["to"]]) + 1 < x < max(cx[s_["from"]], cx[s_["to"]]) - 1]
        cuts += [(t - 2, bt + 2) for lo, hi, t, bt in c.label_boxes if lo - 2 < x < hi + 2]
        y = y1
        for t, bt in sorted(cuts):
            if t > y:
                c.guide(x, y, x, t)
            y = max(y, bt)
        if y < y2:
            c.guide(x, y, x, y2)
    return c.svg()
