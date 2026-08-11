#!/usr/bin/env python3
"""BenchmarkViv model watchdog.

Polls the public Venice models catalog, diffs it against the scored registry
(model_registry.py + data/results.json), and records first-seen dates in
data/known_models.json. Designed to run from cron; with --check-json it emits
{"fire": true/false} so a cron trigger gate only fires when new models exist.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG_URL = "https://api.venice.ai/api/v1/models"
KNOWN_FILE = ROOT / "data" / "known_models.json"

sys.path.insert(0, str(ROOT))
from model_registry import MODELS  # noqa: E402


def fetch_catalog() -> list[dict]:
    req = urllib.request.Request(CATALOG_URL, headers={"User-Agent": "BenchmarkViv-watchdog/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        data = data.get("data", [])
    return [m for m in data if isinstance(m, dict) and m.get("id")]


def load_known() -> dict:
    if KNOWN_FILE.exists():
        return json.loads(KNOWN_FILE.read_text(encoding="utf-8"))
    return {"generated_at": None, "models": {}}


def save_known(known: dict):
    known["generated_at"] = datetime.now(timezone.utc).isoformat()
    KNOWN_FILE.write_text(json.dumps(known, indent=2, ensure_ascii=False), encoding="utf-8")


def registry_ids() -> set[str]:
    ids = {m["id"] for m in MODELS}
    results_file = ROOT / "data" / "results.json"
    if results_file.exists():
        try:
            d = json.loads(results_file.read_text(encoding="utf-8"))
            ids |= {m["id"] for m in d.get("models", [])}
        except Exception:
            pass
    return ids


def log(msg: str, check_json: bool):
    # keep stdout pure (JSON only) when running as a cron gate
    print(msg, file=sys.stderr if check_json else sys.stdout)


def main() -> int:
    check_json = "--check-json" in sys.argv
    try:
        catalog = fetch_catalog()
    except Exception as exc:  # network / API hiccup — don't fire
        log(f"watchdog: catalog fetch failed: {exc}", check_json)
        if check_json:
            print('{"fire": false}')
        return 2

    known = load_known()
    prior = set(known.get("models", {}))
    tracked = registry_ids()

    now = datetime.now(timezone.utc).isoformat()
    new_models = []
    for m in catalog:
        mid = m["id"]
        if mid in tracked:
            continue
        meta = known["models"].get(mid)
        if meta is None:
            meta = {"id": mid, "first_seen": now, "display": m.get("name") or mid}
            known["models"][mid] = meta
            new_models.append(meta)
    save_known(known)

    # models we tracked before but that vanished from the catalog
    gone = sorted(prior - {m["id"] for m in catalog})
    new_ids = sorted({m["id"] for m in new_models})

    if new_models:
        log(f"watchdog: {len(new_models)} NEW model(s) not in BenchmarkViv registry:", check_json)
        for m in sorted(new_models, key=lambda x: x["id"]):
            log(f"  + {m['id']}  (first_seen {m['first_seen']})", check_json)
    else:
        log(f"watchdog: no new models — {len(catalog)} live, {len(tracked)} tracked", check_json)
    if gone:
        log(f"watchdog: {len(gone)} previously seen model(s) no longer in catalog: {', '.join(gone)}", check_json)

    if check_json:
        print(json.dumps({"fire": bool(new_models), "new_count": len(new_models)}))
    return 0 if new_models else (1 if gone else 0)


if __name__ == "__main__":
    sys.exit(main())
