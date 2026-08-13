# Alpaca HTML Test — single-shot benchmark prompt

This prompt is run verbatim against all eligible models for the Alpaca HTML Test
track of BenchmarkViv. All models receive the same prompt, the same
`temperature=0.5` and `max_tokens=2048`, and no prior conversation. Per-model
output is saved and scored against the seven-criterion rubric below.

## Prompt

```
Create a single self-contained HTML file for a modern product landing page
for a fictional app called "Alpaca CRM". The page must include:

  - A responsive navigation bar with logo, links, and a CTA button
  - A hero section with headline, subheadline, and two CTA buttons
  - A features section with at least three feature cards (icon, title, description)
  - A testimonials section with at least two customer quotes
  - A pricing section with three tiers (Free, Pro, Enterprise)
  - A footer with links, social icons, and copyright text

Requirements:
  - Use only HTML, CSS, and vanilla JavaScript — no external libraries or CDNs
  - Inline all CSS in a <style> tag and all JS in a <script> tag
  - Make the layout fully responsive (mobile-first, with media queries for tablet/desktop)
  - Use CSS Flexbox or Grid for layout — no float or table hacks
  - Include at least one CSS animation (e.g., fade-in on hero load, hover transitions on cards)
  - Add a simple JS interaction: a mobile hamburger menu toggle that opens/closes the nav links
  - Use semantic HTML5 elements (header, nav, main, section, footer, article)
  - Ensure the HTML would pass W3C validation (proper nesting, closed tags, valid attributes)
  - Respect prefers-reduced-motion in your CSS animations
  - Use a clean, modern color palette with good contrast and readable typography

Output only the HTML file, starting with <!DOCTYPE html> and ending with </html>.
Do not include any explanation, markdown formatting, or commentary outside the HTML.
```

## Scoring Breakdown (0–100)

| Criterion | Max Points | Description |
|---|---|---|
| Structure | 15 | Valid HTML5 doctype, semantic elements (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`), logical DOM hierarchy, all tags properly closed. |
| CSS | 15 | Quality of internal stylesheet: selector usage, specificity control, Flexbox/Grid layout, consistent design tokens (colors, spacing, fonts). |
| Responsive | 15 | Mobile-first approach with media queries for tablet and desktop breakpoints. Layout reflows correctly at all widths. No horizontal overflow on mobile. |
| JavaScript | 15 | Hamburger menu toggle works correctly. Event listeners are properly attached. No runtime errors. State management is clean (class toggle, aria-expanded). |
| Validation | 15 | HTML passes W3C validator: no unclosed tags, no invalid attributes, no deprecated elements, correct nesting order. |
| Animations | 10 | At least one CSS animation or transition (fade-in, hover effects, slide). `prefers-reduced-motion` media query disables or reduces motion. |
| Content | 15 | All required sections present (nav, hero, features, testimonials, pricing, footer). Text content is meaningful, complete, and consistent with the "Alpaca CRM" theme. Icons can be CSS/Unicode/inline SVG. |

## Scoring Notes

- **Auto-scored first:** The heuristic scorer in `run_benchmarks.py` checks for
  keyword presence (semantic tags, media queries, `addEventListener`, animation
  properties, `prefers-reduced-motion`, section coverage) to produce a rapid
  ballpark score.
- **Manual/LLM-judge review:** Final published scores are reviewed against the
  rubric above. A model that includes the right keywords but produces broken or
  non-functional output is penalized in manual review.
- **Zero-fix bonus:** Output that renders correctly in a browser with no
  modifications earns full marks in the applicable criteria. Output requiring
  fixes is capped at 80% of the criterion's max points.
- **Truncation handling:** If output is cut off at `max_tokens=2048`, the
  incomplete HTML is scored on what was produced. Missing closing tags due to
  truncation do not automatically zero the Structure/Validation criteria but
  do reduce them proportionally.

## Cost Envelope

With `max_tokens=2048` and 11 models, worst-case cost for this track alone:

| Model | Worst-case (1 call) |
|---|---|
| GPT-5.6 Sol | ~$0.077 |
| GPT-5.5 | ~$0.077 |
| Opus 5 | ~$0.061 |
| Sonnet 5 | ~$0.031 |
| GLM 5.2 | ~$0.009 |
| DeepSeek V4 | ~$0.007 |
| Gemini 3.6 Flash | ~$0.019 |
| Grok 4.6 | ~$0.014 |
| Qwen 3.8 Max | ~$0.015 |
| Kimi K3 | ~$0.038 |
| MiniMax M3 | ~$0.002 |
| **Total** | **~$0.35** |

Actual cost will be lower since most models do not fill the full 2048-token
budget on a single landing page.

## Output Handling

- If the response contains a code-block fence (` ```html … ``` `), the inner
  HTML is extracted.
- If the response starts with `<!DOCTYPE html>` directly, the full response is
  saved as-is.
- If neither, the response is stored as raw text and the HTML slot is `null`,
  indicating no valid output was captured.
