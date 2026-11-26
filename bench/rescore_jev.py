"""Re-ask Jev with new level anchors, reusing the stored captioner observations (no vision calls)."""
import json, glob
from pathlib import Path
from common import *
import judge as J
from judge_jev import build_state, ask_jev, RUBRIC_VERSION

for f in sorted(glob.glob(str(RAW / "judge" / "alpaca-*.json"))):
    j = json.load(open(f))
    if not j.get("observations") or not j.get("motion"):
        continue
    mid = Path(f).stem.replace("alpaca-", "")
    ans = ask_jev(build_state(j["observations"], j["motion"]))
    a = ans.get("answers", ans)
    med, rationale = {}, {}
    for k in ("anatomy", "craft"):
        v = a[k]
        med[k] = max(0, min(4, round(float(v["score"]))))
        rationale[k] = "%s (level %.2f of 4)" % (j["observations"].get(k, {}).get("notes", ""), float(v["score"]))
    ch = j["motion"].get("changed_pct", 0)
    band = 4 if ch >= 6 else 3 if ch >= 3 else 2 if ch >= 1 else 1 if ch > 0 else 0
    planted = float((a.get("feet") or {}).get("noul", 0))
    med["gait"] = max(0, band - (0 if planted >= 0.5 else 1))
    rationale["gait"] = "band %d from %.2f%% pixel change; P(planted, coherent)=%.2f" % (band, ch, planted)
    j.update({"rubric": RUBRIC_VERSION, "median": med, "rationale": rationale, "judges_used": 1})
    json.dump(j, open(f, "w"), indent=1)
    print(mid, med, flush=True)
print("RESCORE DONE")
