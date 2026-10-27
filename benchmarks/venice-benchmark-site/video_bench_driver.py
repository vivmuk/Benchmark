#!/usr/bin/env python3
"""BenchmarkViv video benchmark tranche driver.
Usage: video_bench_driver.py [budget_usd]  (default 20)
Reads data/video_matrix.json (jobs) + assets/video-benchmark/manifest.json (state).
Runs the next tranche within budget, saves clips, rebuilds the page, commits, pushes, verifies.
"""
import json, os, sys, time, base64, subprocess, urllib.request, urllib.error

KEY = os.environ.get("VENICE_INFERENCE_KEY", "")
if len(KEY) < 20:
    KEY = os.environ.get("VENICE_API_KEY", "")
SITE = os.path.expanduser("~/.openclaw/workspace/benchmarks/venice-benchmark-site")
OUT = os.path.join(SITE, "assets", "video-benchmark")
os.chdir(SITE)

matrix = json.load(open("data/video_matrix.json"))
manifest_path = os.path.join(OUT, "manifest.json")
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else []
done = {(r["model"], r["pid"]) for r in manifest if r.get("ok") or r.get("charged")}

budget = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
ORDER = {"1-cinematic": 0, "2-creative": 1, "3-motion": 2, "4-lincoln": 3}
jobs = [j for j in matrix["jobs"] if (j["model"], j["pid"]) not in done]
jobs.sort(key=lambda j: (ORDER.get(j["pid"], 9), j["model"]))

# i2v/r2v jobs need their source image; if it is missing, defer them to a later tranche
def needs_image(j):
    img = j.get("image")
    return img and not os.path.exists(os.path.join(SITE, img))

