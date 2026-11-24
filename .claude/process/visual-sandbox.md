# Visual sandbox

The sandbox finds the look of a new visual element before delivery builds it. Search and build are separate: the sandbox iterates fast with no gates, and delivery builds the chosen variant once, with the gates of its lane and stage (→ RP-102).

## When

A new or redesigned visual element that shows data or carries a page (a card, a panel, a page section) and for which the founder has no sample starts in the sandbox, at every lane and stage. An icon or a control with a standard pattern, and any element with a sample, keeps the render sheet of `gates.md` (→ RP-75). The founder can ask for the sandbox for any visual change.

## Who

The root session dispatches one `senior-software-engineer` directly, with this file named in the brief. No coordinator, product owner, reviewer, critic or tester takes part, and no spec, MR or `/verify` entry is made: the sandbox is not `/implement` and ships nothing. The engineer does not merge or deploy sandbox code. Every round goes to the same engineer, resumed with the founder's reply; a new instance starts from the saved pages.

## Steps

1. **Inputs.** The founder's request in their words and 5–10 genre references: screenshots of other products that show the same kind of data well. References give direction only; a variant never copies one. When the founder has none, the engineer proposes ten and the founder keeps 5–10.
2. **Directions.** The engineer builds 4–6 variants that differ in concept: layout, hierarchy, the main visual idea. A change of colour, stroke or spacing alone is not a separate variant. Each variant has a one-line name and uses real data, captured from production or the live API, never invented values.
3. **One page.** All variants stand on one static page, at real size on the real background, at ~375 px and desktop. Each round's page and its screenshots are saved at `sandbox/<slug>/round-<n>/` before the engineer's turn ends, and the hand-back names that path. The founder gets the screenshots with no other text than the variant names.
4. **Rounds.** The founder picks one, combines parts of several, or rejects all. Each next round shows 2–3 variants of the pick. After three rounds with no pick, the engineer asks the founder for new references before building more.
5. **States.** The picked variant is shown on one page in every data state: empty, shortest, longest and boundary values. This page is the screenshot set that `product-owner.md` §6 asks for.
6. **Hand-off.** The founder's pick of the states page is the approved sheet (`sheet=founder-ok`). Delivery then builds exactly that variant through the normal intake, at the lane and stage of the change; the MR links the states page and states the number of sandbox rounds. The built element is compared with the states page side by side: by the reviewer at `live`, by the founder's look at `pre-users`.

Done when the founder has picked one variant on the states page, or has stopped the search.

## Where the code lives

Outside the product build: a `sandbox/<slug>` branch that is never merged, or a folder the target's instructions name. Sandbox code is a prototype; delivery rewrites it to the project's standards and keeps the look. A sandbox round is not a founder rejection in the sense of `harness-quality-loop.md` §3; a rejection after hand-off is.
