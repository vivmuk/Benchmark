# BenchmarkViv — Revamp Execution Plan (v1 — pending approval)

> Status: **APPROVED & EXECUTING** — owner decisions 2026-08-19.
>
> - **A:** Yes — fix the One-Shot UI / HTML benchmark scorer (the "HTML alpaca").
> - **B:** Onboard **ONLY the 3 models added in the last 2 weeks** from the live catalogue (created >= 2026-08-05):
>   - `z-ai-glm-5-3` (GLM 5.3, added 08-18)
>   - `qwen-3-8-27b` (Qwen 3.8 27B, added 08-17)
>   - `deepseek-v4-pro-0813` (DeepSeek V4 Pro 0813, added 08-14)
>   Drop the broader shortlist — do NOT go back and re-run the rest of the catalog.
> - **C:** Light theme (teal + orange + dark blue), Material design, orange more prominent.
> - **D:** Yes — LLM-judge rubric + deterministic fallback.
> - Deploy: commit + push to GitHub → Railway auto-deploys.

---

## 6b. Confirmed scope changes (2026-08-19)

---

## 1. Goals (in priority order)

1. **Add the new Venice models** to the benchmark, re-scored with a corrected rubric.
2. **Model selector** — dropdown/popover with checkboxes; default = top 15 by VivIndex; user can check/uncheck more.
3. **Provider-based colors** — one base color per provider (Claude, GPT, DeepSeek, Grok, Gemini, Qwen, Kimi/Moonshot, MiniMax, GLM/Z-AI, NVIDIA, Aion, Mistral, …). No more per-model arbitrary colors.
4. **Full Material Design 3 (Material You) UI/UX rebuild** of every page — fix the buggy components (nav drawer, sparklines, lightbox, chart resize, GPU bg).
5. **Per-model GIFs** embedded on each model profile page (from existing `data/gif_arena/*.gif` + judge scores).
6. **New evaluation rubric** (replaces the flawed heuristic scorers in `run_benchmarks.py`), including the broken HTML/One-Shot-UI evaluation; re-run and re-publish.

---

## 2. Key decisions to confirm BEFORE I start coding

| # | Question | Default I'd take if you don't say otherwise |
|---|----------|---------------------------------------------|
| A | **"HTML alpaca"** = the **One-Shot UI (HTML) scorer** — the gif-arena has "Alpaca-ness" axis, but the *evaluation bug* you mention lives in `score_one_shot_ui`. | Treat it as the **One-Shot UI / HTML benchmark scorer**; fix it with a new rubric. (Flag if you meant a different trail.) |
| B | Which new models to onboard? `known_models.json` shows **75 not-yet-scored**. Many are tiny / e2 / uncensored / duplicates — running all 75 × 7 tracks is heavy + costly. | Curate a **shortlist of real, popular chat/coding models** (below). You can expand later. |
| C | Color scheme baseline for the re-design: keep current **dark** theme vs. light? | Keep a **dark default** (matches existing), Material-3 surfaces, brand teal accent. |
| D | "New rubric" approach: deterministic **LLM-judge** or corrected heuristics? | **LLM-judge with a fixed rubric + a save-on fallback heuristic**, so scores stay reproducible like now. |
| E | Should selection defaults be **top-15 by VivIndex at load**, and does that include only full-coverage models first? | Top 15 by VivIndex of the **full-coverage** set, then allow adding partials later. |

---

## 3. Workstreams

### WS-1 — Onboard the new models (fresh Venice API)
1. Read live catalog: `GET https://api.venice.ai/api/v1/models` (or trust `data/known_models.json`, refreshed) and diff against `model_registry.py`.
2. **Curated shortlist** of new chat-capable models to add (subject to B):
   - claude-opus-4-7 / claude-opus-4-6 / claude-opus-4-5 / claude-sonnet-4-6 / claude-sonnet-4-5
   - gemini-3-5-flash-lite / gemini-3-1-pro-preview / gemini-3-flash-preview
   - grok-4-3 / grok-4-20-multi-agent
   - kimi-k2-7-code / kimi-k2-6 / kimi-k2-5
   - deepseek-v3.2 / deepseek-v4-pro-0813
   - openai-gpt-oss-120b / openai-gpt-oss-20b (via e2 if needed)
   - qwen3-coder-480b-a35b-instruct-turbo / qwen3-235b-instruct-2507 / qwen-3-6-plus
   - mistral-small-2603 / mistral-small-3-2-24b
   - nvidia-nemotron-3-ultra-550b-a55b / nemotron-3-nano-30b
   - minimax-m25 / xiaomi-mimo-v2-5 (if chat-capable)
3. Add each to `model_registry.py` (id + display), add pricing to `FALLBACK_PRICING` fallback.
4. Run the **new rubric** benchmark on them via `run_benchmarks.py --run-real` (uses scoring from WS-5).
5. Merge into `data/results.json` + `data/summary.json`, regenerate boards.

### WS-2 — Provider color mapping (single source of truth)
- New module `provider_colors.py` (or a `PROVIDERS` dict in `model_registry.py`): map **model id prefix → provider → base color**.
- Proposed base colors:
  - OpenAI GPT = **#17A2F0 (blue)** — wait, DeepSeek gets blue per user. Re-assign: Claude = **orange (#F97316)**, GPT = **violet/indigo**, DeepSeek = **blue (#0891B2)**, Gemini = **cyan/teal**, Grok = **red/black-ish**, Qwen = **purple**, Kimi/Moonshot = **amber**, MiniMax = **pink**, GLM/ZAI = **green**, NVIDIA = **#76B900** green, Aion = magenta, Mistral = **#F90B3D**.