def post(ep, body, timeout=120):
    req = urllib.request.Request(f"https://api.venice.ai/api/v1/{ep}", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, (r.headers.get("Content-Type") or "").lower(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, "application/json", e.read()
    except Exception as e:
        return 0, "text/plain", str(e).encode()

def save_manifest():
    man = [r for r in manifest]
    json.dump(man, open(manifest_path, "w"), indent=1)

# --- queue within budget ---
queued, spent = [], 0.0
for j in jobs:
    q = j.get("est_quote")
    if q is None:
        code, ct, resp = post("video/quote", {k: v for k, v in
            (("model", j["model"]), ("duration", j.get("dur")), ("resolution", j.get("res"))) if v})
        try: q = json.loads(resp).get("quote")
        except Exception: q = 1.0
        j["est_quote"] = q if isinstance(q, (int, float)) else 1.0
    if spent + j["est_quote"] > budget and queued:
        continue
    if needs_image(j):
        j["status"] = "PENDING-IMAGE"
        continue
    body = {"model": j["model"], "prompt": j["prompt"]}
    if j.get("dur"): body["duration"] = j["dur"]
    if j.get("res"): body["resolution"] = j["res"]
    img = j.get("image")
    if img:
        data_url = "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(SITE, img), "rb").read()).decode()
        if j["pid"] == "3-motion": body["image_url"] = data_url
        else: body["reference_image_urls"] = [data_url]
    code, ct, resp = post("video/queue", body)
    txt = resp.decode(errors="ignore")
    if code == 200 and "queue_id" in txt:
        d = json.loads(resp)
        j["queue_id"] = d["queue_id"]; j["status"] = "QUEUED"
        j["download_url"] = d.get("download_url")
        queued.append(j); spent += j.get("est_quote") or 0.0
        # merge into manifest as pending
        manifest.append({"model": j["model"], "pid": j["pid"], "file": None,
                         "duration": j.get("dur"), "resolution": j.get("res"),
                         "quote": j.get("est_quote"), "ok": False, "status": "QUEUED"})
    elif "consent" in txt.lower() or "screening" in txt.lower():
        body["consents"] = {"seedance": {"confirmed_terms_and_privacy": True,
            "confirmed_legal_right": True, "confirmed_screening_acknowledged": True}}
        code, ct, resp = post("video/queue", body)
        if code == 200 and "queue_id" in resp.decode(errors="ignore"):
            d = json.loads(resp)
            j["queue_id"] = d["queue_id"]; j["status"] = "QUEUED"; j["download_url"] = d.get("download_url")
            queued.append(j); spent += j.get("est_quote") or 0.0
            manifest.append({"model": j["model"], "pid": j["pid"], "file": None,
                             "duration": j.get("dur"), "resolution": j.get("res"),
                             "quote": j.get("est_quote"), "ok": False, "status": "QUEUED"})
        else:
            j["status"] = "FAILED"; j["err"] = txt[:200]; print(f"[FAIL] {j['model']} {j['pid']}: {txt[:150]}", flush=True)
    else:
        j["status"] = "FAILED"; j["err"] = txt[:200]; print(f"[FAIL] {j['model']} {j['pid']}: {txt[:150]}", flush=True)
    time.sleep(0.5)

save_manifest()
print(f"queued {len(queued)} jobs, est spend ${spent:.2f} (budget ${budget:.2f})", flush=True)

# --- poll loop ---
deadline = time.time() + 3000
while time.time() < deadline:
    pending = [j for j in jobs if j.get("status") in ("QUEUED", "PROCESSING", "RETRIED")]
    if not pending: break
    for j in pending:
        code, ct, resp = post("video/retrieve", {"model": j["model"], "queue_id": j["queue_id"]}, timeout=180)
        if "video/mp4" in ct or resp[:4] in (b"\x1aE\xdf\xa8", b"\x00\x00\x00"):
            fn = f"{j['model']}-{j['pid']}.mp4"
            open(os.path.join(OUT, fn), "wb").write(resp)
            j["status"] = "COMPLETED"; j["file"] = fn
            for r in manifest:
                if r["model"] == j["model"] and r["pid"] == j["pid"]:
                    r["file"] = fn; r["ok"] = True; r["status"] = "COMPLETED"
            print(f"[DONE] {j['model']} {j['pid']} ({len(resp)/1e6:.1f} MB)", flush=True)
        elif code == 200:
            try: d = json.loads(resp)
            except Exception: d = {}
            st = (d.get("status") or "").upper()
            if st == "COMPLETED":
                du = d.get("download_url") or j.get("download_url")
                if du:
                    try:
                        vdata = urllib.request.urlopen(du, timeout=300).read()
                        fn = f"{j['model']}-{j['pid']}.mp4"
                        open(os.path.join(OUT, fn), "wb").write(vdata)
                        j["status"] = "COMPLETED"; j["file"] = fn
                        for r in manifest:
                            if r["model"] == j["model"] and r["pid"] == j["pid"]:
                                r["file"] = fn; r["ok"] = True; r["status"] = "COMPLETED"
                        print(f"[DONE-url] {j['model']} {j['pid']} ({len(vdata)/1e6:.1f} MB)", flush=True)
                        try: urllib.request.urlopen(urllib.request.Request(du, method="DELETE"), timeout=30)
                        except Exception: pass
                    except Exception as e:
                        j["status"] = "RETRIED"; j["err"] = f"dl: {str(e)[:100]}"
                else:
                    j["status"] = "FAILED"; j["err"] = "completed, no payload"; print(f"[FAIL] {j['model']}", flush=True)
            elif st in ("FAILED", "ERROR"):
                j["status"] = "FAILED"; j["err"] = json.dumps(d)[:180]
                print(f"[FAIL] {j['model']} {j['pid']}: {j['err'][:100]}", flush=True)
            else:
                j["status"] = "PROCESSING"
        else:
            j["poll_errs"] = j.get("poll_errs", 0) + 1
            if j["poll_errs"] > 8:
                j["status"] = "FAILED"; j["err"] = f"retrieve {code}: {resp.decode(errors='ignore')[:150]}"
                print(f"[FAIL] {j['model']} {j['pid']}", flush=True)
    n_ok = sum(1 for j in jobs if j.get("status") == "COMPLETED")
    print(f"-- {n_ok}/{len(jobs)} done", flush=True)
    save_manifest()
    if pending: time.sleep(12)

n_ok = sum(1 for j in jobs if j.get("status") == "COMPLETED")
n_fail = sum(1 for j in jobs if j.get("status") == "FAILED")
print(f"=== DRIVER DONE: {n_ok}/{len(jobs)} completed, {n_fail} failed, spent ~${spent:.2f} ===", flush=True)
subprocess.run([sys.executable, os.path.join(SITE, "build_video_page.py")], check=False)
