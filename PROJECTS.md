# PROJECTS.md — Living fleet & work catalog

**Owner:** Vivek M (`vivmuk` / `vivgatesai`)  
**Maintained by:** Hermes + Paridhi (either agent may update)  
**Created:** 2026-07-26  
**Last updated:** 2026-08-02 (Hita Railway agent provisioned)  

This file is the durable map of projects, agents, prefs, and skills.  
**No secrets.** Tokens/keys live only in env files / auth stores.

---

## How to maintain

- After any meaningful ship, recovery, or preference change: update the relevant section + bump **Last updated**.
- Prefer facts with paths and status over narrative.
- When a skill is load-bearing for a project, list it under that project.
- Secrets: never paste keys, tokens, or bearer values here.

---

## Operator preferences (durable)

| Pref | Detail |
|---|---|
| Model ban | Never Claude/GPT via Venice key unless user names one explicitly |
| Agent naming | Sanskrit / Hindu philosophical nouns (`Jiva`, `Rati`, `Paridhi`, `Hita`, `Medhā`, …) |
| Secrets | Zero-echo in chat; stash base64 under `/tmp` if needed; Hermes redact-filter is incomplete for non-UUID secrets |
| Skill discipline | Design polish briefs → load `viv-design` first (skill is contract) |
| Model IDs | Live `GET https://api.venice.ai/api/v1/models` first; OpenClaw list lags |
| Config layers | **Paridhi** = `~/.openclaw/openclaw.json`. **Hermes** = `~/.hermes/config.yaml`. Patching one does not fix the other |
| Local models | Ollama/llama.cpp = scratchpad only; **not** Paridhi primary/fallbacks |
| Runbooks | Operator checklists (`- [ ]`), commands, time estimates — not prose tours |
| Execute-first | Routine pipeline: do it; stop only on spend risk or substantive decisions |
| Image prompt cap | Venice image gateway hard-caps prompt ~1500 chars (spec limits are misleading) |

---

## Agent fleet

### Hermes (this main agent)

| Field | Value |
|---|---|
| Role | Primary operator agent (Telegram + CLI) |
| Config | `~/.hermes/config.yaml` |
| Model (2026-07-25) | `grok-4-5` via Venice custom provider |
| Gateway | `ai.hermes.gateway` LaunchAgent |
| Skills home | `~/.hermes/skills/` |
| Memory | `~/.hermes/memories/MEMORY.md`, `USER.md` |
| Notes | Separate process from OpenClaw/Paridhi |

### Paridhi (OpenClaw local)

| Field | Value |
|---|---|
| Identity | Sanskrit “intellect”; scientific, teaching-first, model-tester (🧬) |
| Surface | Telegram bot **“Paridhi - MAC”** |
| Config | `~/.openclaw/openclaw.json` |
| Workspace | `~/.openclaw/workspace/` |
| Identity files | `IDENTITY.md`, `SOUL.md`, `MEMORY.md`, `AGENTS.md` |
| Primary (2026-07-25) | `venice/grok-4-5` |
| Fallbacks | `venice/gemini-3-6-flash` → `venice/kimi-k3` (cloud-only; terra-pro removed) |
| Gateway | `ai.openclaw.gateway` on `:18789` |
| Local LLM dir | `/Users/vivgatesai/paridhi/` (GGUF + audit reports) |
| Local stack (optional) | LFM2.5-8B-A1B GGUF + Ollama `qwen3:8b` / `qwen3:4b` — **not** user-facing primary |
| Created | Identity formalized 2026-07-04; local audit 2026-06-03 |

**Paridhi workstreams owned / heavily driven**

1. **BenchmarkViv** — original real runs (2026-07-05), site under workspace, GitHub `vivmuk/Benchmark`
2. **Model benchmarking** — Kimi K2.7-Code vs MiMo-V2.5 (2026-07-04); local LFM/Qwen phase-2 (2026-06-03)
3. **AIPharmaXchange memory** — Paperclip org map, brand, Venice image API notes in Paridhi `MEMORY.md`
4. **Viv Mind** — PDF harvest + watercolor feed (`vivmuk/viv-mind`, 2026-06-19)
5. **Personality / SOUL** — teaching-first innovation partner charter

**Paridhi recovery (2026-07-25)**

- Symptom: Telegram “⚠️ Something went wrong”
- Root cause: Venice **401** stale auth + unregistered fallback (`grok-41-fast`) + dual-layer confusion with Hermes
- Fix: paste working Venice key into OpenClaw auth + service-env; primary `grok-4-5`; fallbacks Google latest + kimi-k3; `gateway install --force` + kickstart
- User confirmed: **“its working!!”**

