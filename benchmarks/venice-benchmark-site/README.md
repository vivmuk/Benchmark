# BenchmarkViv

Practical benchmark suite and interactive showcase for Venice API models.

[![Live site](https://img.shields.io/badge/site-benchmarkviv.up.railway.app-00D4AA)](https://benchmarkviv.up.railway.app)
[![Top model](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fbenchmarkviv.up.railway.app%2Fdata%2Fsummary.json&query=top_model&label=%231%20model&color=D9A441)](https://benchmarkviv.up.railway.app)
[![VivIndex](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fbenchmarkviv.up.railway.app%2Fdata%2Fsummary.json&query=top_viv&label=VivIndex&color=00D4AA)](https://benchmarkviv.up.railway.app)
[![Models](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fbenchmarkviv.up.railway.app%2Fdata%2Fsummary.json&query=n_models&label=models&color=1A1A2E)](https://benchmarkviv.up.railway.app)
[![Generated](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fbenchmarkviv.up.railway.app%2Fdata%2Fsummary.json&query=generated_at&label=updated&color=7a8294)](https://benchmarkviv.up.railway.app)

Live leaderboard of Venice API models scored on practical tracks (intent
understanding, one-shot UI, startup planning, pharma domain, value density,
reverse-prompt vision) with a weighted **VivIndex** composite.

## Pages

- **Leaderboard** — index.html, #1 model crowned
- **Vision** — vision.html, reverse-prompt reconstructions
- **Trends & Movers** — trends.html, VivIndex history from dated snapshots
- **Compare** — compare.html, pick up to 3 models side-by-side
- **Design** — experimental-design.html
- **About** — about.html, methodology

## Data

- `data/results.json` — canonical results (full raw responses)
- `data/chart_snapshot.json` — leaderboard snapshot for charts
- `data/benchmarkviv-results.csv` — flat export, 1 row per result
- `data/summary.json` — top model / VivIndex / count (powers the badges)
- `data/trends.json` + `data/trends_chart.svg` — history series + chart
- `data/changelog.json` — site changelog

## Rebuild pipeline

```bash
python3 make_exports.py          # CSV + summary.json
python3 make_trends.py           # trends.json + chart + trends.html
python3 make_compare.py          # compare.html
python3 make_chart.py            # leaderboard chart data
python3 make_svg_chart.py        # leaderboard_chart.svg
python3 make_infographic_2x2.py  # infographics
python3 make_model_pages.py      # models/<slug>.html profiles
python3 generate_standalone.py   # benchmarkviv-standalone.html
```

## Watchdog

`watch_models.py` polls the public Venice catalog, diffs against the scored
registry, and records first-seen dates in `data/known_models.json`:

```bash
python3 watch_models.py            # print new models found
python3 watch_models.py --check-json  # {"fire": true/false} for cron gates
```

Suggested cron: weekly, fire only when new models appear, then benchmark them.

## Local preview

```bash
cd /Users/vivgatesai/.openclaw/workspace/benchmarks/venice-benchmark-site
python3 -m http.server 8080
```

Open http://localhost:8080

## Run benchmarks

```bash
export VENICE_INFERENCE_KEY=<your-key>
python3 run_benchmarks.py --dry-run   # sample data, $0
python3 run_benchmarks.py --run-real  # real API calls (~$2-5)
```

## Deploy to Railway

Add this repo to Railway as a static site. Serve the root directory.
No build step required. `git push` to `vivmuk/Benchmark` (main) auto-deploys.