- Within a provider, models get same hue, varied by **lightness/alpha** (so "the same color as the provider" is obvious).
- Consume in **all** visuals: `assets/app.js` chart colors, `make_chart.py`/`make_svg_chart.py`/`make_infographic_2x2.py`/`make_model_pages.py`, compare/trends, infographics.

### WS-3 — Model selector (dropdown + checkboxes)
- Add to each data page a **"Models" toolbar control** (chip/select) opening a material popover list of all models:
  - Provider-colored checkbox per model + filter-by-provider.
  - **Defaults: top 15 by VivIndex checked** (on first load if no saved preference).
  - "Select top 15", "All", "Clear" quick actions; count badge.
- Persist selection in `localStorage` (per page).
- A central `state.selected` set filters **every chart + comparison + stats**; charts re-render on change (already have re-render pipeline).
- Includes partial-coverage models (marked) and honors the *info renormalization* note already in the app.

### WS-4 — Material Design 3 overhaul + bug fixes
- Adopt an **MD3-compliant design-token system** (`:root` variables: color roles, elevation grades 0-5, shape, motion), still brand-flagged.
- Ripple on interactive elements, chips, FABs, snackbars, icon buttons, segmented control, dialog/sheet for model picker, animated reveal, prefers-reduced-motion respected.
- **Light first-pass visual refresh** across: `index.html`, `compare.html`, `trends.html`, `vision.html`, `about.html`, `experimental-design.html`, `gif-arena.html`, all `models/*.html`.
- **Fix known buggies:**
  - Sparkline canvases sized wrong (fixed preset dims) → proper responsive sizing + ResizeObserver.
  - Mobile nav drawer + scrim (dedupe click/pointerup double-fire).
  - `.img-zoom` →
  - Material ripple scoping.
  - Chart re-render on breakpoint change (avoid double init leaking charts).
  - Self-contained pages: keep `generate_standalone.py` as source of truth; update for any new markup/colors so the "standalone" trap isn't reintroduced.

### WS-5 — GIFs on model profile pages
- Add **[GIF + score]** block to each `models/<slug>.html`, reading existing `data/gif_arena/<slug>.gif` + `<slug>.meta.json`:
  - animated preview, per-axis badges (alpaca/dance/polish/creative/code) + overall judge score.
  - Models without a GIF: show "no GIF track" placeholder or render new.
- Rebuild `gif-arena.html` + each profile page. Possibly regenerate via `make_model_pages.py` (add GIF lookup).

### WS-6 — New evaluation rubric + fix "HTML / One-Shot-UI" evaluation
- Current heuristic scorers are brittle and skew results (e.g. HTML scorer rewards the word "button"/"card"/"focus" in code; counts `?` in comments; `. = "score"` string matching; zero-fix not really measured).
- **New rubric design (implemented as an LLM-judge over a fixed checklist, with a contained deterministic fallback):**
  - Publish a shared JSON rubric spec (`rubrics/*.json`) with per-benchmark, per-dimension scoring + evidence-based verdicts.
  - **One-Shot UI (HTML/Alpaca)** new dimension set: 1) Runs/browses (valid single HTML); 2) matches spec (dark dashboard, focus score, sparkline, Start-Focus button); 3) semantic + accessible; 4) visual polish; 5) responsiveness. No more string soups.
  - Similarly refresh Intent, Startup, Pharma, Value-Density rubrics so all are consistent + auditable.
- **Re-run the full sweep** on new rubrics so all 37+ models are re-scored fairly (idempotent, no repr character cheating).
- Update `METHODOLOGY.md` + `experimental-design.html` to the new rubric.

### WS-7 — Regenerate / build / deploy
- Run the full regeneration pipeline: `run_benchmarks` → `make_chart` → `make_svg_chart` → `make_infographic_2x2` → `make_model_pages` (+ GIF block) → `make_compare` → `make_trends` → `generate_standalone`, with new UX/colors/selector.
- Manual QA pass in browser (`python -m http.server`) on desktop + mobile.
- Commit + push to `github.com/vivmuk/Benchmark.git`; Railway auto-deploys `benchmarkviv.up.railway.app`. Verify the live `data/results.json` shows the new boards.

---

## 4. Files touched (map)

| Component | Files |
|---|---|
| Registry / colors / pricing | `model_registry.py`, new `provider_colors.py` |
| Scorers | `run_benchmarks.py`, new `rubric/*.json` |
| New models bench | `run_missing.py`/`run_new_model.py`, `batch_run.sh` |
| Charts+infographics / SVG | `make_chart.py`, `make_svg_chart.py`, `make_infographic_2x2.py` |
| Profile pages + GIFs | `make_model_pages.py` (+ gif render), existing `data/gif_arena/*` |
| Site shell + UI | `assets/styles.css`, `assets/app.js`, all `*.html` |
| Standalone site | `generate_standalone.py` (keep in-step) |
| Data | `data/results.json`, `data/summary.json`, `data/chart_snapshot.json`, `data/trends.json`, `data/leaderboard_chart.svg` |

---

## 5. Risks / open questions
1. **Cost of re-running rubric** on ~40-50 models × 7 tracks is real (billed inference anyway). I'll gate with `--dry-run` then batch.
2. **Which new models** actually get added (shortlist above depends on your sign-off).
3. **Deploy target** — confirm it's the Railway site as primary (memory says yes). `curl benchmrkviv.up.railway.app` smoke check before/after.
4. Full Material-DS rebuild could push the standalone files large; will keep everything in the one repo + no build tools.

---

## 6. Definition of done
- Local build serves with the new selector, colors, MD3 look, per-model GIFs, and all pages resolve.
- Top-15 default trends still agree with data.
- New rubric is documented + re-run on all models.
- Live site updated & fetched: `data/results.json` shows new model count + new colors, pages look smooth on desktop + mobile.