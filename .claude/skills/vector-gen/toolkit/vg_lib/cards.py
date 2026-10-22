"""Cards: a grid of equal cards, each with an optional icon, a big value, a title and a short text.

Spec: {"type": "cards", "title", "claim",
       "cards": [{"title", "text"?, "value"?, "icon"?, "accent"?}],
       "columns"?: n}
A card with "value" is a statistic: the value is set large above its title. Cards share one size.
Columns are chosen so the text in each card is at least tokens "cards.min_text" wide and the last row is at least
half full; "columns" overrides that. Icons follow the flow rule: every card has one or none.
"""
from .prims import Canvas
from .layout import wrap, line_height, baseline


def build(spec, tok, variant, top=0, height=None):
    c = Canvas(tok, variant, spec["title"], spec["claim"])
    v, g = c.v, c.v["grid"]
    W, pad, nf, ef = v["width"], v["pad"], v["node_font"], v["edge_font"]
    cards, n = spec["cards"], len(spec["cards"])
    sf = v.get("stat_font", 28)
    gap = c.snap(max(8, v["gap"]), up=True)
    if any(x.get("icon") for x in cards) and not all(x.get("icon") for x in cards):
        raise ValueError("some cards have an icon and some do not; give every card an icon or none")
    icon = all(x.get("icon") for x in cards)

    def card_w(k):
        return int((W - 2 * pad - (k - 1) * gap) // k // g) * g

    feasible = [k for k in range(1, n + 1) if card_w(k) - 2 * pad >= c.t["cards"]["min_text"]] or [1]
    k = spec.get("columns") or max(feasible, key=lambda k: ((n % k or k) / k >= 0.6, k))
    if not spec.get("columns") and n <= v.get("stack_up_to", 0):
        k = 1  # a short set in a portrait frame stacks, so it fills the frame
    rows = -(-n // k)
    row_n = [min(k, n - r * k) for r in range(rows)]  # an incomplete last row shares the full width

    def width_of(r):
        return int(((k * card_w(k) + (k - 1) * gap) - (row_n[r] - 1) * gap) // row_n[r] // g) * g if row_n[r] < k else card_w(k)

    ws = [width_of(i // k) for i in range(n)]
    parts = []
    for i, x in enumerate(cards):
        inner = ws[i] - 2 * pad
        if x.get("value") and c.tw(x["value"], sf, True, "value") > inner:
            raise ValueError(f"value '{x['value']}' does not fit {inner}px at {sf}px in variant {c.vname}; shorten it")
        parts.append((wrap(c, x["title"], nf, inner, True), wrap(c, x["text"], ef, inner) if x.get("text") else []))
    for size in (s for s in (nf, 14, 12) if s <= nf):  # the largest title size at which no title wraps, if one exists
        if all(c.tw(x["title"], size, True) <= ws[i] - 2 * pad for i, x in enumerate(cards)):
            nf = size
            break
    parts = [(wrap(c, x["title"], nf, ws[i] - 2 * pad, True), p[1]) for i, (x, p) in enumerate(zip(cards, parts))]
    lt, lx = line_height(nf), line_height(ef)

    tl_row = [max(len(parts[j][0]) for j in range(r * k, min(n, r * k + k))) for r in range(rows)]  # title lines reserved per row

    def body(i):
        t, x = parts[i]
        return ((v["icon"] + c.icon_gap()) if icon else 0) + ((line_height(sf) + 4) if cards[i].get("value") else 0) + tl_row[i // k] * lt + ((4 + len(x) * lx) if x else 0)

    inner_h = max(body(i) for i in range(n))
    h = c.snap(2 * pad + inner_h, up=True)
    dy = 0
    if height:  # a fixed frame: the cards grow, by at most half, to fill it, and their content stays centred
        grown = min(int((height - 2 * pad - (rows - 1) * gap) // rows // g) * g, c.snap(h * 1.5, up=True))
        if grown > h:
            h, top = grown, 0
        dy = (h - 2 * pad - inner_h) / 2
        top = max(0, c.snap((height - (rows * h + (rows - 1) * gap)) / 2 - pad))
    for i, card in enumerate(cards):
        r_i, w = i // k, ws[i]
        total = row_n[r_i] * w + (row_n[r_i] - 1) * gap
        x = c.snap((W - total) / 2) + (i % k) * (w + gap)
        y = top + pad + r_i * (h + gap)
        r = c.radius_for(w, h)
        acc = card.get("accent", False)
        cid = c.shape("node", "node", x, y, w, h, (r, r, r, r), fill="surface", stroke="accent" if acc else "hair",
                      sw="emphasis" if acc else "outline", group=f"cards-{r_i}", accent=acc, cue="weight")
        cy = y + pad + dy
        if icon:
            c.icon(card["icon"], x + pad, cy, v["icon"], fill="ink", group="cards-icons", inside=cid)
            cy += v["icon"] + c.icon_gap()
        if card.get("value"):
            c.text(x + pad, baseline(cy, sf), card["value"], sf, 700, "accent", anchor="start", halo=False,
                   role="card-value", inside=cid, layer="node")
            cy += line_height(sf) + 4
        t, body_lines = parts[i]
        for j, s in enumerate(t):
            c.text(x + pad, baseline(cy, nf), s, nf, 700, "ink", anchor="start", halo=False, role="node-text", inside=cid, layer="node", cont=j > 0)
            cy += lt
        cy += (tl_row[r_i] - len(t)) * lt  # captions start level across the row
        if body_lines:
            cy += 4
        for j, s in enumerate(body_lines):
            c.text(x + pad, baseline(cy, ef), s, ef, 400, "muted", anchor="start", halo=False, role="node-text", inside=cid, layer="node", cont=j > 0)
            cy += lx
    c.W = W
    c.H = height or (top + 2 * pad + rows * h + (rows - 1) * gap)
    return c.svg()
