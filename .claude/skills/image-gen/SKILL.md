---
name: image-gen
description: Generate raster images (PNG/JPEG/WebP) from a text prompt via Google's Gemini image model ("Nano Banana") through a direct API call — no browser automation, no screenshot-cropping. Use whenever a task calls for an actual image to be generated — an illustration, icon, mascot, banner, product photo mockup, texture, or any other raster artwork — not just when Gemini is named explicitly. Requires GEMINI_API_KEY set in the user's shell environment.
---

# Image Generation Skill

Bundles a small, zero-dependency Node script that calls the Gemini Developer API's
image model directly over REST and writes clean image files to disk — a general
raster-image-generation utility, not scoped to any particular project, brand, or
subject matter. A direct API call avoids the failure modes of driving an AI image
tool's web UI through browser automation (screenshot-cropping the result bakes in
cursor icons, UI chrome, and wrong backgrounds).

This is a plain general-purpose tool — the script takes a prompt and optional
reference images as arguments and returns image files. Any project needing an
image generated uses the same tool rather than reinventing it or copying it into
a project repo.

## Prerequisite: `GEMINI_API_KEY`

The script reads this from the environment, not from any file. Set it once in your
shell profile:

```bash
# in ~/.zshrc (or ~/.bashrc)
export GEMINI_API_KEY=your-ai-studio-key
```

Open a new shell (or `source ~/.zshrc`) after adding it. This is a personal
credential — it must never live inside a project repo, committed or not. Get a key
from Google AI Studio if you don't have one.

If the key is missing or empty, the script fails loudly with a clear message
rather than silently doing nothing. It never prints, logs, or writes the key value
anywhere.

## Use it responsibly — this is billed per call, not a flat subscription

Every invocation costs real money (per-image, not a fixed monthly fee) — there is
no free-tier ceiling backstopping careless use. Don't generate more candidates than
the task actually needs "just in case," don't loop retries blindly on a bad prompt
without first fixing the prompt, and don't regenerate something that already
exists and is still good. Default to the minimum count that lets a human make a
real decision (often 1, rarely more than 2-3), and iterate the prompt/reference
images between calls rather than brute-forcing many candidates per attempt.

## How to run it

```bash
node ./scripts/generate-ai.mjs \
  --prompt "<detailed description of the desired image>" \
  --out-dir <directory to write results into> \
  [--ref <path-to-reference-image>]... \
  [--count 3] \
  [--name candidate] \
  [--model gemini-2.5-flash-image]
```

- `--prompt` — required. Be specific and exhaustive: subject, composition, exact
  details required, palette, background, and anything that must *not* appear
  (the model does not infer omissions correctly by default).
- `--ref` — repeatable. Pass one or more existing images (PNG/JPG/WebP) as visual
  reference input to keep a new generation visually consistent with something
  already approved (same subject, same style, a specific pose/angle) rather than
  getting a fresh, unrelated result each time.
- `--out-dir` — required. Files are written here as plain PNG/JPEG/WebP; nothing
  is committed to git by this script — that decision belongs to whoever calls it.
- `--count` — how many independent candidates to generate (the model returns one
  image per call, so this loops the request rather than trusting a batch
  parameter).
- `--model` — override if a newer/different Gemini image model id is current;
  check `https://ai.google.dev/gemini-api/docs/image-generation` for the current
  recommended model rather than assuming the default stays right forever.

## When to reach for this vs. something else

- Use this for actual raster image generation of any kind.
- Don't use this for logo/wordmark typography-only work, UI mockups, or landing
  page layout — those are better served by the `design` skill or the
  `frontend-design`/`hallmark` skills.
- If the target output must be a true vector (editable SVG paths), this script
  won't give you that — it returns raster images. Investigate a vector-native
  generation API (e.g. Recraft) separately if that requirement is hard, or
  accept raster and vectorize afterward only if actually needed.

## Known limitation to flag to the user

Gemini's own image model does not currently support Vertex AI or `gcloud`-based
auth as a lower-friction alternative in every environment — this script only
supports the Gemini Developer API key path. If the user already has GCP/Vertex AI
set up and prefers that auth path, that would need to be added as a second mode
rather than assumed to already work here.