**Paridhi local LLM research (2026-06-03)** — historical, not current primary path

| Role (then) | Model | Notes |
|---|---|---|
| Router | LFM2.5-8B-A1B (~72 tok/s) | Fast; weak native tools |
| Primary agent | Qwen3-8B | Best tool calling on Ollama |
| Fallback | Qwen3-4B | Faster backup |
| Reports | `~/paridhi/reports/phase1-audit.md`, `phase2-benchmarks.md` | |
| Hardware | Mac mini M4, 16 GB | |

**Skills most used for Paridhi:** `openclaw`, `openclaw-model-management`, `jiva-telegram-deploy` (dual-layer trap), `systematic-debugging`, `venice-benchmark-runner`, `llama-cpp`

### Jiva (Railway)

| Field | Value |
|---|---|
| Role | Hermes-style Telegram agent on Railway |
| Deploy tree | `~/tmp/jiva-deploy` |
| Railway project | `jiva` |
| Recurring issues | Dead baked Venice key vs live env key; DoH/Telegram IP wedge; polling conflicts |
| Skill | `jiva-telegram-deploy`, `hermes-telegram-platform`, `cloud-agent-provisioning` |

### Rati (Railway)

| Field | Value |
|---|---|
| Role | Sibling agent in fleet |
| Deploy tree | `~/tmp/rati-deploy` |
| Railway project | `rati` |
| Notes | Same class as Jiva; keep naming/aesthetic distinct |

### Hita (Railway)

| Field | Value |
|---|---|
| Identity | Sanskrit “welfare / benefit”; Rati-class sibling, usefulness-first |
| Role | Hermes-style Telegram agent on Railway |
| Deploy tree | `~/tmp/hita-deploy` |
| Railway project | `hita` (id `05d53aa1-…2599`) |
| Service | `hita` · volume `hita-volume` → `/root/.hermes` |
| URL | `https://hita-production.up.railway.app` |
| Primary model | `deepseek-v4-flash-0731` (Venice; matches Paridhi primary) |
| Config | `~/tmp/hita-deploy/hermes/cli-config.yaml` + `SOUL.md` |
| Status (2026-08-02) | Online; gateway up; **Telegram bot token not set yet** |
| Skills | `jiva-telegram-deploy`, `self-hosted-agent-deployment`, `cloud-agent-provisioning` |

---

## Major product projects

### 1. Medhā / VivMCP (Venice MCP on Railway)

| Field | Value |
|---|---|
| Purpose | Operator-tuned Venice MCP bridge (31 tools) for any agent client |
| Repo | `vivmuk/medha-mcp` (fork of `veniceai/venice-mcp-server`) |
| Workdir | `~/tmp/medha-deploy` |
| Railway | project `medha` + Postgres service for call/artifact logs |
| Live MCP | `https://medha.up.railway.app/mcp` (or `medha-production…` variant) |
| Admin | `https://medha.up.railway.app/admin` (phase 7–8 dynamic presets SPA) |
| Design | viv-design doctrine (light OKLCH, no em-dashes, chakra-jewel) |
| Open | Public alias `vivmcp` desired; Railway has no service rename — domain/alias path |
| User rule | No Claude/GPT in presets unless named |
| Skills | `venice-mcp-on-railway`, `mcp-server-customize-deploy`, `native-mcp`, `venice-api`, `viv-design`, `cloud-agent-provisioning`, `branded-infographic`, `send-gmail-attachment` |

### 2. BenchmarkViv / Venice benchmark site

| Field | Value |
|---|---|
| Purpose | Cost-to-value model leaderboard on real Venice API |
| Local path | `~/.openclaw/workspace/benchmarks/venice-benchmark-site/` |
| Public repo | `vivmuk/Benchmark` |
| Live URL | `https://benchmarkviv.up.railway.app` |
| Local data (2026-07-24) | **96 rows**, **16 models**, incl. **inkling**; `generated_at` ~2026-07-24T23:36Z |
| Live data issue | Was stale (~4-track / older roster) vs local 6-track rebuild — **push/redeploy still open** |
| Harness | 32k max tokens / 600s timeout; insert-not-overwrite; `data/changelog.json` |
| Paridhi origin | First real multi-model runs 2026-07-05 (Paridhi memory) |
| Hermes extensions | kimi-k3 clear, opus-5, inkling add, About changelog, spend ledger |
| Skills | `venice-benchmark-runner`, `github-repo-management`, `systematic-debugging` |
| Related dirs | `benchmarks/model-benchmark/`, `benchmarks/glm-physics-benchmark/` |

