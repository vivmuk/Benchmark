#!/usr/bin/env python3
"""Generate a BenchmarkViv infographic (DeepSeek V4 Flash 0731 head-to-head)
via the Venice image API."""
import base64, json, os, re, requests, sys

KEY = ""
txt = open("/Users/vivgatesai/.openclaw/service-env/ai.openclaw.gateway.env").read()
m = re.search(r"^(?:export )?VENICE_API_KEY=[\'\"]?(.*?)[\'\"]?$", txt, re.M)
KEY = m.group(1)

# ---- compute comparison snapshot ----
data = json.load(open("data/results.json"))
WEIGHTS = {"intent-understanding":0.20,"one-shot-ui":0.15,"startup-in-a-weekend":0.25,
           "value-density":0.20,"reverse-prompt-vision":0.20}
rows = {}
for r in data["results"]:
    rows.setdefault(r["model_id"], {})[r["benchmark_id"].replace("_","-")] = r
disp = {mm["id"]: mm["display"] for mm in data["models"]}
out = []
for mid, rs in rows.items():
    sc = {k: v["score"] for k, v in rs.items() if v.get("score") is not None}
    wsum = wtt = 0
    for k, w in WEIGHTS.items():
        if k in sc: wsum += sc[k]*w; wtt += w
    out.append({"id": mid, "disp": disp.get(mid, mid), "viv": round(wsum/wtt, 1) if wtt else 0,
                "scores": sc})
out.sort(key=lambda x: -x["viv"])
for i,o in enumerate(out):
    print(f"{i+1}. {o['disp']:24} VivIndex={o['viv']}")
json.dump(out, open("data/chart_snapshot.json", "w"), indent=2)
