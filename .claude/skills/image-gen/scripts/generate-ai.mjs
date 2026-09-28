#!/usr/bin/env node
// generate-ai.mjs — general-purpose raster image generation via the Gemini image
// model (Gemini Developer API, "Nano Banana" / gemini-2.5-flash-image), no
// browser, no screenshots, no project coupling.
//
// Zero dependencies: Node standard library only (native fetch, Node 18+).
//
// Verified against https://ai.google.dev/api/generate-content and
// https://ai.google.dev/gemini-api/docs/image-generation (2026-08-24): the classic
// generateContent REST method remains fully supported for this model (the newer
// Interactions API is recommended for *new* features but generateContent is not
// deprecated) and is used here for its stable, well-documented contents/parts/inlineData
// shape.
//
// CLI:
//   node generate-ai.mjs --prompt "<text>" --out-dir <dir> [--ref <path>]... \
//                         [--count 1] [--name gen] [--model gemini-2.5-flash-image]
//
// Reads the API key from the GEMINI_API_KEY environment variable — set it in your
// shell profile (e.g. ~/.zshrc: `export GEMINI_API_KEY=...`), never in a project
// repo. The key is never printed, logged, or written to any output file.

import fs from 'node:fs';
import path from 'node:path';

const DEFAULT_MODEL = 'gemini-2.5-flash-image';
const API_BASE = 'https://generativelanguage.googleapis.com/v1beta/models';

const MIME_BY_EXT = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
};

function readApiKey() {
  const key = process.env.GEMINI_API_KEY;
  if (!key || !key.trim()) {
    throw new Error(
      'GEMINI_API_KEY is not set in your environment. Add "export GEMINI_API_KEY=<your key>" ' +
        'to your shell profile (e.g. ~/.zshrc) and open a new shell, then retry. This key is ' +
        'a personal credential, not project config — never put it in a repo.'
    );
  }
  return key.trim();
}

function parseArgs(argv) {
  const args = { ref: [], count: 1, name: 'gen', model: DEFAULT_MODEL };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      i++;
      if (i >= argv.length) throw new Error(`${a} requires a value`);
      return argv[i];
    };
    if (a === '--prompt') args.prompt = next();
    else if (a === '--ref') args.ref.push(next());
    else if (a === '--out-dir') args.outDir = next();
    else if (a === '--count') args.count = Number(next());
    else if (a === '--name') args.name = next();
    else if (a === '--model') args.model = next();
    else throw new Error(`Unknown argument: ${a}`);
  }
  if (!args.prompt) throw new Error('--prompt is required');
  if (!args.outDir) throw new Error('--out-dir is required');
  if (!Number.isInteger(args.count) || args.count < 1) {
    throw new Error('--count must be a positive integer');
  }
  return args;
}

function loadReferenceImageParts(refPaths) {
  return refPaths.map((refPath) => {
    const ext = path.extname(refPath).toLowerCase();
    const mimeType = MIME_BY_EXT[ext];
    if (!mimeType) {
      throw new Error(`Unsupported reference image extension "${ext}" for ${refPath} (expected .png/.jpg/.jpeg/.webp)`);
    }
    const data = fs.readFileSync(refPath).toString('base64');
    return { inline_data: { mime_type: mimeType, data } };
  });
}

// Generates one candidate image. The Gemini image model returns a single image per
// call regardless of generationConfig.candidateCount, so multi-candidate requests loop
// this rather than relying on the server to batch them.
async function generateOne({ apiKey, model, prompt, referenceParts }) {
  const url = `${API_BASE}/${model}:generateContent`;
  const parts = [{ text: prompt }, ...referenceParts];
  const body = { contents: [{ parts }] };

  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': apiKey,
      },
      body: JSON.stringify(body),
    });
  } catch (err) {
    throw new Error(`Network error calling Gemini API: ${err.message}`);
  }

  const responseText = await response.text();
  if (!response.ok) {
    throw new Error(
      `Gemini API request failed: HTTP ${response.status} ${response.statusText}\n${responseText}`
    );
  }

  let json;
  try {
    json = JSON.parse(responseText);
  } catch {
    throw new Error(`Gemini API returned non-JSON response (HTTP ${response.status}):\n${responseText}`);
  }

  const candidateParts = json?.candidates?.[0]?.content?.parts;
  if (!Array.isArray(candidateParts)) {
    throw new Error(`Gemini API response had no candidates/content/parts:\n${JSON.stringify(json, null, 2)}`);
  }

  const imagePart = candidateParts.find((p) => p.inline_data || p.inlineData);
  if (!imagePart) {
    const textPart = candidateParts.find((p) => p.text);
    throw new Error(
      `Gemini API returned no image data.` +
        (textPart ? ` Model said: ${textPart.text}` : ` Raw parts: ${JSON.stringify(candidateParts)}`)
    );
  }

  const blob = imagePart.inline_data || imagePart.inlineData;
  const base64Data = blob.data;
  const mimeType = blob.mime_type || blob.mimeType || 'image/png';
  if (!base64Data) {
    throw new Error('Gemini API image part had no base64 data.');
  }
  return { buffer: Buffer.from(base64Data, 'base64'), mimeType };
}

function extForMime(mimeType) {
  if (mimeType === 'image/jpeg') return '.jpg';
  if (mimeType === 'image/webp') return '.webp';
  return '.png';
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const apiKey = readApiKey();
  const referenceParts = loadReferenceImageParts(args.ref);

  fs.mkdirSync(args.outDir, { recursive: true });

  for (let i = 1; i <= args.count; i++) {
    const { buffer, mimeType } = await generateOne({
      apiKey,
      model: args.model,
      prompt: args.prompt,
      referenceParts,
    });
    const ext = extForMime(mimeType);
    const filename = args.count === 1 ? `${args.name}${ext}` : `${args.name}-${i}${ext}`;
    const outPath = path.join(args.outDir, filename);
    fs.writeFileSync(outPath, buffer);
    console.log(`wrote ${outPath} (${buffer.byteLength} bytes)`);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error(`generate-ai.mjs failed: ${err.message}`);
    process.exit(1);
  });
}

export { parseArgs, generateOne, readApiKey };
