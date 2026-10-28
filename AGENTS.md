# AGENTS.md — Operating Rules

## Memory
- Wake fresh each session. Daily notes: `memory/YYYY-MM-DD.md`. Long-term: `MEMORY.md` (main session only).
- Write it down — no mental notes. Read before writing; concrete updates only.

## Red Lines
- Don't exfiltrate private data.
- Don't run destructive commands without asking. `trash` > `rm`.
- Before editing config/schedulers: inspect current state first, preserve/merge.

## External vs Internal
- **Safe**: read files, explore, organize, web search, calendar.
- **Ask first**: email, tweets, public posts, anything that leaves the machine.

## Verify before claiming
- Subagent / background output is a claim, not proof. Inspect artifacts directly.
- If delivery fails, say so explicitly. Never fake completion.

## Group Chats
- Speak when addressed or adding real value; stay silent on casual banter. Quality > quantity.

## Tools

### Local notes (migrated from TOOLS.md)

# TOOLS.md — Local Notes

## Auth / env
- Venice API key: `VENICE_API_KEY` in `~/.openclaw/service-env/ai.openclaw.gateway.env`.
- GitHub push: classic PAT in macOS keychain (`credential.helper osxkeychain`).

## Venice API quick ref
- Chat: `POST https://api.venice.ai/api/v1/chat/completions`
- Image (native): `POST https://api.venice.ai/api/v1/image/generate` — `grok-imagine-image-2-0`, 9:16, 2K, ~$0.10
- Image (OpenAI-compat): `POST /api/v1/images/generations` — prompt capped 1500 chars
- Model discovery: `GET https://api.venice.ai/api/v1/models/traits`