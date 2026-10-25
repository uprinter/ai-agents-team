# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "playwright"]
# ///
"""vector-gen: spec -> one SVG per width variant, gated by measured checks.

  uv run vg.py build SPEC.json --out DIR [--tokens PROJECT_TOKENS.json]
  uv run vg.py icons [QUERY]        list or search the vendored icon names (Lucide, ISC)
  uv run vg.py tokens PALETTE.md [--mode dark|light] [--font sans] [--accent HEX] [--out OVERRIDE.json]
                                    a token override from a dataviz-style palette file, one palette for charts and diagrams
  uv run vg.py check FILE.svg [--width PX] [--tokens PROJECT_TOKENS.json] [--out PNG]
                                    partial gates for an SVG that was not built here (hand-drawn or exported)

Writes DIR/<name>-<variant>.svg, a PNG of each variant at its smallest display width, and
DIR/<name>.picture.html (a <picture> snippet with the computed breakpoints). It also writes the feed
image for a social post, DIR/<name>-social.svg and -social.png (1080px wide, ratio 1:1 to 4:5); a spec
may switch that off with "no_social": true. Exit 1 if any gate fails.
Needs Chromium for Playwright: uv run --with playwright playwright install chromium
"""
import argparse, json, pathlib, re, sys
from vg_lib import tokens, sequence, flow, compare, check, social, cards, steps, hub, cycle, matrix, funnel, swimlanes, layers

TYPES = {"sequence": sequence, "flow": flow, "compare": compare, "cards": cards, "steps": steps, "hub": hub, "cycle": cycle, "matrix": matrix, "funnel": funnel, "swimlanes": swimlanes, "layers": layers}


