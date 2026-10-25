"""Drawing primitives. Every craft rule (see references/craft-rules.md) lives here once.

A diagram type never writes raw SVG: it asks the Canvas for a node, container, tab, edge or
label, and the Canvas applies the stroke scale, radius logic, arrowhead proportions, colour
roles and halo. Each element carries data-* attributes that check.py measures in a browser.
"""
import difflib, json, pathlib, re
from html import escape
from .measure import text_width

_ICON_DIR = pathlib.Path(__file__).resolve().parent.parent / "icons"
_ICONS = json.loads((_ICON_DIR / "lucide.json").read_text())["icons"]
_BRANDS = json.loads((_ICON_DIR / "brands.json").read_text())["brands"]
_BRANDS.update(json.loads((_ICON_DIR / "brands-extra.json").read_text())["brands"])  # hand-added logos

LAYERS = ("guide", "container", "edge", "node", "label")
DIGITS = re.compile(r"(\d[\d.,]*\d|\d)")
VALUE_ROLES = ("card-value", "badge-text")  # numbers: the figure font for digits has lining figures, Georgia has old-style ones that sink below the baseline


class Canvas:
    def __init__(self, tok, variant, title, claim):
        self.t, self.vname, self.title, self.claim = tok, variant, title, claim
        self.v = tok["variants"][variant]
        self.layers = {k: [] for k in LAYERS}
        self._n = 0
        self.icon_sizes = []
        self.brand_notes = {}
        self.icon_kinds = set()
        self.label_boxes = []  # (left, right, top, bottom) of edge labels
        self.spans = []  # (left, right, text) of every text, for the margin rule
        self.links = False  # the figure carries links: it is a group of links, not one image, and its ids are prefixed per variant
        self.W = self.H = 0

    # ---- tokens and measure -------------------------------------------------------------
    def color(self, name):
        return self.t["colors"][name]

    def stroke(self, name):
        return self.t["stroke"][name]

    def tw(self, s, size, bold=False, face=None):
        return text_width(self.t, s, size, bold, self.v["safety"], face)

    def snap(self, x, up=False):
        g = self.v["grid"]
        return (-(-x // g) if up else round(x / g)) * g

    def uid(self, p):
        self._n += 1
        return f"{self.vname + '-' if self.links else ''}{p}{self._n}"

    def radius_for(self, w, h):
        """Radius rule: a sixth of the short side, snapped to the radius scale."""
        scale = sorted(set(self.t["radius"].values()))
        return min(scale, key=lambda r: abs(r - min(w, h) / 6))

    # ---- shapes -------------------------------------------------------------------------
    @staticmethod
    def rpath(x, y, w, h, tl=0, tr=0, br=0, bl=0):
        return (f"M{x + tl:g} {y:g}H{x + w - tr:g}" + (f"A{tr:g} {tr:g} 0 0 1 {x + w:g} {y + tr:g}" if tr else "")
                + f"V{y + h - br:g}" + (f"A{br:g} {br:g} 0 0 1 {x + w - br:g} {y + h:g}" if br else "")
                + f"H{x + bl:g}" + (f"A{bl:g} {bl:g} 0 0 1 {x:g} {y + h - bl:g}" if bl else "")
                + f"V{y + tl:g}" + (f"A{tl:g} {tl:g} 0 0 1 {x + tl:g} {y:g}" if tl else "") + "Z")

    def shape(self, layer, role, x, y, w, h, radii, fill="none", stroke="hair", sw="outline", dash=None,
              group=None, snap=True, accent=False, cue=None, id=None):
        id = id or self.uid("s")
        a = (f'<path id="{id}" data-role="{role}" d="{self.rpath(x, y, w, h, *radii)}" '
             f'fill="{self.color(fill) if fill != "none" else "none"}" stroke="{self.color(stroke)}" stroke-width="{self.stroke(sw)}"')
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if group:
            a += f' data-group="{group}"'
        if snap:
            a += ' data-snap="1"'
        if accent:
            a += f' data-accent="1" data-cue="{cue or ""}"'
        self.layers[layer].append(a + "/>")
        return id

    def node(self, x, y, w, h, lines, group="nodes", accent=False, cue=None, dashed=False, dim=False, sw="outline", size=None, fit_width=None, icon=None, underline=False, href=None):
        """A labelled box. Radius comes from the radius rule, text is optically centred.
        With an icon, icon and label form one block, centred in the box, icon above the label."""
        r = self.radius_for(w, h)
        id = self.uid("n")
        self.shape("node", "node", x, y, w, h, (r, r, r, r), fill="surface",
                   stroke="accent" if accent else "hair", sw=sw, dash="4 3" if dashed else None,
                   group=group, accent=accent, cue=cue, id=id)
        size = size or self.v["node_font"]
        lh = size + 3
        y0 = y + h / 2 - (len(lines) - 1) * lh / 2 + size * 0.345
        if icon:
            isz, gap = self.v["icon"], self.icon_gap()
            block = isz + gap + (len(lines) - 1) * lh + size * 1.14
            top = self.snap(y + (h - block) / 2)
            self.icon(icon, self.snap(x + (w - isz) / 2), top, isz, fill="muted" if dim else "ink", group=group.split(":")[0] + "-icons", inside=id)
            y0 = top + isz + gap + size * 0.92
        n0 = len(self.layers["node"])
        for i, line in enumerate(lines):
            self.text(x + w / 2, y0 + i * lh, line, size, fill="muted" if dim else "ink", halo=False,
                      role="node-text", inside=id, layer="node", cont=i > 0, underline=underline,
                      squeeze=fit_width if fit_width and self.tw(line, size) > fit_width else None)
        if href:  # only the name is the link, never the box: a boxed link reads as a bigger action than opening a page
            self.layers["node"][n0:] = [f'<a href="{escape(href, quote=True)}">' + "".join(self.layers["node"][n0:]) + "</a>"]
        return id

    def _brand_icon(self, slug, x, y, size, fill, group, inside):
        """A brand logo from the vendored Simple Icons set: one filled glyph in one token colour, never the brand colour."""
        if slug not in _BRANDS:
            near = difflib.get_close_matches(slug, _BRANDS, n=4)
            raise ValueError(f"brand '{slug}' is not in icons/brands.json" + (f"; did you mean {', '.join(near)}?" if near else ""))
        if size not in self.t["icon"]["scale"]:
            raise ValueError(f"icon size {size} is not on the icon scale {self.t['icon']['scale']}")
        b = _BRANDS[slug]
        self.icon_sizes.append(size)
        self.brand_notes[slug] = b.get("guidelines")
        extra = f' data-in="{inside}"' if inside else ""
        vw, vh = b.get("viewBox", [24, 24])
        k = size / max(vw, vh)  # a logo that is not square is fitted into the icon box and centred
        self.layers["node"].append(
            f'<g data-role="icon" data-kind="brand" data-name="{slug}" data-size="{size}" data-x="{x:g}" data-y="{y:g}" '
            f'data-group="{group}"{extra} transform="translate({x + (size - vw * k) / 2:g} {y + (size - vh * k) / 2:g}) scale({k:g})" fill="{self.color(fill)}">'
            f'<path d="{b["d"]}"/></g>')

    def icon_gap(self):
        """Space between an icon and the label under it: a quarter of the icon, on the grid."""
        return max(self.snap(self.v["icon"] / 4, up=True), 5)

    def text(self, x, y, s, size, weight=400, fill="ink", anchor="middle", halo=True, role="label",
             inside=None, layer="label", data_for=None, squeeze=None, halo_w=4, cont=False, underline=False):
        a = (f'<text data-role="{role}" x="{x:g}" y="{y:g}" font-size="{size}" font-weight="{weight}" '
             f'fill="{self.color(fill)}" text-anchor="{anchor}"')
        runs = [(part, i % 2 == 1) for i, part in enumerate(DIGITS.split(s)) if part] if role not in VALUE_ROLES else [(s, True)]
        w_ = sum(self.tw(part, size, weight >= 700, "value" if dig else None) for part, dig in runs)
        lo = x - w_ / 2 if anchor == "middle" else x if anchor == "start" else x - w_
        self.spans.append((lo, lo + w_, s))
        if role == "edge-label":
            self.label_boxes.append((lo, lo + w_, y - size * 0.9, y + size * 0.3))
        if size < self.t["type"]["min"]:
            a += ' data-fit="1"'
        if squeeze:
            a += f' textLength="{squeeze:g}" lengthAdjust="spacingAndGlyphs"'
        if halo:
            a += f' stroke="{self.color("bg")}" stroke-width="{halo_w}" stroke-linejoin="round" paint-order="stroke"'
        if inside:
            a += f' data-in="{inside}"'
        if role in VALUE_ROLES:
            a += f' font-family="{escape(self.t["font"]["value"]["family"], quote=True)}"'
        if underline:
            a += ' text-decoration="underline"'
        if cont:
            a += ' data-cont="1"'
        if data_for:
            a += f' data-for="{data_for}"'
        fam = escape(self.t["font"]["value"]["family"], quote=True)
        # digits in body text are set in the figure number font too, so 3 and 4 do not sink below the baseline
        body = escape(s) if role in VALUE_ROLES or not DIGITS.search(s) else "".join(
            f'<tspan font-family="{fam}">{escape(part)}</tspan>' if dig else escape(part) for part, dig in runs)
        self.layers[layer].append(a + f">{body}</text>")

    def icon(self, name, x, y, size, fill="ink", group="icons", inside=None):
        """A line icon from the vendored Lucide set, size on the icon scale, stroke from the stroke scale.
        The 24-unit drawing is scaled by a group transform, so the stroke width is divided by the scale and
        data-sw records the width the eye sees; check.py reads that."""
        self.icon_kinds.add("brand" if name.startswith("brand:") else "line")
        if name.startswith("brand:"):
            return self._brand_icon(name[6:], x, y, size, fill, group, inside)
        if name not in _ICONS:
            near = difflib.get_close_matches(name, _ICONS, n=4) or [n for n, i in _ICONS.items() if name in i["tags"]][:4]
            raise ValueError(f"icon '{name}' is not in icons/lucide.json" + (f"; did you mean {', '.join(near)}?" if near else ""))
        if size not in self.t["icon"]["scale"]:
            raise ValueError(f"icon size {size} is not on the icon scale {self.t['icon']['scale']}")
        k = size / 24
        sw = self.stroke(self.t["icon"]["stroke"])
        body = "".join(
            f"<{tag} " + " ".join(f'{a}="{v}"' for a, v in attrs.items()) + "/>" for tag, attrs in _ICONS[name]["shapes"])
        self.icon_sizes.append(size)
        extra = f' data-in="{inside}"' if inside else ""
        self.layers["node"].append(
            f'<g data-role="icon" data-name="{name}" data-size="{size}" data-sw="{sw:g}" data-x="{x:g}" data-y="{y:g}" data-group="{group}"{extra} '
            f'transform="translate({x:g} {y:g}) scale({k:g})" fill="none" stroke="{self.color(fill)}" '
            f'stroke-width="{sw / k:g}" stroke-linecap="round" stroke-linejoin="round">{body}</g>')

    def guide(self, x1, y1, x2, y2, dash="4 4"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.layers["guide"].append(
            f'<line data-role="guide" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{self.color("hair")}" stroke-width="{self.stroke("guide")}"{d}/>')

    def divider(self, x1, x2, y):
        """Dashed rule across a frame, separating its parallel lanes (UML par operands)."""
        self.layers["container"].append(
            f'<path data-role="divider" d="M{x1:g} {y:g}H{x2:g}" fill="none" stroke="{self.color("muted")}" '
            f'stroke-width="{self.stroke("outline")}" stroke-dasharray="3 4"/>')

    # ---- edges --------------------------------------------------------------------------
    def edge(self, pts, color="muted", dashed=False, accent=False, cue=None, src=None, dst=None, sw="connector", from_tip=False, head="filled"):
        """Orthogonal connector ending in a head 6x stroke long, 0.72x of that wide. head="open" draws a chevron (asynchronous), head="none" ends the line square on its target (a loop bracket)."""
        w = self.stroke(sw)
        hl = self.t["arrow"]["len_per_stroke"] * self.stroke("connector")
        hw = hl * self.t["arrow"]["half_width_ratio"]
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        ux = (x1 > x0) - (x1 < x0)
        uy = (y1 > y0) - (y1 < y0)
        base = (x1 - ux * hl, y1 - uy * hl)
        line = list(pts[:-1]) + [(base[0] + ux, base[1] + uy) if head == "filled" else (x1, y1) if head == "none" else (x1 - ux * w / 2, y1 - uy * w / 2)]
        col = self.color("accent" if accent else color)
        drawn = list(reversed(line)) if from_tip else line  # from_tip: dash phase starts at the arrow end
        d = "M" + "L".join(f"{x:g} {y:g}" for x, y in drawn)
        eid = self.uid("e")
        extra = f' id="{eid}"'
        extra += f' data-src="{src}"' if src else ""
        extra += f' data-dst="{dst}"' if dst else ""
        if accent:
            extra += f' data-accent="1" data-cue="{cue or ""}"'
        pts_attr = ";".join(f"{x:g},{y:g}" for x, y in pts)
        self.layers["edge"].append(
            f'<path data-role="edge" data-hl="{hl:g}" data-pts="{pts_attr}" d="{d}" fill="none" stroke="{col}" stroke-width="{w}" '
            f'stroke-linejoin="round"' + (' stroke-dasharray="5 4"' if dashed else "") + f"{extra}/>")
        px, py = -uy, ux
        if head == "none":
            return eid
        if head == "open":
            self.layers["edge"].append(
                f'<path data-role="head" data-sw="{self.stroke("connector")}" fill="none" stroke="{col}" stroke-width="{w}" '
                f'stroke-linejoin="miter" d="M{base[0] + px * hw:g} {base[1] + py * hw:g}L{x1:g} {y1:g}L{base[0] - px * hw:g} {base[1] - py * hw:g}"/>')
        else:
            self.layers["edge"].append(
                f'<polygon data-role="head" data-sw="{self.stroke("connector")}" fill="{col}" points="'
                f'{x1:g},{y1:g} {base[0] + px * hw:g},{base[1] + py * hw:g} {base[0] - px * hw:g},{base[1] - py * hw:g}"/>')
        return eid

    def edge_label(self, pts, s, accent=False, bold=False, eid=None, seg=None, below=False, side=1, size=None):
        """Label sits above a horizontal run or beside a vertical one. seg = index of the run (default: longest)."""
        size = size or self.v["edge_font"]
        segs = list(zip(pts, pts[1:]))
        if seg is None:
            seg = max(range(len(segs)), key=lambda i: abs(segs[i][1][0] - segs[i][0][0]) + abs(segs[i][1][1] - segs[i][0][1]))
        a, b = segs[seg]
        fill = "accent" if accent else "ink"
        weight = 700 if (accent or bold) else 400
        if a[1] == b[1]:
            self.text((a[0] + b[0]) / 2, a[1] + size + 4 if below else a[1] - 10, s, size, weight, fill, role="edge-label", data_for=eid, halo_w=8)
        else:
            self.text(a[0] + self.v.get("label_gap", 10) * side, (a[1] + b[1]) / 2 + size * 0.345, s, size, weight, fill,
                      anchor="start" if side > 0 else "end", role="edge-label", data_for=eid)

    # ---- output -------------------------------------------------------------------------
    def svg(self):
        c = self.color
        if len(self.icon_kinds) > 1:
            raise ValueError("line icons and brand logos mixed in one figure; use one kind, line icons for generic parts or logos when every node is a named product")
        m = self.v.get("text_margin")
        if m:  # a text that runs closer than the margin to the canvas edge reads as cut off in a feed
            for lo, hi, s in self.spans:
                if lo < m - 0.5 or hi > self.W - m + 0.5:
                    raise ValueError(f"text '{s}' comes within {m}px of the canvas edge in variant {self.vname}; shorten it")
        body = "".join("".join(self.layers[k]) for k in LAYERS)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W:g} {self.H:g}" width="{self.W:g}" '
                f'height="{self.H:g}" font-family="{escape(self.t["font"]["family"], quote=True)}" role="{"group" if self.links else "img"}" '
                f'aria-label="{escape(self.claim, quote=True)}" data-variant="{self.vname}" '
                f'data-min-px="{self.t["type"]["min"]}" data-grid="{self.v["grid"]}"'
                + (f' data-min-icon-px="{self.t["icon"]["min"]}" data-min-icon="{min(self.icon_sizes)}"' if self.icon_sizes else "")
                + (f' data-brands="{",".join(sorted(self.brand_notes))}"' if self.brand_notes else "") + ">"
                f'{"" if self.links else "<title>" + escape(self.title) + "</title>"}<rect width="{self.W:g}" height="{self.H:g}" fill="{c("bg")}"/>{body}</svg>')