**Current local model roster (16):**  
`claude-fable-5`, `claude-opus-4-8`, `claude-opus-5`, `deepseek-v4-pro`, `grok-4-5`, `inkling`, `kimi-k3`, `minimax-m3-preview`, `openai-gpt-55`, `openai-gpt-56-luna`, `openai-gpt-56-luna-pro`, `openai-gpt-56-sol`, `openai-gpt-56-sol-pro`, `openai-gpt-56-terra`, `openai-gpt-56-terra-pro`, `zai-org-glm-5-2`

### 3. AIPharmaXchange (content + multi-agent)

| Field | Value |
|---|---|
| Mission | Grow pharma professional audience (newsletter / LinkedIn / advocacy) |
| Orchestration | Paperclip at `http://127.0.0.1:3100` (local) |
| Workspace | `~/.paperclip/workspaces/aipharmaxchange/` |
| Brand | Teal `#00D4AA`, cream `#FEFCF8`, indigo-black `#1A1A2E`; Fraunces + Inter |
| Open Design | daemon `:7456`, DESIGN.md under `/tmp/open-design/...` (paths may move) |
| Outputs | Editorial carousels, LinkedIn copy, newsletter, email delivery |
| Skills | `paperclip`, `paperclip-delivery-daemon`, `paperclip-status-transition`, `editorial-carousel-orchestration`, `editorial-rigor`, `social-carousel-generation`, `branded-infographic`, `model-routing`, `content-marketing-pipeline`, `send-gmail-attachment`, `open-design` |

### 4. Viv Mind

| Field | Value |
|---|---|
| Purpose | Research journal / PDF harvest + visual feed |
| Path | `~/.openclaw/workspace/viv-mind-scaffold/` (+ skill under workspace skills) |
| Live | `https://vivmuk.github.io/viv-mind` |
| Repo | `vivmuk/viv-mind` |
| Paridhi note | 2026-06-19: trigger phrase “Is this for Viv Mind?”; first McKinsey PDF entry |
| Skills | workspace `viv-mind` skill, `venice-media`, `ocr-and-documents` |

### 5. Nightly agent backups

| Field | Value |
|---|---|
| Purpose | Cross-agent state + artifact backup (Hermes + OpenClaw + Paperclip) |
| Skills | `ai-agents-nightly-backup`, `cross-agent-backup-system`, `multi-agent-nightly-backup` |
| Pattern | Hermes cron `no_agent:true`, OneDrive + local mirror fallback |

### 6. GitHub deploy-key / Gujarati-kids

| Field | Value |
|---|---|
| Issue | `Permission denied (publickey)` local + Jiva same key |
| Fix locus | `github.com/vivmuk/gujarati-kids` → Settings → Deploy keys (not Jiva-side) |
| Skill | `jiva-telegram-deploy`, `github-auth` |

---

## Railway project inventory (workspace `vivmuk's Projects`)

Active / relevant subset (full list is long; many experimental):

| Railway name | Likely role |
|---|---|
| `jiva` | Jiva Telegram agent |
| `rati` | Rati agent |
| `medha` | Medhā/VivMCP |
| `benchmark` | BenchmarkViv hosting |
| `AiPharmaXchange.com` | Brand/site |
| `Viv-Mind` | Viv Mind |
| `Fable5` | Fable5 experiments |
| `Harness-Engin` / `Harness Studio` | Harness engineering |
| `Venice Video` / `Reference to Video` | Video pipelines |
| `Gujarati` | Gujarati-kids related |
| `creative-manifestation`, `Katha`, `Multigen`, … | Other creative/apps |

Local deploy trees: `~/tmp/jiva-deploy`, `~/tmp/rati-deploy`, `~/tmp/medha-deploy`, `~/tmp/medha-share`, `~/tmp/benchmark-clone`, `~/tmp/harness-engineering`

---

## Skills map (load-bearing for this fleet)

### Agent / platform

- `hermes-agent`
- `openclaw`
- `openclaw-model-management`
- `jiva-telegram-deploy`
- `hermes-telegram-platform`
- `hermes-subagent-profile`
- `self-hosted-agent-deployment`
- `cloud-agent-provisioning`
- `managed-agent-deployment`

### MCP / Venice

- `venice-mcp-on-railway`
- `mcp-server-customize-deploy`
- `native-mcp`
- `venice-api`
- `venice-media`
- `venice-benchmark-runner`
- `model-routing`

### Design / content

- `viv-design`
- `viv-app-build`
- `branded-infographic`
- `baoyu-infographic`
- `open-design`
- `social-carousel-generation`
- `editorial-rigor`
- `editorial-carousel-orchestration`
- `content-marketing-pipeline`
- `paper-reel-pipeline`
- `ai-video-production`

