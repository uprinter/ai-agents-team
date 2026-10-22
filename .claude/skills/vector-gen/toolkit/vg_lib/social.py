"""Feed image: the same figure on a fixed-ratio canvas for a social post.

A phone feed shows the image as wide as the screen, 360px at the narrowest, so the figure is drawn at
360 units wide with the "social" variant tokens (bigger type, top-down flow) and exported at 3x, which
is 1080px wide. Height lies between square and 4:5; a figure shorter than 4:5 is centred, one taller is
refused with advice. Ratio, width and size limits are in tokens "social"; the source of the numbers is in craft-rules.md.
"""
import copy, re


def build(mod, spec, tok):
    """Largest type step whose figure still fits 4:5, so the figure fills the frame; the base step is the last resort."""
    s = tok["social"]
    t2 = copy.deepcopy(tok)
    t2["type"]["min"] = s["min_font"]
    w, g = s["variant"]["width"], s["variant"]["grid"]
    hmax, hmin = w * s["ratio_max"], w * s["ratio_min"]
    err = None
    for relaxed in (False, True):  # first insist on the figure's best layout, then accept a fallback layout
        for tier in [*s.get("tiers", []), {}, *s.get("compact", [])]:
            t2["variants"] = {"social": {**s["variant"], **tier, "cross_only": not relaxed}}
            try:
                natural = float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', mod.build(spec, t2, "social")).group(1))
            except ValueError as e:
                err = e
                continue
            if natural > hmax:
                err = ValueError(f"social: figure is {natural:g}px tall at {w}px wide, 4:5 allows {hmax:g}; cut nodes or label length, or split it in two images")
                continue
            target = max(hmax if natural >= s["fill_from"] * hmax else hmin, natural)
            top = round((target - natural) / 2 / g) * g
            return mod.build(spec, t2, "social", top=top, height=target), t2
    raise err
