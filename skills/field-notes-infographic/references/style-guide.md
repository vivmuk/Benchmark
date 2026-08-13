# Field Notes Infographic — Style Guide

## Aesthetic ("Field Notes Journal")

- **Orientation**: vertical 9:16 Instagram-ready infographic
- **Paper**: cream #FEFCF8 with torn edges, washi tape, sticky notes, coffee stains
- **Ink**: handwriting annotations, arrows, underlines in teal #00D4AA + indigo #1A1A2E
- **Elements**: speech-bubble quote, tag chip, stamp-style date, footer badge
- **Tone**: warm, inspiring, evidence-first; clean readable typography, never cluttered

## API recipe (Venice-native)

- `POST https://api.venice.ai/api/v1/image/generate`
- Auth: `Authorization: Bearer $VENICE_API_KEY`
- Model: `grok-imagine-image-2-0`
- `aspect_ratio: "9:16"`, `resolution: "2K"`, `format: "png"`, `safe_mode: false`
- Prompt limit: **7500 chars** (model spec, verified live 2026-08-13 with a 2120-char prompt).
  The 1500-char cap applies ONLY to the OpenAI-compatible `/api/v1/images/generations`.
- Response: JSON `{"images": ["<base64>"]}` → base64-decode to PNG
- Cost: ~$0.10/image @2K, ~$0.07 @1K

## database.json schema

```json
{
  "series": "...", "creator": "...", "url": "...",
  "episodes": [{
    "ep": 0, "date": "2026-08-06", "title": "...", "duration_s": 84.3,
    "key_message": "...", "quote": "...", "tag": "procrastination"
  }]
}
```

## Prompt templates

See `templates/daily-prompt.txt` and `templates/weekly-prompt.txt`.
Placeholders: `{brand}`, `{series}`, `{ep}`, `{date}`, `{title}`, `{key_message}`, `{quote}`, `{tag}`, `{total}`, `{week_label}`, `{listing}`.

## Naming & output

- Daily: `ep{NN}-{slug}.png` (slug = lowered title, non-alnum → `-`, ≤ 40 chars)
- Weekly: `weekly-week{N}.png` (7-day weeks from series start; label `Week N (Mon–Sun)`)
- Manifest: `manifest.json` with `{generated, dailies[], weekly[]}`

## Integration

`daily_pipeline.sh` / `update_site.sh` → `generate_infographics.py` → git push → Railway auto-deploy
(live: https://messy-action-site-production.up.railway.app/).
