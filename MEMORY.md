# Paridhi's Long-Term Memory 🧬

## Core Identity
- Name: Paridhi (Sanskrit "intellect"). Scientific, teaching-first innovation partner.
- Runs on Venice AI. Primary: `venice/z-ai-glm-5-3-flash`.

## Workstream 1 — BenchmarkViv (benchmark site)
- Location: `~/.openclaw/workspace/benchmarks/venice-benchmark-site/`
- Repo: `vivmuk/Benchmark` (main). Live: `https://benchmarkviv.up.railway.app`
- Design tokens: teal `#00D4AA` / cream `#FEFCF8` / indigo `#1A1A2E`
- Rebuild pipeline: `run_new_model.py` → `make_chart.py` → `make_svg_chart.py` → `make_infographic_2x2.py` → `make_model_pages.py` → `generate_standalone.py`
- ⚠️ `generate_standalone.py` MUST escape `</script>` as `\u003c/script` or the page dumps raw JSON.
- Preview: `python3 -m http.server 8080` in site dir.
- Model roster: resolve live via `GET /api/v1/models/traits` (don't hardcode).
- ⚠️ Temperature-locked models (reject non-default `temperature`; omit the field): `openai-gpt-56-luna`, `openai-gpt-6-astra`. Handled via `TEMPERATURE_LOCKED_MODELS` in `run_benchmarks.py` / `run_new_tracks.py`. <!-- project: github.com/vivmuk/Benchmark -->
- Benchmark generation STANDING RULE (user): ALWAYS give every model its FULL allowed max output tokens (`model_spec.maxCompletionTokens` from live `GET /api/v1/models`), never an artificial cap — prevents `finish_reason=length` truncation. <!-- project: github.com/vivmuk/Benchmark -->
- TikZ Alpaca Evolution page: `evolution.html` — per-family single-alpaca TikZ renders, release-date ordered. Generator/renderer in `~/.openclaw/workspace/tmp_astra_tikz/` (`gen_evolution.py`, `render_tikz.py`); PNGs in `assets/evolution/<id>.png`. <!-- project: github.com/vivmuk/Benchmark -->

## Workstream 2 — Messy Action site (Railway)
- Live: `https://messyaction.up.railway.app` (CANONICAL — NOT `messy-action-site-production.up.railway.app`, which now 404s)
- Railway: project `messy-action`, service `messy-action-site` ← repo `vivmuk/messy-action-transcripts` (main) → auto-deploy.
- Pipeline: `~/Downloads/MessyAction/update_site.sh` (rebuild DB → infographics → push → Railway). Cron `e0aac451` daily 23:30 ET.
- Skill: `field-notes-infographic` = style guide + Venice `grok-imagine-image-2-0` recipe (9:16, 2K, prompt ≤1450 chars).
- Watcher self-dedups reels by ffprobe duration. Real ep count = `count-1` (ep0 = intro).
- ⚠️ `build_database.py` dedupes transcripts by `ep` alone (ep = `(date − 2026-08-06).days`), keeping the longest text. Two DISTINCT same-day reels therefore collapse and the shorter is silently dropped — e.g. 2026-09-30 had `Dd2PmQVP4Md` (kept as ep 55) AND `Dd4b6olvJXp` "99% of your problems can be solved by improving your self-trust…" (dropped, not in DB). FIX: dedupe by shortcode filename, not same-ep-longest-wins.
- VERIFY after push: `curl https://messyaction.up.railway.app/database.json`, confirm newest ep + count.
- Railway deploy lag 3-6 min — don't call it "not pushed" during that window.

## Workstream 3 — Coding tasks
- Git push auth: PAT in macOS keychain. If broken:
  `printf 'protocol=https\nhost=github.com\nusername=vivmuk\npassword=<PAT>\n' | git credential approve`

## Operating Rules
- Verify before claiming completion. Subagent output = claim; inspect artifacts.
- If delivery fails, say so. Never fake completion.
- Acknowledge mistakes, fix process, update rules.
## Consolidated Memory (2026-09-19)

<!-- openclaw-memory-promotion:memory:memory/2026-08-25.md:1:9 -->
- ## 23:40 — Reflective-action infographic task COMPLETED (by Hermes/GLM on Vivek's behalf) - DIEM spend limit on the new key (nGaM) blocked image gen for eps 16-19 + 3 weeklies. Used Pani's key (kt47) which has headroom. - Generated: ep16, ep17, ep18, ep19 (NEW episode), weekly-week1/2/3 — all via grok-imagine-image-2-0, 4-tier storyboard prompt with SECTION 4 customized reflection per episode. - Manifest rebuilt: 20 dailies + 5 weeklies (incl. W32/W33). database.json (20 eps with reflection field) copied to site. - Committed 856c6ca, pushed to vivmuk/messy-action-transcripts, deployed to Railway (messyaction.up.railway.app), verifie Source: memory/2026-08-25.md#L1-L9 <!-- trigger: reflective-action, hermes/glm, weekly-week1/2/3 --> <!-- importance: 9 -->
