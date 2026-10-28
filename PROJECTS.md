# PROJECTS.md — Active workstreams

**Owner:** Vivek M (`vivmuk`). Maintained by Paridhi.

Three active workstreams. Full historical catalog (agent fleet, Medhā, AIPharmaXchange, Viv Mind, etc.) was archived to `backup-tokenclean-2026-08-26-1535/` on 2026-08-26.

## 1. BenchmarkViv — Venice model benchmark site
- Path: `~/.openclaw/workspace/benchmarks/venice-benchmark-site/`
- Repo: `vivmuk/Benchmark` · Live: `https://benchmarkviv.up.railway.app`
- Pipeline: `run_new_model.py` → `make_chart.py` → `make_svg_chart.py` → `make_infographic_2x2.py` → `make_model_pages.py` → `generate_standalone.py`
- ⚠️ `generate_standalone.py` must escape `</script>` as `\u003c/script`.
- Roster resolved live via `GET /api/v1/models/traits`.

## 2. Messy Action — field-notes site (Railway)
- Live: `https://messyaction.up.railway.app` · repo `vivmuk/messy-action-transcripts`
- Pipeline: `~/Downloads/MessyAction/update_site.sh` (cron `e0aac451`, daily 23:30 ET)
- Skill: `field-notes-infographic` (Venice `grok-imagine-image-2-0`, 9:16, 2K)

## 3. Coding tasks
- Git push: PAT in macOS keychain (`credential.helper osxkeychain`).

## 4. NuOrgBot — Telegram+Slack agent on Railway (live 2026-09-15)
- Project: `nuorgbot` (id `a0d2f382-263f-4bb1-946d-073f88cf1ba5`), service `nuorgbot`, volume `/root/.hermes`, single replica `us-east4-eqdc4a` (do NOT scale — adds us-west2 poller → 409 conflicts)
- Workdir: `~/tmp/nuorgbot-deploy` (image = `hermes-agent[slack,mcp]`; entrypoint: `VENICE_API_KEY` env WINS over baked key)
- Telegram: **@NuOrgbot** (bot id 8882869857), token in `~/.config/railway/nuorgbot-bot-token.env`, allowlist 6808691714 — polling LIVE
- Slack: **LIVE (2026-09-16)** — Socket Mode, team "NuOrg", app id A0C22KVMYFQ; tokens in `~/.config/railway/nuorgbot-slack-{bot,app}.env` + Railway env (`SLACK_BOT_TOKEN` xoxb-, `SLACK_APP_TOKEN` xapp-)
- Models: planner `openai-gpt-56-sol-pro` (1M ctx, 128k out, tools+vision; user-named exception) + workers `deepseek-v4-1-flash` (1M/131k) via delegation
- Ops: verify Telegram health via `railway logs` ONLY (external getUpdates probes cause 409 conflicts); scale trap: `service scale` zeroed regions re-add us-west2

## Critical paths
| What | Path |
|---|---|

## 5. FleetDash — agent mesh dashboard (live 2026-09-25)
- URL: **fleet-dash-production.up.railway.app** (project `fleet-dash` 70663917, service `fleet-dash`, nginx:alpine with `listen ${PORT}` template)
- Style: terminal-neon (Katha palette #0a0a0a / #00f0ff / #ff9f1a / #ff4dff), boot sequence, LED status cards, system log
- Data: pull model — `~/tmp/fleet-dash/fleet-sweep.py` probes 19 agents (6 local daemons + 13 Railway + Maritime + Venice DIEM), writes `/tmp/fleet-dash/fleet-status.json`, uploads via `railway service files upload --overwrite`
- Automation: cron `4a38ecc1cd92` daily 09:00 ET → sweep + verify upload + fleet digest to origin chat (status changes, 401/402, disconnects called out)
- Maritime layer: mk_ token rotated 2026-10-04, auth OK — agents: **Kavi** (openclaw, active) + **Yantra** (hermes template, id `d6fde437-1888-4dee-86a3-a92b5ffb2f2d`, project `c2af537a-6eec-4ac2-b381-2cd7e923aaef`; see `references/operator-maritime-inventory.md`). Rebuilt 2026-10-04 on the hermes template (codex harness retired): **dual-model** — main brain `z-ai-glm-5-3-flash` (env `HERMES_INFERENCE_MODEL`, live-verified identity 2026-10-04; was xiaomi-mimo-v2-6-flash), coding subagents `mercury-2-5` via `delegation.model`, both on the Venice fleet key (pays DIEM, not Maritime credits). Durable wiring: `/usr/sbin/maritime-init` operator patch v2 regenerates `/opt/data/config-extra.yaml` (delegation + `mcp_servers.netlify` incl. PAT env block) at every boot and merges into `config.yaml` — proven across restarts. 66 skills at `/opt/data/skills/` (28 MattPocock engineering+productivity + 15 Netlify). Netlify MCP stdio (`netlify-mcp` npm -g) with `NETLIFY_PERSONAL_ACCESS_TOKEN` — live-verified: 44 sites listed. Telegram **@yantroaibot** re-wired to new project (POST /channels/telegram, webhook live). Learning layer: `/opt/data/AGENTS.md` (orchestration contract: mimo plans w/ MP skills → mercury implements → verify → direct Netlify deploy) + `/opt/data/workspace/LESSONS.md` (mistake-learning protocol)
| OpenClaw config | `~/.openclaw/openclaw.json` |
| Workspace | `~/.openclaw/workspace/` |
| Long memory | `~/.openclaw/workspace/MEMORY.md` |
| Venice key env | `~/.openclaw/service-env/ai.openclaw.gateway.env` |
| Benchmark site | `~/.openclaw/workspace/benchmarks/venice-benchmark-site/` |