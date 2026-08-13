# Paridhi's Long-Term Memory 🦚

## AIPharmaXchange Mission
Grow to 2000 pharma professionals via 3 pillars:
- **Pillar 1 — Newsletter**: 800 subscribers (+50/week, 45%+ open rate)
- **Pillar 2 — LinkedIn**: 1200 followers (+40/week, 3%+ engagement, 1 viral/month)
- **Pillar 3 — Advocacy**: 200 members via GitHub, Twitter/X, Reddit, conferences

## Venice AI Image API
- **Endpoint**: POST https://api.venice.ai/api/v1/image/generate
- **Auth**: Bearer VENICE_INFERENCE_KEY_[REDACTED]
- **Prompt cap CORRECTED 2026-08-13**: the 1500-char cap applies ONLY to the OpenAI-compatible endpoint `/api/v1/images/generations`. The Venice-native `/image/generate` honors each model's `promptCharacterLimit` from `GET /models?type=image`. Verified live: `grok-imagine-image-2-0` spec limit = **7500**, and a **2120-char prompt generated fine** (HTTP 200).
- **Response format**: images[] base64 (decode to PNG bytes)
- **Params**: model, prompt, height, width, aspect_ratio, resolution, format, cfg_scale, negative_prompt, steps, style_preset, seed, variants, safe_mode, enable_web_search, return_binary, lora_strength, quality
- **Best models**: grok-imagine-image-2-0 (2K, 9:16, 7500-char prompts, $0.10 — field-notes infographics), gpt-image-2 (highest quality, 4K + 16:9), flux-2-max (fast, good), nano-banana-2 (32K spec)

### Model Prompt Limits (/image/generate, per model spec)
| Model | Spec Limit | Cost/2K | Best For |
|-------|-----------|---------|----------|
| grok-imagine-image-2-0 | 7.5K (verified) | $0.10 | Field-notes infographics, 9:16 |
| gpt-image-2 | 10K | ~$0.27+ | Detailed infographics, 4K |
| nano-banana-2 | 32K | ~$0.10-0.19 | Long-prompt infographics |
| flux-2-max | 3K | $0.09 | Quick visuals |
| flux-2-pro | 3K | $0.04 | Budget visuals |
| venice-sd35 | 1.5K | $0.01 | Batch/budget (1:1 only) |

⚠️ If using `/images/generations` (OpenAI-compat) instead, prompt is capped at 1500 chars.

Full catalog: ~/.paperclip/workspaces/aipharmaxchange/venice-image-api-reference.md

## Paperclip AI Org
- **API**: http://127.0.0.1:3100/api
- **Company ID**: 05f511f6-0e22-4d8a-ae55-fc17202944c4
- **9 Agents**: CEO(1) + LinkedIn(2) + Content(2) + Newsletter(2) + Research(1) + GitHub(1)
- **3 Venice LLM Models**: Nemotron 3 Ultra 550B (6 agents), DeepSeek V4 Pro (2 agents), Gemma 4 Uncensored (1 agent)
- **3 Projects**: LinkedIn Growth, Newsletter Growth, Advocacy & GitHub
- **5 Goals**: LinkedIn 1200 followers, Newsletter 800 subs, Advocacy 200 members, 1→5+ content repurposing, 100% DESIGN.md compliance
- **Full org reference**: ~/.paperclip/workspaces/aipharmaxchange/ORG_REFERENCE.md

## Open Design
- **Daemon**: http://127.0.0.1:7456 (155 skills including 5 native Venice skills)
- **Design System**: /tmp/open-design/design-systems/aipharmaxchange/DESIGN.md
- **Native Venice Skills**: venice-audio-music, venice-audio-speech, venice-image-edit, venice-image-generate, venice-video

## Brand Guidelines (DESIGN.md)
- **Teal**: #00D4AA (primary)
- **Cream**: #FEFCF8 (background)
- **Indigo-black**: #1A1A2E (text)
- **Fonts**: Fraunces Variable (headlines), Inter Variable (body)
- **Style**: Watercolor wash, evidence-first tone, pharma-professional

## Identity
- Name: **Paridhi** (Sanskrit for "intellect")
- Vibe: Scientific, innovative, teaching-first, six-sigma positive deviation
- Role: Innovation partner, model tester, teacher + support
- Emoji: 🧬
- Created: 2026-07-04

## User Preferences
- Vivek M (@vivgatesai on GitHub)
- Telegram chat_id: 6808691714
- Prefers Venice API for all AI tasks
- Wants credentials wiped from config files after email use
- Wants Paridhi to be always innovative, scientifically accurate, and a teaching partner
- **Hates fabricated completion claims**: always verify subagent/background work before reporting it done. Never claim files were emailed unless confirmed.
- **Expects me to take criticism and fix process**: when called out on mistakes, acknowledge, correct, and update rules so it doesn't recur.

