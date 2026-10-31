# Model Prompting Guide — Anthropic & OpenAI (for agent / prompt-optimizer use)

## ANTHROPIC — CLAUDE (latest vs previous)

### Claude Opus 5.5 (current — claude-opus-5-5)
- Thinking is ALWAYS ON. Rejects `thinking:{"type":"disabled"}` (and manual budget_tokens). Omit the field, or send `{"type":"adaptive"}`.
- Default effort = **medium** (Opus 5 defaulted to high). Always set `effort` explicitly.
- Effort calibration: start at **medium**. Drop to **low** for less thinking/latency/cost. Reserve **high/xhigh/max** only after you measure a real quality gain.
- Long agentic turns: set `max_tokens=128000` (thinking counts against max_tokens even when not returned).
- ~30% faster + fewer output tokens than Opus 5 for the same task.
- Capabilities to lean on: multistep agentic coding/code review (medium ≈ Opus 5 at high, fewer steps), knowledge work (fewer wrong figures/citations), dense visuals/computer-use (strong even at low effort), plain-language progress reports.
- Progress updates arrive as `thinking` blocks, empty by default. Set `display:"updates"` to surface them (beta header `thinking-display-updates-2026-08-18`).
- Unattended agents: a text-only `end_turn` is a REPORT, not completion. Add a standing "keep working" instruction + keep an open-items checklist; auto-continue at most 2–3 times.
- Do NOT ask it to reproduce its internal reasoning in the response — triggers `reasoning_extraction` refusal. Use `display:"summarized"` if you need its reasoning.
- New safeties: biology (same as Fable 5.1), cybersecurity (finding vulns OK; high-risk dual-use not), reasoning_extraction.
- Frontend: supply explicit design defaults (colors/fonts/layout) or output looks generic.
- Complex visuals: give it tools to crop/analyze rather than relying on thinking.

### Claude Opus 5 (previous — claude-opus-5)
- Thinking on by default; `disabled` accepted at high effort or below.
- Default effort = **high**.
- Verbose by default — add an explicit conciseness instruction to shorten responses.
- Strong agentic coding when given the full spec up front and left to run.

### Claude Fable 5.1 (claude-fable-5-1)
- Shares 3 breaking changes with Opus 5.5: thinking can't be disabled; forced tool use errors; thinking blocks tied to model+conversation.
- Same new biology safeguard as Opus 5.5.

### Claude Sonnet 5.5 / Sonnet 5
- Medium-effort reasoning; cheaper/faster tier. Follow Opus 5.5 effort-calibration rules (start medium, set explicitly).

### KEY DIFF (Opus 5.5 vs Opus 5): thinking always-on, effort default medium (not high), thinking-blocks architecture, new end_turn report behavior, new reasoning_extraction + biology safeties.

## OPENAI — GPT-6.x (latest) vs GPT-5.6

### GPT-6.1 Sol (latest flagship), GPT-6 Sol / Luna / Astra / Astra Pro
- Reasoning on by default; effort controllable where supported (default often "high" — calibrate down).
- GPT-6.1 Sol is the strongest current Sol; prefer it for knowledge/coding over GPT-6 Sol.
- Luna = low-cost fast tier; Astra = top reasoning tier.
- Prefer explicit effort calibration + generous max_tokens (128k) for long agentic work.

### GPT-5.6 Sol / Luna / Terra (+ Pro variants) — previous generation
- Superseded by GPT-6.x. Use GPT-6.1 Sol / GPT-6 Astra for quality; GPT-6 Luna for cheap/fast.
- Seed previous-generation prompts as-is; they should perform well.

## UNIVERSAL RULES (paste into any agent harness)
1. Set reasoning `effort` explicitly every call; default to the model's documented default.
2. `max_tokens` must leave room for hidden thinking — use the model's max for long agentic turns.
3. A text-only end-of-turn with no tool call is a progress report, not completion. Continue if open tasks remain (cap 2–3 auto-continuations).
4. Never instruct a reasoning model to "show your chain-of-thought"; read summarized thinking via the API instead.
5. Give tools for visual/diagram work rather than asking it to think through pixels.
6. Supply explicit frontend design tokens when generating UI.