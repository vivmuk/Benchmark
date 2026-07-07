# Brick Breaker Maximum — single-shot benchmark prompt

This prompt is run verbatim against all eligible models for the BenchmarkViv Arcade lineup.
All models receive the same prompt, the same `max_tokens=32768`, and no prior conversation.
Per-model output is saved as `arcade/&lt;model-id&gt;-brick.html` and the run is recorded in
`data/brick_arcade.json`. The existing Fable 5 brick from the original benchmark prompt
(`brick_breaker_realism` in the leaderboard) is kept as a 6th slot for continuity.

## Prompt

```
Generate a single self-contained HTML file containing the most advanced,
fully-featured Brick Breaker game you are capable of producing in one prompt.

Use everything you know:
  - Canvas (and WebGL where it earns complexity)
  - Ball physics with angle reflection off paddle (subtle spin on contact)
  - Multi-ball, multiple levels with progression, persistent best score in localStorage
  - Power-ups (multi-ball, paddle extend, slow ball, sticky paddle, laser, life)
  - Particle trails on ball motion + explosions on brick break
  - Web Audio API for synthesized sound effects (no external audio assets)
  - Score, lives, level, start screen, in-game HUD, game-over, victory
  - Mobile gestures (touch to launch, swipe to move paddle) and keyboard (arrows / WASD)
  - Accessibility: prefers-reduced-motion fallback, color contrast for HUD, focus rings

Inline all CSS, JS, and audio. No external libraries, no CDN imports, no fetched images.
Make it feel polished and production-quality. Output only the HTML file, starting with
<!DOCTYPE html> and ending with </html>. Nothing else.
```

## Why "Maximum" not "Realism"

The original `brick_breaker_realism` benchmark prompt is a sanity check:
single-shot, physics+particles+sound, dark-neon-look. The Arcade lineup is a
*capability* benchmark; it asks each model to self-direct toward the most
ambitious single-file game it can ship. Output length is uncapped up to the
model's per-call maximum. The prompt deliberately does NOT enumerate every
feature -- leaving room for each model to show what it prioritizes when
given freedom.

## Output handling

- If the model's response contains a code-block fence (```html … ```), the
  inner HTML is extracted and saved.
- If the response starts with `<!DOCTYPE html>` directly, the full response
  is saved as-is.
- If neither, the response is stored as `arcade/<model>-brick.raw.txt` and
  the `html` slot in `data/brick_arcade.json` is `null` (so the Arcade page
  shows a "no output captured" placeholder for that model).

## Scoring heuristic

Reuses `score_brick_breaker_realism` from `run_benchmarks.py`. The heuristic
counts keyword presence for:
- canvas / RAF
- paddle / brick logic
- game states (start/play/over/victory)
- physics (angle, reflection, spin)
- particles / sound / responsive
- polish (power-ups, multi-ball, levels, localStorage, reduced-motion, focus rings)

Score remains a heuristic. Heuristic-failing entries that actually run well are
worth keeping -- the Arcade page renders them anyway, ranked by score.

## Cost envelope

| Model | Approx. worst-case output cost (32K completion) |
|---|---|
| Opus 4.8 | $2.40 |
| GPT-5.5 | $0.96 |
| GLM 5.2 | $0.10 |
| DeepSeek V4 | $0.07 |
| MiniMax M3 | $0.05 |
| **Total** | **~$3.58** |

Well under the daily $10 cap. Run with `--dry-run` for $0 first; run with
`--run-real` once you've reviewed the wiring.
