# BenchmarkViv — Methodology

## Overview

BenchmarkViv is a multi-track evaluation suite that measures frontier LLM
capability across four distinct dimensions: intent understanding, one-shot UI
generation, long-horizon agentic planning, and single-file HTML/CSS/JS
production. Every model receives the identical prompt per track, with the same
sampling parameters, and outputs are scored on a 0–100 scale per track. A
composite **VivIndex** rolls the four track scores into a single headline
number, weighted by the relative difficulty and practical value of each track.

All inference is served through the Venice AI API. No model receives special
prompt engineering, system preambles, or few-shot examples. The goal is a
reproducible, apples-to-apples comparison under controlled conditions.

---

## Models and Pricing

Fifteen models are evaluated. Pricing is listed in USD per 1 million tokens
(input / output). Rates reflect Venice API pricing at time of evaluation.

| # | Model | Venice API ID | Input ($/1M) | Output ($/1M) |
|---|---|---|---|---|
| 1 | GPT-5.6 Sol | openai-gpt-56-sol | $6.25 | $37.50 |
| 2 | GPT-5.5 | openai-gpt-55 | $6.25 | $37.50 |
| 3 | Opus 5 | claude-opus-5 | $6.00 | $30.00 |
| 4 | Sonnet 5 | claude-sonnet-5 | $3.00 | $15.00 |
| 5 | GLM 5.2 | zai-org-glm-5-2 | $1.40 | $4.40 |
| 6 | DeepSeek V4 | deepseek-v4-pro | $1.65 | $3.30 |
| 7 | DeepSeek V4 Flash | deepseek-v4-flash-0731 | $0.175 | $0.35 |
| 8 | Gemini 3.6 Flash | gemini-3-6-flash | $1.875 | $9.375 |
| 9 | Grok 4.6 | grok-4-6 | $2.27 | $6.80 |
| 10 | Qwen 3.8 Max | qwen-3-8-max | $2.50 | $7.50 |
| 11 | Qwen 3.8 2.4T | qwen-3-8-2-4t-a95b | $2.50 | $7.50 |
| 12 | Kimi K3 | kimi-k3 | $3.75 | $18.75 |
| 13 | GPT-5.6 Luna | openai-gpt-56-luna | $0.267 | $1.60 |
| 14 | Nemotron 3.5 | nvidia-nemotron-3-5-lightning-30b-a3b | $0.10 | $0.25 |
| 15 | MiniMax M3 | minimax-m3-preview | $0.30 | $1.20 |

Pricing is fetched live from the Venice `/models` endpoint when a real API key
is available. If the endpoint is unreachable or omits pricing for a model,
hardcoded fallback rates from the table above are used. The cost calculator in
`run_benchmarks.py` uses whichever source is active.

---

## Benchmark Tracks

### Track 1 — Intent Understanding

**Goal:** Measure whether a model asks clarifying questions before assuming
details, produces a structured proposal, and avoids hallucinating requirements
that were not stated.

**Prompt:** A deliberately vague build request with missing context. The model
must resist the temptation to jump straight to a solution.

**Scoring (0–100):**

| Criterion | Points | Description |
|---|---|---|
| Clarifying questions | 0–40 | Quality and quantity of questions asked before proposing a solution. Each meaningful question contributes up to 10 points, capped at 40. |
| Structured proposal | 0–30 | Presence of headings, bullet points, numbered lists, or other structural markers in the proposal section. Each structural marker contributes up to 6 points, capped at 30. |
| Avoids hallucination | 0–30 | Use of hedging language, explicit acknowledgment of uncertainty, and asking before assuming. Each hedge/qualifier contributes up to 6 points, capped at 30. |

**Scoring mode:** Heuristic auto-score in `run_benchmarks.py` for rapid
iteration; manual or LLM-judge review for final published scores.

---

### Track 2 — One-Shot UI Generation

**Goal:** Measure whether a model can produce a polished, production-quality
HTML component in a single shot — no iteration, no follow-up, no fixes.

**Prompt:** A request for a self-contained dark-mode dashboard card with
specific UI elements (focus score, sparkline, action button).

**Scoring (0–100):**

| Criterion | Description |
|---|---|
| Polish | Visual refinement: spacing, typography, color harmony, shadow/depth, hover states. |
| Semantic HTML | Use of proper semantic elements (`<section>`, `<header>`, `<button>`, ARIA roles) rather than generic `<div>` soup. |
| Accessibility | Focus rings, ARIA labels, color contrast meeting WCAG AA, keyboard operability. |
| Responsive | Layout adapts to mobile and desktop viewports via media queries or flexible units. |
| Zero-fix | Output runs as-is in a browser with no missing closing tags, no broken JS, no external dependencies. |

