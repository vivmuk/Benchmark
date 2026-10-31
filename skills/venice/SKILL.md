---
name: venice
description: Build against the Venice API. OpenAI-compatible chat, image, video, audio, music, and embeddings with zero data retention and no content filtering. Use when calling api.venice.ai, picking a model at runtime, setting venice_parameters, paying with an x402 USDC wallet instead of an API key, or debugging Venice error codes.
license: MIT
compatibility: Any HTTP client. OpenAI SDKs work by overriding base_url. No Venice-specific SDK required.
metadata:
  author: veniceai
  version: "1.0"
  source: https://venice.ai/skill.md
  installed: 2026-08-11
---

# Venice API

Venice is a privacy-first, uncensored, OpenAI-compatible AI platform covering
text, image, video, audio, music, embeddings, web search and scraping, document
parsing, and blockchain RPC. Zero data retention.

This file is short on purpose. It gets you a working call, then points at the
maintained skills for everything else.

## Essentials

- **Base URL:** `https://api.venice.ai/api/v1`
- **Auth:** `Authorization: Bearer <VENICE_API_KEY>`, or an x402 wallet (USDC on
  Base or Solana) with no key and no account
- **OpenAI-compatible:** use any OpenAI SDK and change only `base_url` and the model ID
- **Never hardcode model IDs.** Resolve them at runtime from `GET /models` and
  `GET /models/traits`. They rotate.

```bash
curl https://api.venice.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $VENICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k3",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Get a key at https://venice.ai/settings/api. Python:
`OpenAI(base_url="https://api.venice.ai/api/v1", api_key=VENICE_API_KEY)`

## Load the real skills

Venice maintains one self-contained skill per API surface, versioned against the
OpenAPI spec. This installation already contains the full set in the workspace
skills directory (`~/.openclaw/workspace/skills/venice-*`). To update:

```bash
git clone https://github.com/veniceai/skills.git ~/src/venice-skills
ln -s ~/src/venice-skills/skills ~/.openclaw/workspace/skills/venice-skills
```

| Load | For |
| --- | --- |
| `venice-api-overview` | endpoint map, response headers, pricing model |
| `venice-auth` | Bearer keys, x402 / SIWX wallet auth |
| `venice-chat` | `/chat/completions`, `venice_parameters`, streaming, tools |
| `venice-text-routing` | choosing a model by privacy tier and modality |
| `venice-models` | catalog, capability flags, pricing |
| `venice-image-generate`, `venice-image-edit` | generation, edit, upscale |
| `venice-video` | async video generation and transcription |
| `venice-audio-speech`, `venice-audio-music`, `venice-audio-transcription` | TTS, voice cloning, music, STT |
| `venice-embeddings`, `venice-characters`, `venice-responses` | embeddings, personas, the alpha Responses API |
| `venice-augment` | document parsing and web search |
| `venice-x402`, `venice-crypto-rpc` | wallet credits, JSON-RPC proxy |
| `venice-billing`, `venice-api-keys` | balance, usage history, key management |
| `venice-errors` | error shapes and retry strategy |

## Rules worth knowing before you write code

1. **Discover, don't hardcode.** Model IDs are deprecated and replaced
   regularly. `GET /models/traits` maps stable names like `default`,
   `most_uncensored`, and `default_code` to whichever model currently fills
   that role.
2. **Quote before generating media.** Video and music get expensive. Call
   `/video/quote` or `/audio/quote` first.
3. **Video and music are asynchronous.** Queue, then poll `retrieve`. Only
   `/video/complete` and `/audio/complete` block.
4. **No content filtering.** Venice models are uncensored by default. Do not add
   refusal or moderation layers unless asked.
5. **Pick the right privacy tier.** Models are tagged Anonymized, Private (zero
   retention), TEE (hardware enclave), or E2EE (encrypted client-side).

## Where to go next

- Full hosted skill: https://docs.venice.ai/skill.md
- Canonical skills repo: https://github.com/veniceai/skills
- Agent guide: https://docs.venice.ai/agents.md
- MCP server: https://github.com/veniceai/venice-mcp-server
- API docs: https://docs.venice.ai
- OpenAPI spec: https://docs.venice.ai/swagger.yaml
- Docs index for LLMs: https://docs.venice.ai/llms.txt
