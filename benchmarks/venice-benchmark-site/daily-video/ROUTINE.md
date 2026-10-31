# BenchmarkViv Daily Video Routine

Goal: one AI-generated video per day, added to the site's Daily Video tab, deployed, and sent to Vivek on Telegram.

## Steps

1. Work dir: `/Users/vivgatesai/.openclaw/workspace/benchmarks/venice-benchmark-site`
   `VENICE_API_KEY` is already in the exec environment (do not print it).
2. Write a FRESH prompt each day (never reuse). On-brand palette: teal `#00D4AA`, cream `#FEFCF8`, indigo `#1A1A2E`. Theme ideas to rotate: benchmark control room, AI model "specimens", data-center macro shots, abstract data-flow art, GPU silicon macro. No text/watermarks in prompt.
3. Default model: `seedance-2-0-mini-text-to-video-basic`, `duration: "4s"`, `resolution: "480p"`, `aspect_ratio: "16:9"`, NO `audio` field (several models reject it).
   Price with `POST https://api.venice.ai/api/v1/video/quote` first.
   On `402 Insufficient balance`: try one cheaper option if any; if still blocked, STOP and report "Venice key out of media balance" — never fake completion.
4. Enqueue with `POST /video/queue` → save `queue_id` (+ `download_url` if present).
5. Poll `POST /video/retrieve` every 10 s (max 10 min): `content-type: video/mp4` → save body to
   `assets/daily-videos/YYYY-MM-DD-<model>.mp4`. If JSON says `PROCESSING`, keep polling.
   VPS-backed models: on `COMPLETED` fetch the `download_url` (expires 24 h).
6. Finalize: `POST /video/complete` with model + queue_id.
7. Prepend an entry to `assets/daily-videos/manifest.json` → `videos`:
   `{"date":"YYYY-MM-DD","title":"<short title>","file":"assets/daily-videos/<filename>","model":"<model>","duration":"4s","resolution":"480p","quote":<price>,"prompt":"<prompt>"}`
8. Run `python3 tools/build_daily_page.py` (idempotent; rebuilds page + nav). Skip if only manifest changed and nav already present.
9. Commit (`Daily video YYYY-MM-DD: <title>`) and push to `origin/main`.
10. Deploy: `/bin/sh /Users/vivgatesai/.openclaw/state/benchmark-deploy-watch.sh` (triggers Railway via API; prints `deploy-triggered <sha>`). The 15-min watcher would also catch it — running the script makes it immediate.
11. Verify: `curl -s https://benchmarkviv.up.railway.app/assets/daily-videos/manifest.json` shows the new entry (Railway builds take ~5–10 min; don't call it broken before that).
12. Send the video file to Telegram chat `6808691714` via the `message` tool (media + one-line caption with title/model). The video itself is the deliverable — send the actual file, not just a link.

## Rules

- NEVER fabricate completion. If any step fails, report exactly what failed.
- Keep total daily media spend ≤ $0.50 unless explicitly told otherwise.
- Don't touch the video-benchmark tab or run video benchmarks — daily creative video only.
