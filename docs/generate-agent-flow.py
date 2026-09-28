#!/usr/bin/env python3
"""Hand-built sequence-diagram SVG generator.

Design discipline (hallmark + artifact-diagramming):
- One accent hue only (rust/terracotta), used exclusively for step badges
  and the two fragment (par/loop) boxes -- everything else stays ink/neutral.
- OKLCH-derived palette, warm paper, no gradients, no drop shadows.
- Every arrow labeled; self-messages drawn as a small hook, matching UML.
- Grid-aligned: fixed lane x-centers, fixed row height.
"""

import pathlib

FONT = "Helvetica Neue, Arial, sans-serif"

PAPER   = "#FAF8F3"
INK     = "#1C1B17"
MUTED   = "#6E6A5D"
RULE    = "#CFC9B8"
LANE    = "#B9B3A0"
ACCENT  = "#B5502E"
ACCENT_SOFT = "#F3E4DC"
GOOD    = "#3E7A4C"

W = 1900
actors = [
    ("U",  "User",                    160),
    ("R",  "Root session",            423),
    ("C",  "team-lead-\ncoordinator", 687),
    ("PO", "product-owner",           950),
    ("A",  "lead-system-\narchitect", 1213),
    ("E",  "senior-software-\nengineer", 1477),
    ("CR", "code-reviewer",           1740),
]
ax = {k: x for k, _, x in actors}

TOP = 168
BOTTOM = 1560
BOX_W, BOX_H = 172, 64

lines = []
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text(x, y, s, size=15, weight=400, fill=INK, anchor="middle", family=FONT, spacing=None, style=None):
    attrs = f'font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
    if spacing:
        attrs += f' letter-spacing="{spacing}"'
    if style:
        attrs += f' font-style="{style}"'
    lines.append(f'<text x="{x:.1f}" y="{y:.1f}" {attrs}>{esc(s)}</text>')

def multitext(x, y, s, size=15, weight=700, fill=INK, lh=18):
    for i, part in enumerate(s.split("\n")):
        text(x, y + i * lh, part, size=size, weight=weight, fill=fill)

def actor_box(x, y, label):
    lines.append(f'<rect x="{x-BOX_W/2:.1f}" y="{y:.1f}" width="{BOX_W}" height="{BOX_H}" rx="10" '
                 f'fill="#FFFFFF" stroke="{LANE}" stroke-width="1.6"/>')
    n_lines = label.count("\n") + 1
    start = y + BOX_H/2 - (n_lines-1)*10 + 5
    multitext(x, start, label, size=15.5, weight=700, fill=INK, lh=20)

def lifeline(x):
    lines.append(f'<line x1="{x:.1f}" y1="{TOP+BOX_H:.1f}" x2="{x:.1f}" y2="{BOTTOM:.1f}" '
                 f'stroke="{LANE}" stroke-width="1.6" stroke-dasharray="2 5"/>')

def badge(x, y, n):
    lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12.5" fill="{ACCENT}"/>')
    text(x, y+4.5, str(n), size=13, weight=700, fill="#FFFFFF")

def arrow(y, src, dst, label, n, dashed=False, label_dy=-9):
    x1, x2 = ax[src], ax[dst]
    forward = x2 > x1
    tip = x2 - (16 if forward else -16)
    stroke_style = f'stroke-dasharray="7 5"' if dashed else ""
    lines.append(f'<line x1="{x1+ (14 if forward else -14):.1f}" y1="{y:.1f}" x2="{tip:.1f}" y2="{y:.1f}" '
                 f'stroke="{MUTED}" stroke-width="2" {stroke_style} marker-end="url(#arrow)"/>')
    mid = (x1 + x2) / 2
    text(mid, y+label_dy, label, size=14.5, weight=600, fill=INK)
    badge(x1 + (14 if forward else -14), y, n)

def self_msg(y, actor, label, n):
    x = ax[actor]
    hook = 66
    lines.append(f'<path d="M {x:.1f} {y-14:.1f} L {x+hook:.1f} {y-14:.1f} L {x+hook:.1f} {y+14:.1f} L {x+13:.1f} {y+14:.1f}" '
                 f'fill="none" stroke="{MUTED}" stroke-width="2" marker-end="url(#arrow)"/>')
    text(x+hook+14, y-2, label, size=14.5, weight=600, fill=INK, anchor="start")
    badge(x, y-14, n)