### Orchestration / delivery

- `paperclip`
- `paperclip-delivery-daemon`
- `paperclip-status-transition`
- `send-gmail-attachment`
- `google-workspace`

### Engineering hygiene

- `systematic-debugging`
- `github-repo-management`
- `github-auth`
- `github-pr-workflow`
- `hermes-agent-skill-authoring`
- `writing-plans` / `plan`
- `llama-cpp` (local GGUF only)

### Backup

- `ai-agents-nightly-backup`
- `cross-agent-backup-system`
- `multi-agent-nightly-backup`

Full catalog lives under `~/.hermes/skills/` (~130+ skills). This map is the **used** set for fleet work, not the full list.

---

## Critical paths (cheat sheet)

| What | Path |
|---|---|
| Hermes config | `~/.hermes/config.yaml` |
| Hermes memory | `~/.hermes/memories/` |
| OpenClaw config | `~/.openclaw/openclaw.json` |
| OpenClaw workspace | `~/.openclaw/workspace/` |
| Paridhi identity | `~/.openclaw/workspace/IDENTITY.md` |
| Paridhi long memory | `~/.openclaw/workspace/MEMORY.md` |
| This catalog | `~/.openclaw/workspace/PROJECTS.md` |
| Paridhi local models | `~/paridhi/models/`, `~/paridhi/reports/` |
| Benchmark site | `~/.openclaw/workspace/benchmarks/venice-benchmark-site/` |
| Medhā deploy | `~/tmp/medha-deploy` |
| Jiva deploy | `~/tmp/jiva-deploy` |
| Venice key env (names only) | `~/.config/railway/venice-rati-key.env` |
| OpenClaw service env | `~/.openclaw/service-env/ai.openclaw.gateway.env` |
| Paperclip workspace | `~/.paperclip/workspaces/aipharmaxchange/` |
| Spend ledger pattern | `/tmp/aipharmaxchange_spend/spend_YYYY-MM-DD.json` |

---

## Open / unfinished (as of 2026-07-26)

- [x] Paridhi new tracks: `value_density` 16/16 + `reverse_prompt_vision` DIEM retry (14 ok, 2 non-vision skipped) — local results + standalone rebuilt 2026-07-26
- [ ] **Push** local BenchmarkViv to git/Railway so live site matches disk (128 rows, 8 tracks)
- [ ] Medhā public alias / cleaner `vivmcp` URL (no Railway service rename)
- [ ] Medhā cascade round-trip: admin dropdown → next MCP `tools/list`
- [ ] Keep Paridhi SOUL.md model-routing section in sync with live primary (still mentions older kimi-k2-7-code in places)
- [ ] Optional: retire stale OpenClaw session overrides / old explicit paridhi_* sessions
- [ ] Confirm Jiva Railway health after last key/env swap
- [ ] Nightly backup install status verification (if not already cron-live)

---

## Update log

| Date | Change |
|---|---|
| 2026-07-26 | Vision gallery page (`vision.html`): source image, full nano-banana-2 prompt, reverse instruction, 28-attr checklist, 14 reconstructions; nav + changelog; commit `671503e` |
| 2026-07-26 | Paridhi task finished: cleared Venice billing disable lock; retried reverse_prompt_vision DIEM failures (opus-5/minimax/grok-4-5/inkling/kimi-k3); local site 128 rows / 8 tracks; standalone rebuilt. Push still open. |
| 2026-07-26 | Initial living catalog created from Hermes memory, Paridhi workspace/memory/reports, Railway list, skills catalog, and recent recovery work |
| 2026-07-25 | Paridhi restored (Venice auth + grok-4-5 + gemini-3-6-flash fallback); Hermes on grok-4-5 |
| 2026-07-24 | Benchmark local: inkling + 96 rows + changelog; Medhā phase 8 admin design |
| 2026-07-20 | Medhā MCP fork/deploy phases; no-Claude/GPT preset scrub |
| 2026-07-05 | Paridhi BenchmarkViv real runs shipped to `vivmuk/Benchmark` |
| 2026-07-04 | Paridhi identity created; Kimi vs MiMo benchmark |
| 2026-06-19 | Viv Mind PDF + feed |
| 2026-06-03 | Paridhi phase1 audit + phase2 local LLM benchmarks |

---

## Related files agents should open first

1. This file — `PROJECTS.md`
2. Hermes prefs — `~/.hermes/memories/USER.md` + `MEMORY.md`
3. Paridhi prefs — `~/.openclaw/workspace/MEMORY.md` + `IDENTITY.md`
4. Relevant skill `SKILL.md` (never freestyle a class-level workflow)