## #unique List (Things That Make Me Unique)
- **File**: `~/.openclaw/workspace/things-that-make-me-unique.md`
- **Convention**: whenever Vivek sends a message containing `#unique`, append everything after the tag as a new numbered entry to that file (with date). Never overwrite or reorder existing entries.
- **Weekly email**: cron job fires Sundays 18:00 ET (America/New_York), reads the list, emails it to **vivek@live.de** via himalaya (account `gmail`), and announces the result to Telegram.
- First planned send: 2026-08-16.

## MessyAction Site — Railway Deploy (2026-08-13)
- **Live**: https://messy-action-site-production.up.railway.app/ (NO GitHub Pages — user migrate to Railway)
- Railway project `messy-action`, service `messy-action-site` ← GitHub repo `vivmuk/messy-action-transcripts` (main) → **auto-deploy on push**
- Build: Dockerfile (python:3.12-slim + http.server); railway.json builder=DOCKERFILE (RAILPACK lacked python → crash fixed 2026-08-13)
- Site: swipeable field-notes UI (index.html), self-updating via database.json + infographics/manifest.json
- Infographics: ~/Downloads/MessyAction/generate_infographics.py — daily per-ep + weekly summary (grok-imagine-image-2-0, 9:16 @2K, prompt <1500 chars), idempotent, mirrors to site/infographics/
- Pipeline: daily_pipeline.sh runs generator, then commit+push (Railway auto-deploys)
- **Skill**: `field-notes-infographic` (workshop, applied 2026-08-13) = full style guide: palette (cream #FEFCF8, teal #00D4AA, indigo #1A1A2E, washi tape/coffee stains), Venice recipe (grok-imagine-image-2-0, 9:16, 2K, prompt ≤1450 chars), daily + weekly prompt templates
- **Dedicated cron** e0aac451: daily 23:30 ET runs ~/Downloads/MessyAction/update_site.sh (rebuild DB → generate infographics → push → Railway); announces PUSHED to TG, NO_REPLY on CLEAN
- Style guide emailed to vivek@live.de 2026-08-13 (with example images)

## Email (himalaya) — FIXED 2026-08-10
- Config: ~/.config/himalaya/config.toml — **v1.2.0 schema** (backend.* + message.send.backend.* blocks). Old v0.x format broke sends.
- Gmail app password stored at ~/.config/himalaya/gmail-app-password (chmod 600) — auth via `backend.auth.cmd = "cat ..."`.
- Verified working: IMAP read + SMTP send to vivek@live.de (unique list email sent successfully 2026-08-10).
- himalaya v1.2.0 flag: mailbox = `-f/--folder` (NOT `-m`).

## BenchmarkViv Site (venice-benchmark-site)
- **Location**: ~/.openclaw/workspace/benchmarks/venice-benchmark-site/
- **Design tokens**: teal #00D4AA / cream #FEFCF8 / indigo #1A1A2E (unified 2026-08-10 across all pages + infographics)
- **18 models** in registry (added kimi-k3-fast-api 2026-08-10, live benchmarked, now #1 with VivIndex 93.06)
- **Always #1 highlighted**: gold crown/border/badge (compare cards, VivIndex chart, infographic board)
- **Per-model pages**: `models/<slug>.html` via `make_model_pages.py`; compare cards link to them
- **Mobile**: stacked mobile infographic via `<picture>`; safe-area padding; `.img-zoom` lightbox on tap
- **Standalone trap**: raw responses contain `</script>`; generate_standalone.py MUST escape as `\u003c/script`-style (`</script`) or the page dumps raw JSON text
- **Rebuild pipeline**: run benchmark (run_new_model.py) → make_chart.py → make_svg_chart.py → make_infographic_2x2.py → make_model_pages.py → generate_standalone.py
- Local preview: `python3 -m http.server 8080` in site dir

## GitHub Push Auth (FIXED 2026-08-10)
- Repo: ~/.openclaw/workspace → github.com/vivmuk/Benchmark.git (branch main)
- `gh` CLI token was INVALID (expired); SSH key rejected. Do NOT rely on `gh auth status`.
- Fix: classic PAT stored in **macOS keychain** via `git credential approve` + `credential.helper osxkeychain`; git pushes now work.
- gh login requires `read:org` scope — classic PATs without it fail `gh auth login --with-token`, but git push works fine with just repo scope.
- If push auth breaks again: `printf 'protocol=https\nhost=github.com\nusername=vivmuk\npassword=<PAT>\n' | git credential approve`.

## Paridhi Operating Rules
- Verify before claiming completion: check file existence, content, and side effects.
- Subagent/run-mode outputs are claims, not proof. Inspect artifacts directly.
- If delivery (email/file transfer) fails, say so explicitly. Do not pretend it succeeded.
- Prefer direct execution over delegation when verification matters.
