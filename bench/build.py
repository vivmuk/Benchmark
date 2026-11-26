"""Phase 3: turn raw results into site/data.js."""
import datetime, re, statistics
from common import *

sp = load(RAW / "specs.json")
answers = load(ROOT / "bench" / "answers.json")
motion = load(RAW / "motion.json", {})


def norm(v):
    return re.sub(r"[\s,$_]", "", str(v)).upper().replace("0X", "").split(".")[0] if not isinstance(v, float) else str(round(v))


def grade(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None
    out = {}
    for q, a in answers.items():
        got = d.get(q)
        out[q] = got is not None and (norm(a) in norm(got) if q == "q3" else norm(got) == norm(a))
    return out


WEIGHTS = {"anatomy": 0.40, "gait": 0.40, "craft": 0.20}


def judged(task, mid):
    j = load(RAW / "judge" / ("%s-%s.json" % (task, mid)), {})
    if task == "alpaca" and j.get("median"):
        med = j["median"]
        score = round(sum(WEIGHTS[k] * med[k] / 4 for k in WEIGHTS) * 100, 1)
        used = [k for k, v in j.items() if isinstance(v, dict) and "scores" in v]
        if used:
            by = {k: round(sum(WEIGHTS[c] * j[k]["scores"][c] / 4 for c in WEIGHTS) * 100, 1) for k in used}
            rat = (j.get(used[0]) or {}).get("rationale", {})
            verd = {k: j[k].get("verdict", "") for k in used}
        else:
            by = {("jev+" + j.get("captioner", "captioner")): score}
            rat = j.get("rationale") or {}
            verd = j.get("verdict") or {}
        return {"score": score, "criteria": med, "by_judge": by, "rationale": rat, "verdict": verd,
                "setting": j.get("setting"), "judges": j.get("judges_used", len(by)), "rubric": j.get("rubric"), "scale": 4}
    ok = {k: v for k, v in j.items() if "scores" in v}
    if not ok:
        return None
    keys = list(next(iter(ok.values()))["scores"])
    crit = {k: round(statistics.mean(v["scores"][k] for v in ok.values()), 1) for k in keys}
    per = {k: round(statistics.mean(v["scores"].values()) * 10, 1) for k, v in ok.items()}
    return {"score": round(statistics.mean(per.values()), 1), "criteria": crit, "by_judge": per,
            "notes": {k: v["note"] for k, v in ok.items()}, "judges": len(ok)}


def meta(r):
    u = r.get("usage") or {}
    return {"out_tokens": u.get("completion_tokens"), "cost": r.get("cost"), "seconds": round(r["t_total"], 1),
            "finish": r.get("finish")}


def gen_task(task, mid):
    r = load(RAW / task / (mid + ".json"))
    if not r:
        return {"status": "not run"}
    if r.get("error"):
        return {"status": "failed", "error": "%s: %s" % (r["error"], str(r.get("body", ""))[:160])}
    if incomplete(r):
        return {"status": "failed", "error": "Venice closed the stream at %d minutes, before the model finished. Output incomplete, not scored." % round(r["t_total"] / 60)}
    d = dict(meta(r), status="ok")
    j = judged(task, mid)
    if j:
        d.update(j)
    else:
        d["status"] = "unscored"
    return d



def compliance(mid, ms):
    """Brief compliance, checked in code rather than by a judge: self-contained, fits 1280x720, animates, renders."""
    import re as _re
    notes, ok = [], 0
    html_p = SITE / "out" / "alpaca" / (mid + ".html")
    html = html_p.read_text(errors="ignore") if html_p.exists() else ""
    ext = _re.findall(r'(?:src|href)\s*=\s*["\']https?://|url\(\s*["\']?https?://|@import\s+url\(', html, _re.I)
    if ext:
        notes.append("links to %d external asset(s)" % len(ext))
    else:
        ok += 1
    meta_p = RAW / "shots" / ("alpaca-%s-meta.json" % mid)
    meta = load(meta_p, {}) or {}
    sw = max(meta.get("sw") or 0, meta.get("bw") or 0)
    sh = max(meta.get("sh") or 0, meta.get("bh") or 0)
    if sw and sh and sw <= 1282 and sh <= 722:
        ok += 1
    elif sw or sh:
        notes.append("overflows the 1280x720 stage (%dx%d)" % (sw, sh))
    if (ms or {}).get("changed_pct", 0) >= 1:
        ok += 1
    else:
        notes.append("barely animates")
    if len(html) > 800:
        ok += 1
    else:
        notes.append("almost no markup")
    return ok, notes


NAME_OVERRIDE = {"e2ee-kimi-k3-1-pro-p": "Kimi K3.1 Pro (E2EE)"}

models, spend = [], 0.0
for mid in MODELS:
    s = sp[mid]
    m = {"id": mid, "name": NAME_OVERRIDE.get(mid, s["name"]), "lab": s["lab"], "icon": "logos/%s.svg" % dict(ICONS).get(s["family"], "venice-color"),
         "released": datetime.datetime.fromtimestamp(s["created"], datetime.timezone.utc).date().isoformat(), "price_in": s["in"], "price_out": s["out"],
         "vision": s["vision"]}
    m["alpaca"] = gen_task("alpaca", mid)
    if m["alpaca"]["status"] != "failed":
        ms = motion.get(mid) or {}
        if isinstance(ms, dict):
            m["alpaca"]["motion"] = ms.get("mean")
            m["alpaca"]["motion_changed"] = ms.get("changed_pct")
            m["alpaca"]["motion_leg"] = ms.get("leg_pct")
        else:
            m["alpaca"]["motion"] = ms
        c, cnotes = compliance(mid, ms)
        m["alpaca"]["compliance"] = c
        m["alpaca"]["compliance_notes"] = cnotes
        if m["alpaca"].get("criteria"):
            crit = dict(m["alpaca"]["criteria"])
            ch = (ms or {}).get("changed_pct", 0)
            band = 4 if ch >= 6 else 3 if ch >= 3 else 2 if ch >= 1 else 1 if ch > 0 else 0
            if crit.get("gait", 0) > band:
                crit["gait"] = band
            m["alpaca"]["criteria"] = crit
            m["alpaca"]["gait_band"] = band
            visual = round(sum(WEIGHTS[k] * crit[k] / 4 for k in WEIGHTS) * 100, 1)
            m["alpaca"]["score_visual"] = visual
            m["alpaca"]["score"] = round(visual * (0.75 + 0.0625 * c), 1)
    m["design"] = gen_task("design", mid)

    if not s["vision"]:
        m["recreate"] = {"status": "no vision", "error": "This model cannot take image input."}
    else:
        m["recreate"] = gen_task("vision", mid)
        r = load(RAW / "vision" / (mid + ".json")) or {}
        if r.get("text"):
            m["recreate"]["prompt"] = r["text"].strip()
        if m["recreate"]["status"] == "unscored" and not (SITE / "img" / "recon" / (mid + ".jpg")).exists():
            m["recreate"].update(status="failed", error="Image generation rejected the prompt.")

    runs = [load(RAW / "speed" / ("%s-%d.json" % (mid, i))) for i in range(3)]
    good = [r for r in runs if r and not r.get("error") and (r.get("usage") or {}).get("completion_tokens")]
    if good:
        tps = [r["usage"]["completion_tokens"] / r["t_total"] for r in good]
        m["speed"] = {"status": "ok", "runs": len(good), "tps": round(statistics.median(tps), 1),
                      "tps_min": round(min(tps), 1), "tps_max": round(max(tps), 1),
                      "ttft": round(statistics.median(r["t_first_content"] for r in good), 2),
                      "seconds": round(statistics.median(r["t_total"] for r in good), 1),
                      "out_tokens": round(statistics.median(r["usage"]["completion_tokens"] for r in good))}
    else:
        e = next((r for r in runs if r), {})
        m["speed"] = {"status": "failed" if e else "not run", "error": "%s: %s" % (e.get("error"), str(e.get("body", ""))[:160])}

    v = load(RAW / "value" / (mid + ".json"))
    if not v:
        m["value"] = {"status": "not run"}
    elif v.get("error"):
        m["value"] = {"status": "failed", "error": "%s: %s" % (v["error"], str(v.get("body", ""))[:160])}
    else:
        g = grade(v["text"])
        d = dict(meta(v), status="ok")
        if g is None:
            d.update(status="failed", error="Answer was not valid JSON.")
        else:
            c = sum(g.values())
            d.update(correct=c, total=len(g), per_q=[g[q] for q in answers],
                     per_1k=round(c / d["out_tokens"] * 1000, 2) if d["out_tokens"] else None,
                     per_dollar=round(c / d["cost"]) if d["cost"] else None)
        m["value"] = d

    for task in ("alpaca", "design", "value", "vision"):
        spend += (load(RAW / task / (mid + ".json")) or {}).get("cost") or 0
    spend += sum((r or {}).get("cost") or 0 for r in runs)
    models.append(m)

data = {"generated": datetime.date.today().isoformat(), "models": models, "judges": JUDGES, "image_model": IMAGE_MODEL,
        "contestant_spend": round(spend, 2), "questions": len(answers),
        "judge_note": "Alpaca cards are scored differently from the other tabs: a small vision model records what is in the four frames, and Jev, a decision model, maps those observations onto the 0-4 rubric. Design and recreation cards were scored by Claude Opus 5.5 and GPT-6 Sol before 2026-11-25, and by Gemini 3.1 Pro and GPT-6 Sol after Claude Opus 5.5 became a contestant.",
        "run_note": "The first ten models ran on 2026-11-16; the seventeen added since ran on 2026-11-25."}
# Two axes of "value": answers per 1,000 output tokens (parsimony) and answers per dollar (price).
# The index is their geometric mean, each axis scaled to the best model, so a model has to be good at both.
scored = [m for m in models if m["value"].get("status") == "ok" and m["value"].get("correct")]
if scored:
    best_t = max(m["value"]["per_1k"] for m in scored)
    best_m = max(m["value"]["per_dollar"] for m in scored)
    for m in scored:
        v = m["value"]
        v["per_correct_cost"] = round(v["cost"] / v["correct"], 6)
        v["index"] = round(100 * ((v["per_1k"] / best_t) * (v["per_dollar"] / best_m)) ** 0.5, 1)
    order = sorted(scored, key=lambda m: -m["value"]["index"])
    for i, m in enumerate(order, 1):
        m["value"]["index_rank"] = i
(SITE / "data.js").write_text("window.BENCH = " + json.dumps(data, indent=1).replace("</", "<\\/") + ";\n")
for m in models:
    print("%-44s alp %-8s des %-8s rec %-9s tps %-6s val %s" % (
        m["id"], m["alpaca"].get("score", m["alpaca"]["status"]), m["design"].get("score", m["design"]["status"]),
        m["recreate"].get("score", m["recreate"]["status"]), m["speed"].get("tps", m["speed"]["status"]),
        "%s/%s %s/1k" % (m["value"].get("correct"), m["value"].get("total"), m["value"].get("per_1k")) if m["value"]["status"] == "ok" else m["value"]["status"]))
print("contestant spend $%.2f" % spend)
