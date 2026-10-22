# Critic round

A fresh agent looks at the renders and names what a designer would fix. It has not seen the spec, the code or the author's reasoning, so it cannot be talked out of what it sees. Gates are green before this round starts; the critic judges what measurement cannot.

## Brief (copy into the Agent prompt, fill the brackets)

> You are a visual design critic. Open these images with the Read tool: [absolute PNG paths, one per width variant]. They show one figure at [widths]. The figure claims: "[claim sentence]". Judge only what you see.
>
> Look in this order: (1) Does the claim land in five seconds? (2) Hierarchy: is the one important thing the most prominent? (3) Rhythm: equal parts equal, spacing even, alignment on shared edges. (4) Joints and corners: are rounded corners placed where a shape is free, square where shapes join? (5) Marks: arrowheads, line weights and radii proportional to each other; anything too small, too heavy or too light. (6) Text: placement against lines and boxes, wraps, crowding. (7) Balance and emptiness: lopsided areas, dead space, cramped edges. (8) Looks finished or generated?
>
> Report at most three findings, most damaging first. Label each DEFECT (a designer would send the figure back: wrong, ambiguous, broken rhythm or proportion, claim not shown) or POLISH (would improve, not required). Each finding: which image, where in the image, what is wrong, one concrete fix in design terms (a proportion, a corner, a position), and how sure you are (high, medium, low). Describe positions relative to neighbouring elements, not in pixels; you see a scaled image. If no DEFECT remains, answer exactly `NO DEFECTS` and list POLISH items only if you have them. Do not praise. Do not suggest redesigns of the whole figure.

## Loop

1. Run the critic on every variant PNG in one call.
2. Fix every DEFECT, and POLISH items that cost little, in the spec, token override or toolkit. Treat low-confidence findings as questions: check them in the render yourself. A fix that generalises goes into the toolkit and `craft-rules.md`, so the next figure gets it free.
3. Rebuild, gates green, run the critic again with a fresh agent.
4. Stop on `NO DEFECTS` or after three rounds. After three rounds, ship with the open findings listed in the report.

The completion criterion is `NO DEFECTS` from an agent that did not draw the figure, on every variant. A critic always finds something to polish; only DEFECT counts against shipping.
