---
name: "field-notes-infographic"
description: "Generate 9:16 hand-drawn 'field notes' infographics (per-item + weekly summaries) via Venice grok-imagine-image-2-0."
---

# Field Notes Infographic

Generate vertical 9:16 "field notes" infographics from a JSON archive: one image per
item (daily) plus one weekly summary. Venice `grok-imagine-image-2-0`, cream paper +
teal/indigo handwritten aesthetic.

## When to use
- Batch infographics for an episode/series archive.
- Recreating the Messy Action look: per-episode + weekly-summary field notes.

## Workflow
1. Prepare `database.json` — `episodes[]` with `ep, date, title, key_message, quote, tag`.
2. Run `scripts/generate_infographics.py --db database.json [--out DIR] [--site DIR] [--brand ...] [--series ...]`.
3. Idempotent: skips existing files, writes `manifest.json`, mirrors to site dir.
4. Verify output PNGs before pushing.

## Files
- `scripts/generate_infographics.py` — generator (python3, stdlib only)
- `references/style-guide.md` — aesthetic, API recipe, prompt templates, schema
- `templates/daily-prompt.txt` / `templates/weekly-prompt.txt` — exact prompts
- `assets/example-daily.jpg` / `assets/example-weekly.jpg` — output examples

## Key facts (verified 2026-08-13)
- Endpoint: `POST /api/v1/image/generate` (Venice-native); model `grok-imagine-image-2-0`
- Prompt cap: **7500 chars** per model spec (the 1500 cap applies only to `/images/generations`)
- Params: `aspect_ratio 9:16`, `resolution 2K`, `format png`, `safe_mode false`
- Auth: `Bearer $VENICE_API_KEY` (env file: `~/.openclaw/service-env/ai.openclaw.gateway.env`)
- Cost: ~$0.10/image @2K
