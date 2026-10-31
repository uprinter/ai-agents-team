---
name: vector-gen
description: Generate diagrams and infographics as SVG, by code from a spec, not drawn by an image model, so they look finished on the first look, for the site and for posts. Sequence, flow, before/after, card and statistic grids, steps, hub-and-spoke, cycle, matrix, funnel and swimlane figures, with line icons or product logos, build from a spec through a token and craft-rule set and come out as SVG for the site and as a 1080px PNG for a LinkedIn post, gated by measured checks and judged by a fresh-eyes critic. Use for any architecture, flow or sequence diagram, comparison graphic or infographic; charts route to dataviz.
---

# Vector gen

Craft comes from rules encoded once (`toolkit/`), measured gates, and a critic who did not draw the figure. Hand-written SVG is for throwaway sketches only; shipped graphics come from the toolkit or an engine named below. A visual that is not a diagram (an icon, logo or illustration drawn by hand or exported from a tool) can be screened with `uv run toolkit/vg.py check FILE.svg`: palette, stroke, radius and type scales, contrast, text size, overlap and canvas edge. The check is partial and does not replace the look of RP-58 for such a visual; a hand-written diagram stays blocking (RP-59).

## Route by graphic

| Graphic | Path |
|---|---|
| sequence, flow, before/after, cards or statistics, steps or timeline, hub, cycle, matrix, funnel, swimlanes, layers, with or without icons | `toolkit/vg.py` (below); the form is the spec `"type"`: `sequence`, `flow`, `compare`, `cards`, `steps`, `hub`, `cycle`, `matrix`, `funnel`, `swimlanes`, `layers` |
| the same figure as an image for a LinkedIn post | automatic: `build` also writes `NAME-social.png` (1080px wide, 1:1 to 4:5); details in `references/craft-rules.md`, "Feed image" |
| another diagram or infographic form (timeline with dates, Venn, treemap) | add a form module beside `vg_lib/flow.py`, built on `vg_lib/prims.py` and `vg_lib/layout.py`, register it in `vg.py`, then follow the steps below |
| logo, symbol, tile (traced layers, a wordmark from font outlines, sizes 16-96) | `vg.py mark SPEC --out DIR`, spec `"type": "mark"`; the chain is `references/logo-craft.md` |
| chart | `dataviz` skill, then steps 4-5 |
| illustration, photo, cover art | not drawn here; `image-gen` makes raster, text goes on in code |

Icons: a node takes `"icon": "NAME"` for a line icon (Lucide, ISC) or `"icon": "brand:SLUG"` for a product logo (Simple Icons, CC0 files). `uv run toolkit/vg.py icons QUERY` searches both. To add one, put its name in `toolkit/icons/icons.txt` or `brands.txt` and run `build_icons.py` or `build_brands.py` on the unpacked npm package. A logo that Simple Icons does not carry (Oracle) goes by hand into `toolkit/icons/brands-extra.json`, one plain path with its viewBox; a logo that is not square is fitted into the icon box. Logos stay the owners' trademarks: the build lists each brand's guidelines link, use a logo only to name that product. Brands whose icon licence asks for attribution or share-alike are not in the set.

## Steps

1. **Claim.** Write the one sentence the picture proves. It becomes the `claim` in the spec and the alt text. Done when the sentence names a mechanism, not a topic, and every verb or comparison in it ("waits", "in parallel", "no longer") has a mark you can point at in the figure.
2. **Tokens.** Use the project's design document (`DESIGN.md`) for colours and font; write them as a token override JSON that changes only what differs from `toolkit/tokens/default.json`. When the project already has a `dataviz` palette file, make the override from it, so charts and diagrams share one palette: `uv run toolkit/vg.py tokens PALETTE.md --mode dark|light [--font sans] [--accent HEX] --out OVERRIDE.json`, then pass it to `build --tokens`. Done when every colour in the figure traces to a token.
3. **Build.** Write the spec (`examples/` holds one per type), run `uv run .claude/skills/vector-gen/toolkit/vg.py build SPEC --out DIR [--tokens OVERRIDE]`. Done when every variant prints `PASS`. A `FAIL` names the gate; fix the spec or shorten the label. Never loosen a gate to pass.
4. **Look.** Read each variant PNG yourself. Done when you can state, per image, what you checked in `references/craft-rules.md` principles.
5. **Critic.** Run the round in `references/critic.md`. Done on `NO DEFECTS` or after three rounds with open findings listed. For a figure that goes into a LinkedIn post, add the feed read of the same file (`feed-scroller` on the draft and `NAME-social.png`).
6. **Ship.** For the site, place the SVGs and the `<picture>` snippet from `DIR/NAME.picture.html`. For a post, upload `NAME-social.png`. Attach the PNGs to the MR. Commit the spec and the token override in the target project, beside the figure's evidence record: a figure rebuilds only from a committed spec, never from a scratchpad. A fix that generalises goes into the toolkit and `references/craft-rules.md`.

Needs `uv` and Chromium for Playwright (`uv run --with playwright playwright install chromium`).

## Reference

- `references/craft-rules.md` - scales, element rules, variants, gates, sources.
- `references/critic.md` - critic brief and loop.
- `references/logo-craft.md` - model image to working mark: trace, lettering, tile, size gates, tools and licences.
- `examples/` - `agent-flow.json` and `cache-aside.json` (sequence), `pipeline.json`, `pipeline-icons.json` and `retry-loop.json` (flow, the last with a back edge), `cache-aside-icons.json` (sequence with icons), `queue-compare.json` (compare), `agent-cards.json` and `agent-stats.json` (cards), `review-steps.json` (steps), `skill-hub.json` (hub), `harness-loop.json` (cycle), `priority-matrix.json` (matrix), `signup-funnel.json` (funnel), `release-lanes.json` (swimlanes), `logo-mark.json` (mark: layers, a wordmark and a tile), `app-layers.json` (layers: tinted groups, bars and a grid of independent modules). `agent-flow` and `queue-compare` are too dense for the feed image and switch it off.
