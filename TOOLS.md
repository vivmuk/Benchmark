# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

## Venice Official Skills (installed 2026-08-11)
- Umbrella skill: `skills/venice/SKILL.md` (from https://venice.ai/skill.md)
- 20 canonical per-surface skills cloned from https://github.com/veniceai/skills → `skills/venice-*` (chat, models, text-routing, image-generate/edit, video, audio-*, embeddings, augment, billing, errors, x402, crypto-rpc, characters, api-keys, responses, auth, api-overview)
- Fresh catalog snapshot: `skills/venice-models/snapshots/` (109 text, 37 image, 320 total IDs across 10 types, `model_ids.txt`)
- Core rule: **discover, don't hardcode** — resolve models via `GET /models/traits` (default, most_uncensored, default_code, default_reasoning, default_vision, function_calling_default)
- Env: `VENICE_API_KEY` (in ~/.openclaw/service-env/ai.openclaw.gateway.env) — verified working against /models/traits + chat
- Re-snapshot anytime: clone repo's scripts/snapshot_models.py with VENICE_API_KEY set
