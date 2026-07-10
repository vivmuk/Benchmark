# Arcade Maximum Standalone Game — canonical prompt

This prompt is sent verbatim to every model in the canonical BenchmarkViv roster.
The Arcade is a capability showcase, not the scored Brick Breaker benchmark.

```text
Create the most polished, technically ambitious Brick Breaker game you can within this response. Return exactly one complete, standalone HTML document and nothing else.

Hard constraints:
- It must run locally by opening the .html file: no CDN, package, network request, external image, font, audio, asset, API, or build step.
- Use only HTML, CSS, and vanilla JavaScript. Canvas is required. Web Audio API may be used after a user gesture.
- Begin with <!doctype html> and end with </html>. Do not wrap the answer in Markdown fences.

Build a complete game, not a prototype. Include a distinctive art direction, a responsive high-DPI Canvas renderer, deterministic game loop, polished ball/paddle/brick collision resolution, multiple levels with varied layouts, progressive difficulty, lives/score/combo, pause/restart, keyboard + mouse + touch controls, and usable mobile layout.

Push quality where it helps: power-ups with clear effects, particles/screen shake/trails, boss or special bricks, local high-score persistence, synthesized audio, settings for sound and reduced motion, onboarding, high-contrast text, visible focus states, and an accessible non-canvas status/instruction layer. Handle tab visibility, resize, and game-over/victory states gracefully.

Prefer robust, maintainable code over commentary. Do not claim features that are not implemented.
```

## Protocol
- Temperature: 0.5.
- Each request uses the model's maximum practical completion allowance advertised by the provider at run time, capped only by the Arcade safety ceiling recorded in the manifest.
- Raw response, extracted HTML, token usage, errors, and browser validation are retained. No output is manually edited.
