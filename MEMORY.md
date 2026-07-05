# Paridhi's Long-Term Memory 🦚

## AIPharmaXchange Mission
Grow to 2000 pharma professionals via 3 pillars:
- **Pillar 1 — Newsletter**: 800 subscribers (+50/week, 45%+ open rate)
- **Pillar 2 — LinkedIn**: 1200 followers (+40/week, 3%+ engagement, 1 viral/month)
- **Pillar 3 — Advocacy**: 200 members via GitHub, Twitter/X, Reddit, conferences

## Venice AI Image API
- **Endpoint**: POST https://api.venice.ai/api/v1/image/generate
- **Auth**: Bearer VENICE_INFERENCE_KEY_c5diyYrdrrKLbenzadX4CP7CueQN--urN3zxUYEXNE
- **CRITICAL**: API gateway hard-caps `prompt` field at 1500 chars (model specs show 10K/32K but gateway rejects >1500)
- **Response format**: b64_json (decode base64 to get PNG bytes)
- **Params**: model, prompt, height, width, aspect_ratio, resolution, format, cfg_scale, negative_prompt, steps, style_preset, seed, variants, safe_mode, enable_web_search, return_binary, lora_strength, quality
- **Best models**: gpt-image-2 (highest quality, supports 4K + 16:9), flux-2-max (fast, good quality), nano-banana-2 (32K spec but gateway caps at 1500)

### Model Prompt Limits (Spec vs Reality)
| Model | Spec Limit | API Reality | Best For |
|-------|-----------|-------------|----------|
| gpt-image-2 | 10K | 1500 | Detailed infographics |
| nano-banana-2 | 32K | 1500 | Same as above |
| flux-2-max | 3K | 1500 | Quick visuals |
| flux-2-pro | 3K | 1500 | Budget visuals |
| ideogram-v4 | 10K | 1500 | Text-heavy designs |
| venice-sd35 | 1.5K | 1500 | Batch/budget ($0.01) |

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

## Paridhi Operating Rules
- Verify before claiming completion: check file existence, content, and side effects.
- Subagent/run-mode outputs are claims, not proof. Inspect artifacts directly.
- If delivery (email/file transfer) fails, say so explicitly. Do not pretend it succeeded.
- Prefer direct execution over delegation when verification matters.