def min_display_width(svg):
    w = float(re.search(r'viewBox="0 0 ([\d.]+)', svg).group(1))
    minpx = float(re.search(r'data-min-px="([\d.]+)"', svg).group(1))
    smallest = min(float(x) for x in re.findall(r'<text(?![^>]*data-fit)[^>]*font-size="([\d.]+)"', svg))
    need = w * minpx / smallest
    m = re.search(r'data-min-icon-px="([\d.]+)" data-min-icon="([\d.]+)"', svg)
    if m:
        need = max(need, w * float(m.group(1)) / float(m.group(2)))
    return w, need


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "icons", "check", "tokens"])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--tokens")
    ap.add_argument("--mode", choices=["dark", "light"], default="dark", help="tokens: which column of the palette to use")
    ap.add_argument("--font", choices=["sans"], help="tokens: also set the system sans the dataviz method uses")
    ap.add_argument("--accent", help="tokens: replace the accent colour, for example a darker step of slot 1 on a light surface")
    ap.add_argument("--width", type=float, help="check: display width in px; default the viewBox width")
    a = ap.parse_args()
    if a.cmd == "tokens":
        if not a.spec:
            ap.error("tokens needs a palette file")
        over = tokens.from_palette(a.spec, a.mode, a.font)
        if a.accent:
            over["colors"]["accent"] = a.accent
        for name, back in (("bg", over["colors"]["bg"]), ("surface", over["colors"]["surface"])):
            ratio = check.contrast(over["colors"]["accent"], back)
            if ratio < tokens.load()["contrast"]["text"]:
                print(f"warning: the accent {over['colors']['accent']} is {ratio:.1f}:1 on the {name} colour, under 4.5:1; accent text (an accent edge label) will fail the contrast gate. "
                      f"Pass --accent with a {'darker' if a.mode == 'light' else 'lighter'} step of the same hue.", file=sys.stderr)
        text = json.dumps(over, indent=2) + "\n"
        if a.out:
            pathlib.Path(a.out).write_text(text)
            print(f"wrote {a.out}: {', '.join(f'{k} {v}' for k, v in over['colors'].items())}")
        else:
            print(text, end="")
        return
    if a.cmd == "check":
        if not a.spec:
            ap.error("check needs an SVG file")
        svg = pathlib.Path(a.spec).read_text()
        tok = tokens.load(a.tokens)
        errs, width, minfont = check.run_external(svg, tok, a.width, pathlib.Path(a.out) if a.out else None)
        print(f"{a.spec}: displayed at {width:g}px, smallest text {minfont:.1f}px  ->  {'PASS (partial)' if not errs else 'FAIL'}")
        for e in errs:
            print("   -", e)
        print("Partial check: palette, stroke and type scales, contrast, text size, text overlap and canvas edge. Arrowheads, grid, equal sizes and icon rules need a figure built by vg.py build.")
        sys.exit(1 if errs else 0)
    if a.cmd == "icons":
        d = pathlib.Path(__file__).parent / "icons"
        icons = json.loads((d / "lucide.json").read_text())["icons"]
        brands = json.loads((d / "brands.json").read_text())["brands"]
        brands.update(json.loads((d / "brands-extra.json").read_text())["brands"])
        q = (a.spec or "").lower()
        for n, i in icons.items():
            if q in n or any(q in t.lower() for t in i["tags"]):
                print(n, "-", ", ".join(i["tags"][:5]))
        for n, b in brands.items():
            if q in n or q in b["title"].lower():
                print(f"brand:{n} - {b['title']} logo")
        return
    if not a.spec or not a.out:
        ap.error("build needs SPEC and --out")
    spec = json.loads(pathlib.Path(a.spec).read_text())
    tok = tokens.load(a.tokens)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    name = pathlib.Path(a.spec).stem
    mod = TYPES[spec["type"]]
    failed, built = False, []
    for variant in tok["variants"]:
        try:
            svg = mod.build(spec, tok, variant)
        except ValueError as e:
            print(f"[{variant}] FAIL  {e}"); failed = True; continue
        W, bp = min_display_width(svg)
        (out / f"{name}-{variant}.svg").write_text(svg)
        errs, minfont = check.run(svg, tok, bp, out / f"{name}-{variant}.png")
        print(f"[{variant}] viewBox {W:g}px, valid from {bp:.0f}px, smallest text {minfont:.1f}px  ->  {'PASS' if not errs else 'FAIL'}")
        for e in errs:
            print("   -", e)
        failed |= bool(errs)
        built.append((variant, W, bp))
    if not spec.get("no_social"):
        try:
            svg, t2 = social.build(mod, spec, tok)
        except ValueError as e:
            print(f"[social] FAIL  {e}"); failed = True
        else:
            W, bp = min_display_width(svg)
            png = out / f"{name}-social.png"
            (out / f"{name}-social.svg").write_text(svg)
            errs, minfont = check.run(svg, t2, W, png, tok["social"]["scale"])
            errs += check.social_gates(svg, t2, png, bp)
            H = float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', svg).group(1))
            px = f"{round(W * tok['social']['scale'])}x{round(H * tok['social']['scale'])}"
            print(f"[social] feed image {px} PNG, ratio {H / W:.2f}, smallest text {minfont:.1f}px at a {W:g}px phone  ->  {'PASS' if not errs else 'FAIL'}")
            for e in sorted(set(errs)):
                print("   -", e)
            failed |= bool(errs)
    if built:
        brands = re.search(r'data-brands="([^"]+)"', svg)
        if brands:
            meta = json.loads((pathlib.Path(__file__).parent / "icons" / "brands.json").read_text())["brands"]
            meta.update(json.loads((pathlib.Path(__file__).parent / "icons" / "brands-extra.json").read_text())["brands"])
            print("Brand logos in this figure are the owners' trademarks. Use them only to name the product, and check the guidelines:")
            for slug in brands.group(1).split(","):
                print(f"   - {meta[slug]['title']}: {meta[slug].get('guidelines') or 'no guidelines link in the Simple Icons data'}")
        built.sort(key=lambda t: -t[2])
        src = "\n".join(f'  <source media="(min-width: {bp + tok["page_gutter"]:.0f}px)" srcset="{name}-{v}.svg">' for v, W, bp in built[:-1])
        fallback = built[-1][0]
        alt = spec["claim"].replace('"', "&quot;")
        (out / f"{name}.picture.html").write_text(
            f'<picture>\n{src}\n  <img src="{name}-{fallback}.svg" alt="{alt}" style="width:100%;height:auto;display:block">\n</picture>\n')
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
