---
name: viv-mind
description: "Harvest links/videos shared in Telegram, journal them, generate a watercolor infographic, render an Instagram-style feed, and push to GitHub."
homepage: https://github.com/vivmuk/viv-mind
metadata:
  openclaw:
    emoji: 🧠
    requires:
      bins: ["python3", "git"]
      env: ["VENICE_API_KEY", "GITHUB_TOKEN"]
      pip: ["requests", "beautifulsoup4", "openpyxl", "yt-dlp", "pypdf"]
    primaryEnv: VENICE_API_KEY
---

# viv-mind

When you drop a link, video URL, or document in Telegram, **viv-mind** asks:

> Is this for Viv Mind?

After you confirm, it harvests the source, appends structured metadata to
`data/viv-mind-journal.xlsx`, generates a detailed watercolor infographic with
Venice AI image models (default `flux-2-max`, override with `--model gpt-image-2`;
magenta/blue/orange whimsical palette, 1024×1280 portrait),
renders an Instagram-style HTML feed page, sends the infographic image back to
Telegram, and pushes the update to the private repo `github.com/vivmuk/viv-mind`.

## Trigger

1. User sends a URL or document in Telegram.
2. Main agent detects a URL/document and calls this skill.
3. Skill replies with: **"Is this for Viv Mind?"**
4. On confirmation (`yes`, `y`, ✅, 👍), run the save pipeline.

## Workflow

```text
URL in Telegram
       │
       ▼
  ask("Is this for Viv Mind?")
       │
       ├── no / cancel → abort
       │
       └── yes
            │
            ▼
    python3 scripts/harvest.py <url>
            │
            ▼
    python3 scripts/journal.py --add <harvested.json>
            │
            ▼
    python3 scripts/infographic.py --id <uuid>
            │
            ▼
    python3 scripts/site.py
            │
            ▼
    python3 scripts/push.py
```

## File layout

```text
~/.openclaw/workspace/skills/viv-mind/
├── SKILL.md
└── scripts/
    ├── harvest.py      # URL detection + content extraction
    ├── journal.py      # Excel journal CRUD
    ├── infographic.py  # Venice AI watercolor infographic
    ├── site.py         # Instagram-style HTML feed
    └── push.py         # git commit + push (Railway hosts the feed)
```

Runtime data lives in the local scaffold repo at
`~/.openclaw/workspace/viv-mind-scaffold/`:

```text
viv-mind-scaffold/
├── docs/
│   └── index.html        # rendered feed
├── data/
│   └── viv-mind-journal.xlsx
├── assets/
│   └── infographics/     # PNG images
├── README.md
└── .gitignore
```

## Dependencies

- `python3` 3.10+
- `git`
- Python packages: `requests`, `beautifulsoup4`, `openpyxl`, `yt-dlp`
- Environment variables:
  - `VENICE_API_KEY` — required for image generation
  - `GITHUB_TOKEN` — required for push to GitHub repo (repo scope)

Install deps:

```bash
pip3 install requests beautifulsoup4 openpyxl yt-dlp
```

## Environment setup

```bash
export VENICE_API_KEY="vn_..."
export GITHUB_TOKEN="ghp_..."
```

Or configure via OpenClaw/Clawdbot skill env.

## Usage

### One-shot save from a URL

```bash
URL="https://example.com/article"
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/harvest.py "$URL" > /tmp/harvest.json
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/journal.py --journal ~/.openclaw/workspace/viv-mind-scaffold/data/viv-mind-journal.xlsx add /tmp/harvest.json
ID=$(python3 -c "import json; print(json.load(open('/tmp/harvest.json'))['id'])")
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/infographic.py --id "$ID"
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/site.py
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/push.py
# Then send assets/infographics/<id>*.png back to Telegram.
```

### Regenerate an infographic for an entry

```bash
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/infographic.py --id <entry-id>
```

### Force rebuild site + push

```bash
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/site.py
python3 ~/.openclaw/workspace/skills/viv-mind/scripts/push.py
```

## Notes

- `harvest.py` falls back to generic HTML scraping when a site blocks requests.
- YouTube/TikTok transcripts are captured via `yt-dlp` when available.
- `push.py` pushes to `vivmuk/viv-mind` as a private repo and does **not** enable GitHub Pages.
- Generated image prompts are tuned for `gpt-image-2` at 1024×1280 portrait (Venice max 1280 height).
- After generation, the infographic PNG is sent back to the originating Telegram chat.