def fragment(y0, y1, x0, x1, tag, top_label=None, mid_label=None, mid_y=None):
    pad = 34
    lx0, lx1 = x0-pad, x1+pad
    lines.append(f'<rect x="{lx0:.1f}" y="{y0:.1f}" width="{lx1-lx0:.1f}" height="{y1-y0:.1f}" rx="4" '
                 f'fill="{ACCENT_SOFT}" fill-opacity="0.55" stroke="{ACCENT}" stroke-width="1.6" stroke-dasharray="3 4"/>')
    tab_w, tab_h = 54, 24
    lines.append(f'<path d="M {lx0:.1f} {y0:.1f} h {tab_w} v {tab_h-8} l -8 8 h {-(tab_w-8)} z" fill="{ACCENT}"/>')
    text(lx0+tab_w/2, y0+16.5, tag, size=12.5, weight=700, fill="#FFFFFF")
    if top_label:
        text((lx0+lx1)/2 + 14, y0+16.5, top_label, size=13, weight=600, fill=ACCENT)
    if mid_label:
        lines.append(f'<line x1="{lx0:.1f}" y1="{mid_y:.1f}" x2="{lx1:.1f}" y2="{mid_y:.1f}" '
                     f'stroke="{ACCENT}" stroke-width="1.4" stroke-dasharray="3 4"/>')
        text((lx0+lx1)/2, mid_y+16.5, mid_label, size=13, weight=600, fill=ACCENT)

# ---- header ----
text(70, 78, "AI Agents Team", size=40, weight=700, fill=INK, anchor="start")
text(70, 116, "How an application-code change ships — request to /verify", size=21, weight=400, fill=MUTED, anchor="start")
lines.append(f'<line x1="70" y1="136" x2="{W-70}" y2="136" stroke="{RULE}" stroke-width="1.6"/>')

# ---- actor boxes (top) ----
for key, label, x in actors:
    actor_box(x, TOP, label)
    lifeline(x)

# ---- rows ----
arrow(240, "U", "R", "Request", 1)
arrow(310, "R", "C", "Brief and constraints", 2)
self_msg(380, "C", "Classify size lane and dependencies", 3)

fragment(420, 700, ax["PO"], ax["A"], "par", top_label=None, mid_label="[ architecture ]", mid_y=560)
text((ax["PO"]+ax["A"])/2, 442, "[ business requirements ]", size=13, weight=600, fill=ACCENT, anchor="middle")
arrow(480, "C", "PO", "Draft requirements and ACs", 4)
arrow(538, "PO", "C", "Spec and consultation", 5, dashed=True)
arrow(618, "C", "A", "Define constraints", 6)
arrow(676, "A", "C", "Plan and consultation", 7, dashed=True)

arrow(760, "C", "E", "Requirements and constraints", 8)
self_msg(830, "E", "Implement, test, open MR", 9)
arrow(900, "E", "CR", "MR for independent review", 10)

fragment(940, 1080, ax["E"], ax["CR"], "loop")
text((ax["E"]+ax["CR"])/2, 962, "[ while blocking findings remain ]", size=13, weight=600, fill=ACCENT, anchor="middle")
arrow(1000, "CR", "E", "Findings", 11, dashed=True)
arrow(1058, "E", "CR", "Fixes", 12)

arrow(1140, "CR", "E", "Attestation and approval", 13, dashed=True)
self_msg(1210, "E", "SHA-pinned merge", 14)
arrow(1280, "E", "C", "Result and evidence", 15, dashed=True)
self_msg(1350, "C", "/verify", 16)
arrow(1420, "C", "R", "Confirmation or blockers", 17, dashed=True)
arrow(1490, "R", "U", "Outcome", 18, dashed=True)

# ---- actor boxes (bottom) ----
for key, label, x in actors:
    actor_box(x, BOTTOM, label)

# ---- footer ----
lines.append(f'<line x1="70" y1="{BOTTOM+BOX_H+30}" x2="{W-70}" y2="{BOTTOM+BOX_H+30}" stroke="{RULE}" stroke-width="1.6"/>')
text(70, BOTTOM+BOX_H+62, "Author and reviewer are always separate agent instances — recorded in a REVIEW-ATTESTATION.", size=15.5, weight=400, fill=MUTED, anchor="start")
text(W-70, BOTTOM+BOX_H+62, "github.com/uprinter/ai-agents-team", size=15.5, weight=400, fill=MUTED, anchor="end")

H = BOTTOM + BOX_H + 90

svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img"
  aria-label="Sequence diagram: a change request flows from the user through the coordinator, which consults the product owner and architect in parallel, then hands off to the engineer, whose merge request goes through an independent review loop with the reviewer before a SHA-pinned merge and /verify.">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7.5" markerHeight="7.5" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/>
    </marker>
  </defs>
  <rect width="{W}" height="{H}" fill="{PAPER}"/>
  {chr(10).join(lines)}
</svg>
'''

out = pathlib.Path(__file__).parent / "agent-flow.svg"
out.write_text(svg)
print(f"wrote {out}", H, "tall")
print("render with: rsvg-convert -o agent-flow.png agent-flow.svg")