**Scoring mode:** Heuristic placeholder maps detected features onto a 70–95
range for dry runs; final scoring is manual or LLM-judge based on the five
criteria above.

---

### Track 3 — Long-Horizon Agentic Task

**Goal:** Measure whether a model can decompose a complex, multi-step system
into a coherent plan with tool selection, failure-mode awareness, and correct
task ordering.

**Prompt:** A request to plan an AI research assistant pipeline with four
explicit sub-tasks (monitor, summarize, store, answer).

**Scoring (0–100):**

| Criterion | Points | Description |
|---|---|---|
| Step coverage | 0–40 | Number of distinct, correctly ordered steps. ≥ 4 steps earns full 40; fewer steps earn 8 points each. Steps must be numbered or explicitly labeled. |
| Tools | 0–30 | Mentions concrete tools or technologies (API, vector DB, embedding model, scheduler, framework). Each unique tool mention contributes up to 6 points, capped at 30. |
| Failure modes | 0–30 | Identifies potential failure modes (rate limits, hallucinated citations, stale index, API downtime, edge cases). Each unique failure-mode mention contributes up to 8 points, capped at 30. |
| Ordering | Implicit | Steps must appear in a logical execution order. Gross misordering (e.g., answering before storing) penalizes the step-coverage subscore. |

**Scoring mode:** Heuristic auto-score in `run_benchmarks.py`.

---

### Track 4 — Alpaca HTML Test

**Goal:** Measure single-file HTML/CSS/JS production quality across structure,
styling, responsiveness, interactivity, validation, animations, and content
fidelity.

**Prompt:** See `alpaca_html_test.md` for the verbatim prompt and full scoring
breakdown.

**Scoring (0–100):**

| Criterion | Description |
|---|---|
| Structure | Valid HTML5 doctype, semantic elements, logical DOM hierarchy, no unclosed tags. |
| CSS | Internal or inline stylesheet quality: selectors, specificity, layout method (flex/grid), design tokens. |
| Responsive | Media queries or fluid units; layout adapts to mobile and desktop. |
| JS | JavaScript functionality: event handlers, DOM manipulation, state management, no runtime errors. |
| Validation | HTML passes W3C validator; no stray closing tags, no invalid attributes. |
| Animations | CSS transitions/animations or JS-driven motion; respect for `prefers-reduced-motion`. |
| Content | Text content is meaningful, complete, and matches the prompt's requirements. |

**Scoring mode:** Heuristic auto-score supplemented by manual/LLM-judge review.
See `alpaca_html_test.md` for per-criterion point allocation.

---

## VivIndex — Composite Score

The VivIndex is a weighted average of the four track scores. Weights reflect
the relative difficulty and practical significance of each capability:

| Track | Weight |
|---|---|
| Long-Horizon Agentic | 30% |
| Intent Understanding | 25% |
| One-Shot UI Generation | 25% |
| Alpaca HTML Test | 20% |
| **Total** | **100%** |

**Formula:**

```
VivIndex = (Agentic × 0.30) + (Intent × 0.25) + (UI × 0.25) + (Alpaca × 0.20)
```

Each track score is normalized to 0–100 before weighting. The VivIndex is
reported as a single number in the same 0–100 range. If a model does not
produce a valid response for a track (error, empty output, or refusal), that
track scores 0 and the VivIndex is computed with the 0 included — no
renormalization.

---

## Cost Analysis

### Per-call cost

For each model/benchmark call, cost is calculated from actual token usage
reported by the Venice API:

```
cost = (prompt_tokens / 1,000,000) × input_rate
     + (completion_tokens / 1,000,000) × output_rate
```

Where `input_rate` and `output_rate` are the per-1M-token prices from the
pricing table above (or live-fetched values).

### Pre-run estimate

Before a real run, `estimate_total_cost()` computes a worst-case ceiling:

```
estimated_max_cost = Σ  (150 / 1,000,000) × input_rate
                   + Σ  (max_tokens / 1,000,000) × output_rate
```

Summed over all model × benchmark pairs. This assumes every model outputs the
full `max_tokens` on every call — an upper bound, not a prediction.

### Per-model cost envelope (full run, all 4 tracks, max_tokens=2048)

