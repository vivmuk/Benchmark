"""Pairwise alpaca ranking: one comparison per call, Bradley-Terry over the votes.

Why: absolute 0-4 scores from a vision model flip between runs, and a single flipped
criterion moves a model 11 points. A comparison asks only "which of these two is better",
which is a far easier question to answer consistently.

Two voters per pair:
  - a vision judge that sees both stills side by side (anatomy and craft);
  - Jev, which compares the two structured fact sheets and picks a winner on each axis.
Measured cadence and smoothness are not voted on; they are reported and used as diagnostics.
"""
import json, math, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw
from common import *

VISION_JUDGE = "openai-gpt-6-sol"
PAIRS_PER_MODEL = 10
SEED = 20261126
OUT = RAW / "pairwise.json"
PAIRDIR = RAW / "pairs"

ASK = """Two still frames from two different animated alpaca components, labelled A and B.
Answer two comparisons:
1. anatomy: which one has the more accurate alpaca anatomy - legs with visible joints, legs attached at chest and rump, a proportionate neck and head, a tail, nothing detached?
2. craft: which is better drawn - cleaner vector construction, consistent lighting, no seams, stray shapes or clipped elements?

Compare only what you can see. If they are genuinely equal, answer "tie" for that axis.
Return JSON only: {"anatomy":"A|B|tie","craft":"A|B|tie","note":"one sentence on the decisive difference"}"""


def facts(mid):
    j = load(RAW / "judge" / ("alpaca-%s.json" % mid), {}) or {}
    o = j.get("observations") or {}
    p = o.get("parts") or {}
    c = o.get("craft") or {}
    return {"joints": p.get("legs_with_visible_joint"), "legs": p.get("legs_visible"),
            "attach": str(p.get("leg_attachment", "?")).replace("_", " "),
            "ears": str(p.get("ears", "?")).replace("_", " "),
            "tail": p.get("tail_visible"), "detached": p.get("detached_parts"),
            "seams": c.get("seams_or_stray_shapes"), "light": c.get("inconsistent_light"),
            "clipped": c.get("clipped_elements"), "shadow": c.get("contact_shadow"),
            "craft_note": c.get("notes", ""), "anat_note": p.get("notes", "")}


def jev(state, questions):
    req = RAW / "jev_pair_req.json"
    req.write_text(json.dumps({"state": state, "questions": questions}))
    r = subprocess.run([str(Path.home() / ".local/bin/jev-decide"), "--file", str(req)],
                       capture_output=True, text=True, timeout=120)
    if not r.stdout.strip():
        raise RuntimeError("jev failed: " + (r.stderr or "")[:160])
    return json.loads(r.stdout)


def jev_vote(a, b, fa, fb):
    """Two comparative choices over the two fact sheets; Jev reads comparisons far better than absolutes."""
    state = (
        "MODEL A: %s of %s legs show a visible joint; legs attach %s; ears %s; tail %s; detached parts %s. "
        "Craft: seams %s, inconsistent light %s, clipped %s, contact shadow %s. Notes: %s %s\n"
        "MODEL B: %s of %s legs show a visible joint; legs attach %s; ears %s; tail %s; detached parts %s. "
        "Craft: seams %s, inconsistent light %s, clipped %s, contact shadow %s. Notes: %s %s"
    ) % (fa["joints"], fa["legs"], fa["attach"], fa["ears"], fa["tail"], fa["detached"],
         fa["seams"], fa["light"], fa["clipped"], fa["shadow"], fa["anat_note"], fa["craft_note"],
         fb["joints"], fb["legs"], fb["attach"], fb["ears"], fb["tail"], fb["detached"],
         fb["seams"], fb["light"], fb["clipped"], fb["shadow"], fb["anat_note"], fb["craft_note"])
    q = {"anatomy": {"type": "choice", "instructions":
                     "Which model has the more accurate alpaca anatomy - more legs with visible joints, legs attached at chest and rump, a tail, nothing detached? Answer A or B.",
                     "criteria": {"A": "model A", "B": "model B"}},
         "craft": {"type": "choice", "instructions":
                   "Which model is more cleanly drawn - fewer seams, stray shapes, clipped elements; consistent light? Answer A or B.",
                   "criteria": {"A": "model A", "B": "model B"}}}
    out = jev(state, q)
    ans = out.get("answers") or out
    res = {}
    for k in ("anatomy", "craft"):
        pr = (ans.get(k) or {}).get("probabilities") or {}
        pa, pb = float(pr.get("A", 0)), float(pr.get("B", 0))
        res[k] = "A" if pa > pb + 0.08 else "B" if pb > pa + 0.08 else "tie"
        res[k + "_p"] = [round(pa, 2), round(pb, 2)]
    return res


