# Logo craft: from a model image to a working mark

The model gives the idea. Code and tools give the craft. A model image is never the shipped file: it has no vector, no transparency, lettering with uncontrolled weight and spacing, and no small-size tile. The `mark` form (`toolkit/vg_lib/mark.py`, `vg.py mark`) builds the shipped file from a spec.

## Chain

1. **Idea.** `image-gen` with `--background COLOUR --meta`: a flat background, references of the real mascot, one or two candidates. The accepted image becomes the source file; later edits pass it as `--ref` with "change only X" (image-gen, "An accepted image is the source").
2. **Flat colours.** Reduce the accepted image to 4-6 flat colours. Done when each region is one colour and no gradient is left.
3. **Trace by layer.** One layer per colour with `vtracer` (colour) or `potrace` (one layer at a time), then clean the contours by hand: fewest nodes, no stray specks, `svgo` for the final file. Each cleaned layer becomes a `layers[].d` entry in the spec.
4. **Lettering from a font.** The wordmark is set from font outlines in the spec (`wordmark`: font file, size, `tracking`, `kern` pairs, variable-font `axes` such as weight, softness, optical size). The model's lettering is discarded. A kerning pair is judged by the gap between letter shapes, not by the advance widths.
5. **One stroke.** Where two shapes must read as one (a tail that flows into a letter), list them in `layers[].union`; the build merges them into one outline (needs `skia-pathops`). Inkscape does the same by hand as an external tool only.
6. **Tile.** The 16, 24 and 32 px tile is drawn by hand on its own pixel grid (`tile`: grid, palette, rows), never scaled down from the large mark. It keeps the one feature that carries the idea and drops the rest. Start from a render with `shape-rendering="crispEdges"` (`resvg -w 24`) for the silhouette only: an anti-aliased render snapped to the palette turns small features into noise. Then place every feature pixel by hand, symmetric halves mirrored, with a row of the base colour between features that must not merge.
7. **Sizes and recognition.** `vg.py mark` renders 16, 24, 32, 48 and 96 px and a sizes sheet. Gates: at most 6 flat colours, the mark does not vanish or fill the box at small sizes. Then show the sheet at 1:1 for one second to five people and ask what it is; the mark passes when four of five name the product's idea.
8. **Critic.** `critic.md` round on the 96 px render and the sizes sheet, ending `NO DEFECTS` (→ RP-67).
9. **Record.** Commit the spec, the cleaned layer files and the image-gen `.json` records beside the figure: the prompt, references and sha256 of every file.

## Tools (reviewed before any install)

| Tool | Licence | Use | Note |
|---|---|---|---|
| vtracer | MIT | colour trace | Python library through `uv run --with vtracer` |
| potrace | GPL-2.0 | one-colour trace per layer | run as a separate program; a non-GPL licence is sold if linked into a product |
| svgo | MIT | shrink the SVG | node tool |
| fontTools | MIT | font outlines, kerning, variable axes | `uv run --with fonttools`; the wordmark gate needs it |
| skia-pathops | BSD-3-Clause | union of paths | `uv run --with skia-pathops` |
| Inkscape | GPL-3.0 | manual boolean and clean-up | external program only, never in the toolchain |
| resvg | MPL-2.0 | SVG render without a browser | optional; Chromium already renders the sizes |

Installed 2026-10-28 with the founder's approval: `brew bundle --file=.claude/skills/vector-gen/toolkit/Brewfile` (potrace, svgo, resvg, Inkscape). vtracer has no Homebrew formula: `uv run --with vtracer`. fontTools and skia-pathops: `uv run --with fonttools --with skia-pathops`. A new tool beyond this list needs approval again.

## Legal note

A purely AI-made image has weak copyright protection in most places; protection needs human authorship. The lettering, the cleaned shapes and the tile are that human (and code) work, so keep them in the repository history. Read the Gemini terms for commercial use of outputs before the mark ships as a brand.

## First run, 2026-10-28 (a product logo)

Steps 2 to 4 ran end to end on the accepted candidate (source sha256 `cc1cf618...b4c`):
- Flat colours: median-cut spent its colours on shades of the navy background. Fix: sample a fixed palette from the image (background, indigo, cream, skin, ink) and map every pixel to the nearest one.
- Trace: `vtracer` with `color_precision=8`, `layer_difference=8`, `filter_speckle=24`, then `svgo` (-31%). Snap each traced fill to the palette, bake the `translate` into the path, and merge only back-to-back runs of one colour: grouping by colour broke the stacking and hid the pupils.
- The result is a 5-colour mark in 11 stacked layers. `vg.py mark` passed; `union` on three cream layers ran with `skia-pathops`; the wordmark from Georgia Bold rendered from outlines.
- Open: the tail still ends in a straight cut where the model's S began; the S is set from the font, so the tail must be redrawn to run into it. Fraunces Soft is not installed; Georgia stood in. The eye glints and the 16/24 px tile are not done. Those are the human or design steps.

## Second run, 2026-10-28 (cartoon mouse head, private exercise)

A 16-layer, 5-colour vector with two `union` outlines (the rim and the face mask, built from `part` layers) passed the gates and had no craft defect in any critic round (round one flagged the likeness to a known character, out of scope for the exercise). The 24 px tile reached no defects after three rounds. The 16 px tile still had two open defects after the third round: the ears were too flat and fused into the crown, so the head read as a haircut, and the mouth read as a block, not a smile. A second loop of three rounds fixed both (ears as discs cut from the crown, a black-outlined mouth with lifted corners and skin under it, tall eyes with the pupil low). In that loop the critics reversed each other twice (black head sides, then a 2x2 eye, each undone by the next round), so a finding that undoes an earlier accepted fix is settled against the vector, not by the newest critic. Lesson: at 16 px a character survives only by its silhouette (round ears separated from the crown by a background pixel) and one expression mark with its corners lifted; the gate cannot see either, only the critic can.
