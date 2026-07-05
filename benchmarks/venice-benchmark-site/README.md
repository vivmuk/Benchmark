# BenchmarkViv

Long-horizon benchmark suite and interactive showcase for Venice API models.

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
No build step required.