def composite(a, b):
    PAIRDIR.mkdir(parents=True, exist_ok=True)
    p = PAIRDIR / ("%s__%s.jpg" % (a, b))
    if p.exists():
        return p
    ims = []
    for mid, label in ((a, "A"), (b, "B")):
        im = Image.open(SITE / "img" / "alpaca" / (mid + ".jpg")).convert("RGB")
        im.thumbnail((760, 428))
        canvas = Image.new("RGB", (800, 480), "white")
        canvas.paste(im, ((800 - im.width) // 2, 40))
        d = ImageDraw.Draw(canvas)
        d.text((16, 12), label, fill="black")
        ims.append(canvas)
    out = Image.new("RGB", (1620, 480), "white")
    out.paste(ims[0], (0, 0))
    out.paste(ims[1], (820, 0))
    out.save(p, quality=88)
    return p


def vision_vote(a, b, img):
    content = [{"type": "text", "text": ASK},
               {"type": "image_url", "image_url": {"url": data_url(img)}}]
    r = post("/chat/completions", {"model": VISION_JUDGE, "messages": [{"role": "user", "content": content}],
                                   "max_completion_tokens": 4000, "temperature": 0,
                                   "venice_parameters": {"include_venice_system_prompt": False}})
    txt = r["choices"][0]["message"].get("content") or ""
    i, depth = txt.find("{"), 0
    for k in range(i, len(txt)):
        if txt[k] == "{":
            depth += 1
        elif txt[k] == "}":
            depth -= 1
            if depth == 0:
                d = json.loads(txt[i:k + 1])
                return {"anatomy": d.get("anatomy", "tie"), "craft": d.get("craft", "tie"),
                        "note": str(d.get("note", ""))[:200]}
    raise ValueError("bad judge reply")


def one_pair(pair):
    a, b = pair
    out = {"a": a, "b": b}
    try:
        out["vision"] = vision_vote(a, b, composite(a, b))
    except Exception as e:
        out["vision"] = {"error": repr(e)[:150]}
    try:
        out["jev"] = jev_vote(a, b, facts(a), facts(b))
    except Exception as e:
        out["jev"] = {"error": repr(e)[:150]}
    print("pair", a[:18], b[:18], out.get("vision"), out.get("jev"), flush=True)
    return out


def fit_bradley_terry(votes, ids, iters=600):
    """MM algorithm for Bradley-Terry with ties counted as half wins."""
    theta = {i: 0.0 for i in ids}
    w = {i: 0.0 for i in ids}
    n = {}
    for i in ids:
        w[i] = 0.5  # weak prior so an unbeaten or winless model still has a finite rating
    for a, b, v in votes:
        w[a] += v
        w[b] += 1.0 - v
        n[(a, b)] = n.get((a, b), 0) + 1
        n[(b, a)] = n.get((b, a), 0) + 1
    for _ in range(iters):
        new = {}
        for i in ids:
            denom = 0.0
            for j in ids:
                if j != i and n.get((i, j)):
                    denom += n[(i, j)] / (math.exp(theta[i]) + math.exp(theta[j]))
            new[i] = math.log(max(w[i], 1e-6)) - math.log(max(denom, 1e-9))
        m = sum(new.values()) / len(new)
        theta = {i: v - m for i, v in new.items()}
    return theta


def main():
    ids = [m for m in MODELS if (RAW / "judge" / ("alpaca-%s.json" % m)).exists()]
    random.seed(SEED)
    pairs = set()
    for m in ids:
        others = [x for x in ids if x != m]
        for o in random.sample(others, min(PAIRS_PER_MODEL, len(others))):
            pairs.add(tuple(sorted((m, o))))
    pairs = sorted(pairs)
    done = load(OUT, {}) or {}
    results = done.get("pairs", {})
    todo = [p for p in pairs if "%s|%s" % p not in results]
    print("models", len(ids), "pairs", len(pairs), "todo", len(todo), flush=True)
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(one_pair, todo):
            results["%s|%s" % (r["a"], r["b"])] = r
            save(OUT, {"pairs": results})
    # votes: vision weighs 2, jev weighs 1; ties are half a win for each
    votes = []
    for key, r in results.items():
        a, b = key.split("|")
        for axis in ("anatomy", "craft"):
            v = (r.get("vision") or {}).get(axis)
            if v == "A":
                votes.append((a, b, 2.0))
            elif v == "B":
                votes.append((a, b, 0.0))
            elif v == "tie":
                votes.append((a, b, 1.0))
        jv = r.get("jev") or {}
        for axis in ("anatomy", "craft"):
            v = jv.get(axis)
            if v == "A":
                votes.append((a, b, 1.0))
            elif v == "B":
                votes.append((a, b, 0.0))
            elif v == "tie":
                votes.append((a, b, 0.5))
    rec = {i: [0, 0, 0] for i in ids}
    for key, r in results.items():
        a, b = key.split("|")
        for axis in ("anatomy", "craft"):
            v = (r.get("vision") or {}).get(axis)
            if v == "A":
                rec[a][0] += 1; rec[b][1] += 1
            elif v == "B":
                rec[b][0] += 1; rec[a][1] += 1
            elif v == "tie":
                rec[a][2] += 1; rec[b][2] += 1
    theta = fit_bradley_terry(votes, ids)
    # score = expected win rate against a randomly chosen opponent (0-100)
    # smoothed win rate over the comparisons actually played (Laplace),
    # with the Bradley-Terry strength kept in the file as the opponent-adjusted check
    scores = {}
    for i in ids:
        w, l = rec[i][0], rec[i][1]
        scores[i] = round(100 * (w + 1) / (w + l + 2), 1)
    save(OUT, {"pairs": results, "theta": theta, "scores": scores, "record": rec,
               "method": "bradley-terry over vision (2) + jev (1) votes"})
    for i, s in sorted(scores.items(), key=lambda kv: -kv[1]):
        print("%5.1f %-40s %s" % (s, i, rec[i]), flush=True)
    print("PAIRWISE DONE", flush=True)


if __name__ == "__main__":
    if "--jev-only" in sys.argv:
        refresh_jev()
    else:
        main()