| Model | Worst-case cost (4 tracks × 2048 output) |
|---|---|
| GPT-5.6 Sol | ~$0.31 |
| GPT-5.5 | ~$0.31 |
| Opus 5 | ~$0.25 |
| Sonnet 5 | ~$0.12 |
| GLM 5.2 | ~$0.04 |
| DeepSeek V4 | ~$0.03 |
| Gemini 3.6 Flash | ~$0.08 |
| Grok 4.6 | ~$0.06 |
| Qwen 3.8 Max | ~$0.06 |
| Kimi K3 | ~$0.15 |
| MiniMax M3 | ~$0.01 |
| **Total (11 models)** | **~$1.42** |

Actual costs will be lower because most models do not fill the full token
budget on every call.

---

## Execution Parameters

All models are called with identical sampling parameters to ensure fair
comparison:

| Parameter | Value |
|---|---|
| Temperature | 0.5 |
| Max tokens (completion) | 2048 |
| Rate-limit sleep between calls | 1.0 s |
| Request timeout | 180 s |
| API endpoint | `https://api.venice.ai/api/v1/chat/completions` |
| Auth | `Bearer $VENICE_INFERENCE_KEY` |

No system prompt is sent. Each call is a single user-turn message containing the
verbatim benchmark prompt. No conversation history, no few-shot examples, no
tool definitions.

The Arcade track (`brick_breaker_maximum.md`) is a separate capability benchmark
that uses `max_tokens=32768` and is not part of the VivIndex calculation.

---

## Reproducibility

1. **Fixed prompts:** All four track prompts are hardcoded strings in
   `run_benchmarks.py`. They never change between runs.
2. **Fixed sampling:** Temperature (0.5) and max_tokens (2048) are constants,
   not per-model overrides.
3. **Single-turn:** No model receives conversation context from prior calls or
   prior tracks.
4. **Output capture:** Every raw response is saved to `data/results.json` with
   token counts, latency, cost, and score. Re-scoring can be done offline
   without re-calling the API.
5. **Dry-run mode:** `python3 run_benchmarks.py --dry-run` generates plausible
   sample data at $0 cost. Use this to validate wiring before spending API
   budget.
6. **Real-run mode:** `python3 run_benchmarks.py --run-real` makes live Venice
   API calls. Requires `VENICE_INFERENCE_KEY` environment variable.
7. **Pricing transparency:** Per-call cost is computed from actual token usage
   and the live or fallback pricing table. The pricing source is logged at run
   start.
8. **Timestamps:** Every run record includes a UTC `generated_at` timestamp.

To reproduce a published result set:

```bash
export VENICE_INFERENCE_KEY=<key>
cd /Users/vivgatesai/tmp/benchmark-clone/benchmarks/venice-benchmark-site
python3 run_benchmarks.py --run-real
```

Results are written to `data/results.json`.

---

## Limitations

1. **Heuristic scoring is approximate.** The auto-scorers count keyword
   presence and structural markers. A response that uses the right vocabulary
   but produces broken output can score higher than it deserves. Final
   published scores should be validated with manual or LLM-judge review.
2. **Single-shot, not iterative.** No track allows follow-up turns. Real-world
   usage involves conversation, correction, and iteration. A model that excels
   in single-shot may underperform in agentic loops, and vice versa.
3. **Token cap constrains output.** `max_tokens=2048` is sufficient for plans
   and UI cards but limits long-form HTML generation. Models that produce
   verbose boilerplate may truncate. The Arcade track lifts this to 32768 but
   is not part of VivIndex.
4. **Temperature is fixed.** Some models may perform better at temperature 0
   (deterministic) or 0.7 (creative). Using 0.5 for all is a compromise, not an
   optimum per model.
5. **Pricing is approximate.** Live pricing depends on Venice API state at call
   time. Fallback rates may drift from actual billing. Cost figures are
   estimates, not invoices.
6. **No multi-modal evaluation.** All prompts are text-in, text-out. Vision,
   audio, and tool-use capabilities are not tested.
7. **API availability varies.** A model returning an HTTP error scores 0 for
   that track. This penalizes transient outages as if they were capability
   failures. Re-running failed calls is recommended before publishing.
8. **No statistical significance testing.** Each model/track pair is run once.
   Variance across runs is not measured. For publication-grade results, multiple
   runs with aggregated statistics (mean, std) are recommended.
9. **Model availability.** Not all 11 models may be available on the Venice API
   at all times. The runner logs errors and continues; absent models appear
   with score 0 in results.
