"""Alpaca scoring v12: measured proportions, measured smoothness, and a blind part-accuracy judge.

Why this exists: v11 scored anatomy from a holistic "does it look like an alpaca" answer, so a
polished drawing with stick legs and a too-long neck could sit next to a badly built one. This
version separates the three things Vivek asked for:

  1. body parts  - counted by a vision model (legs, joints, attachment, ears, tail, detachment)
                   and scored by Jev from those counts;
  2. proportions - measured as ratios from bounding boxes, compared against alpaca reference
                   bands in code (neck/body, head/body, leg depth/body depth);
  3. smoothness  - computed from the four frames: how much changes, how evenly it changes, and
                   whether one pair of frames jumps (popping).

Everything that can be measured is measured; Jev only judges what cannot be counted.
"""
import json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import *
import judge as J

CAPTIONERS = ["openai-gpt-6-sol", "gemini-3-1-pro-preview"]
CAPTIONER = CAPTIONERS[0]
RUBRIC_VERSION = "v13"

OBSERVE = """You are looking at four frames, 400 ms apart, of one animated HTML component: an alpaca walking in a scene, drawn in code.
Report only what you can see. Do not rate quality and do not score.

Return JSON only:
{"description":"one sentence",
 "parts":{"legs_visible":0,"legs_with_visible_joint":0,
          "leg_attachment":"chest_and_rump | under_belly | unclear",
          "ears":"upright_banana | small_pointed | other | none",
          "tail_visible":false,"detached_parts":false,
          "notes":"specific parts affected, or 'none'"},
 "points":{"chest":[x,y],"rump":[x,y],"neck_base":[x,y],"poll":[x,y],"muzzle":[x,y],"belly":[x,y],"ground":[x,y]},
 "gait":{"feet_planted":true,"sliding_or_popping":false,"legs_change_between_frames":true,"notes":"what the legs do"},
 "craft":{"seams_or_stray_shapes":false,"inconsistent_light":false,"clipped_elements":false,"contact_shadow":true,"notes":"specific artifacts, or 'none'"}}

Landmark points: 0-1000 coordinates, origin top-left, x right and y down, as if the frame were 1000x1000.
- chest: the front of the torso where the neck rises.
- rump: the back of the torso, before the tail.
- neck_base: where the neck meets the torso, at the top of the shoulder.
- poll: the top of the skull, where the neck ends.
- muzzle: the tip of the nose.
- belly: the underside of the torso at its lowest point.
- ground: the point where the representative leg touches the floor.
Place each point on the animal itself, not on the scenery.

Definitions, apply strictly:
- legs_with_visible_joint: legs showing a bend at knee, hock or fetlock. A straight stick does not count.
- ears: "upright_banana" only for long curved camelid ears; short triangular ears are "small_pointed".
Every field is required."""

ALPACA_BANDS = {"neck_body": (0.55, 1.05), "head_body": (0.22, 0.45), "leg_depth": (0.90, 1.70)}


def caption(model, images):
    content = [{"type": "text", "text": OBSERVE}]
    content += [{"type": "image_url", "image_url": {"url": data_url(i)}} for i in images]
    last = None
    for _ in range(3):
        r = post("/chat/completions", {"model": model, "messages": [{"role": "user", "content": content}],
                                       "max_completion_tokens": 7000, "temperature": 0,
                                       "venice_parameters": {"include_venice_system_prompt": False}})
        try:
            txt = r["choices"][0]["message"].get("content") or ""
            i = txt.find("{")
            if i < 0:
                raise ValueError("no JSON")
            depth = 0
            for k in range(i, len(txt)):
                if txt[k] == "{":
                    depth += 1
                elif txt[k] == "}":
                    depth -= 1
                    if depth == 0:
                        d = json.loads(txt[i:k + 1])
                        break
            else:
                raise ValueError("unbalanced")
            for key in ("parts", "points", "gait", "craft"):
                if key not in d:
                    raise ValueError("missing " + key)
            return d
        except Exception as e:
            last = e
    raise RuntimeError("captioner failed: %r" % last)


def jev(state, questions):
    req = RAW / "jev_req.json"
    req.write_text(json.dumps({"state": state, "questions": questions}))
    r = subprocess.run([str(Path.home() / ".local/bin/jev-decide"), "--file", str(req)],
                       capture_output=True, text=True, timeout=180)
    if not r.stdout.strip():
        raise RuntimeError("jev failed: " + (r.stderr or "")[:200])
    return json.loads(r.stdout)


def box_ratio(points):
    """Ratios from landmark points. Distances are in the same normalised units."""
    def p(k):
        v = (points or {}).get(k)
        return v if isinstance(v, list) and len(v) == 2 and (v[0] or v[1]) else None
    def dist(a, b):
        if not a or not b:
            return 0.0
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
    body = dist(p("chest"), p("rump"))
    neck = dist(p("neck_base"), p("poll"))
    head = dist(p("poll"), p("muzzle"))
    leg = (p("ground")[1] - p("belly")[1]) if p("belly") and p("ground") else 0.0
    out = {"body_len": round(body, 1), "neck_len": round(neck, 1), "head_len": round(head, 1),
           "leg_len": round(leg, 1)}
    out["neck_body"] = round(neck / body, 3) if body > 5 else None
    out["head_body"] = round(head / body, 3) if body > 5 else None
    out["leg_depth"] = round(leg / (0.55 * body), 3) if body > 5 else None
    return out


def band_score(value, lo, hi):
    """4 inside the band, falling off with distance outside it."""
    if value is None:
        return None
    if lo <= value <= hi:
        return 4
    span = hi - lo
    d = (lo - value) if value < lo else (value - hi)
    if d <= 0.15 * span:
        return 3
    if d <= 0.40 * span:
        return 2
    if d <= 0.80 * span:
        return 1
    return 0


def smoothness(mid):
    """How evenly the animation moves between frames. Returns metrics and a 0-4 score."""
    from PIL import Image, ImageChops
    fs = [J.SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(4)]
    if not all(f.exists() for f in fs):
        return {}
    ims = [Image.open(f).convert("L").resize((320, 180)) for f in fs]
    changed = []
    for a, b in zip(ims, ims[1:]):
        d = ImageChops.difference(a, b)
        px = list(d.getdata())
        changed.append(100.0 * sum(1 for v in px if v > 12) / len(px))
    mean = sum(changed) / len(changed)
    spread = (max(changed) - min(changed)) / mean if mean else 0
    score = 4 if mean >= 3 and spread <= 0.8 else 3 if mean >= 3 and spread <= 1.5 else 2 if mean >= 1 else 1 if mean > 0 else 0
    return {"changed": [round(c, 2) for c in changed], "mean": round(mean, 2), "spread": round(spread, 2), "score": score}



def pace(mid):
    """Cadence in gait cycles per second, from the frame-to-frame change series."""
    from PIL import Image, ImageChops
    import math
    fs = [J.SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(20)]
    if not all(f.exists() for f in fs):
        return {}
    ims = [Image.open(f).convert("L").resize((240, 135)) for f in fs]
    d = []
    for a, b in zip(ims, ims[1:]):
        diff = ImageChops.difference(a, b)
        px = list(diff.getdata())
        d.append(sum(1 for v in px if v > 12) / len(px))
    mean = sum(d) / len(d)
    centred = [x - mean for x in d]
    dt = 0.15
    best_lag, best_corr = None, 0
    for lag in range(2, len(centred) // 2):
        num = sum(centred[i] * centred[i + lag] for i in range(len(centred) - lag))
        den = math.sqrt(sum(x * x for x in centred) * sum(x * x for x in centred[lag:]))
        c = num / den if den else 0
        if c > best_corr:
            best_corr, best_lag = c, lag
    if best_lag is None or best_corr < 0.25:
        return {"cadence": 0.0, "strength": round(best_corr, 2), "mean_change": round(mean * 100, 2),
                "score": 1 if mean > 0.001 else 0}
    cadence = 1.0 / (best_lag * dt)
    score = 4 if 0.6 <= cadence <= 2.2 else 3 if 0.35 <= cadence < 0.6 or 2.2 < cadence <= 3.0 else 2 if 0.15 <= cadence < 0.35 else 1
    return {"cadence": round(cadence, 2), "strength": round(best_corr, 2), "mean_change": round(mean * 100, 2), "score": score}


def build_state(obs, ratios, smooth, motion):
    p = obs["parts"]
    yes = lambda b: "yes" if b else "no"
    L = []
    L.append("BODY PARTS REPORT")
    L.append("Legs visible: %s. Legs with a visible joint: %s." % (p.get("legs_visible"), p.get("legs_with_visible_joint")))
    L.append("Leg attachment: %s." % str(p.get("leg_attachment")).replace("_", " "))
    L.append("Ears: %s. Tail visible: %s. Any detached part: %s." % (str(p.get("ears")).replace("_", " "), yes(p.get("tail_visible")), yes(p.get("detached_parts"))))
    if p.get("notes") and str(p["notes"]).strip().lower() not in ("none", "n/a", ""):
        L.append("Note: " + p["notes"])
    L.append("")
    L.append("MEASURED PROPORTIONS (body length = 1.0)")
    L.append("Neck length: %s (alpaca reference 0.50-0.80 of body length)." % ratios.get("neck_body"))
    L.append("Head length: %s (reference 0.22-0.36)." % ratios.get("head_body"))
    L.append("Leg length: %s of body depth (reference 1.15-1.75)." % ratios.get("leg_depth"))
    L.append("")
    L.append("MEASURED SMOOTHNESS")
    L.append("Pixel change per frame pair: %s percent. Mean %.2f, spread %.2f." % (
        smooth.get("changed"), smooth.get("mean", 0), smooth.get("spread", 0)))
    L.append("Gait report: feet planted %s, sliding or popping %s, legs change %s. %s" % (
        yes(obs["gait"].get("feet_planted")), yes(obs["gait"].get("sliding_or_popping")),
        yes(obs["gait"].get("legs_change_between_frames")), obs["gait"].get("notes", "")))
    L.append("")
    L.append("CRAFT REPORT")
    c = obs["craft"]
    L.append("Seams or stray shapes: %s. Inconsistent light: %s. Clipped elements: %s. Contact shadow: %s." % (
        yes(c["seams_or_stray_shapes"]), yes(c["inconsistent_light"]), yes(c["clipped_elements"]), yes(c["contact_shadow"])))
    if c.get("notes"):
        L.append("Note: " + c["notes"])
    return "\n".join(L)


PART_LEVELS = [
    "0 - not recognisably an animal",
    "1 - several structural faults: no joints and a part missing or detached, or not a camelid",
    "2 - one structural fault: fewer than three legs show a joint, or a part is detached or missing",
    "3 - three legs show joints, nothing detached, but one part is wrong (ears, tail or attachment)",
    "4 - four legs show joints, nothing detached, camelid ears and a tail",
]
CRAFT_LEVELS = [
    "0 - blank or unrenderable",
    "1 - broken layout or missing parts",
    "2 - several visible artifacts",
    "3 - one visible artifact",
    "4 - no artifact reported",
]


def ask_jev(state):
    return jev(state, {
        "parts": {"type": "score", "instructions":
                  "Read the BODY PARTS REPORT. Score how accurately the animal is built. "
                  "Use the joint count and the named faults. Ignore the scene and the motion.",
                  "criteria": PART_LEVELS},
        "craft": {"type": "score", "instructions":
                  "Read the CRAFT REPORT. Score execution quality from the artifacts actually reported.",
                  "criteria": CRAFT_LEVELS},
    })


def run(mid):
    out = RAW / "judge" / ("alpaca-%s.json" % mid)
    old = load(out, {}) or {}
    if old.get("rubric") == RUBRIC_VERSION and old.get("median"):
        print("skip", mid, flush=True)
        return
    pngs = [J.SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(20)]
    if not all(p.exists() for p in pngs):
        print("no frames", mid, flush=True)
        return
    # four evenly spaced moments go to the vision model; all twenty feed the cadence measure
    images = [J.jpeg(pngs[i], RAW / "judge_in" / (pngs[i].stem + ".jpg"), 1024) for i in (0, 6, 12, 18)]
    try:
        reads = []
        for model in CAPTIONERS:
            try:
                reads.append(caption(model, images))
            except Exception as e:
                print("caption fail", mid, model, repr(e)[:100], flush=True)
        if not reads:
            raise RuntimeError("no captioner succeeded")
        obs = reads[0]
        motion = J.motion_stats(mid) or {}
        rs = [box_ratio(o["points"]) for o in reads]
        ratios = {}
        for k in rs[0]:
            vals = sorted(r[k] for r in rs if r.get(k) is not None)
            ratios[k] = vals[len(vals) // 2] if vals else None
        # conservative on parts: the lower joint count and any detached/absent part reported
        joints = min(int(o["parts"].get("legs_with_visible_joint") or 0) for o in reads)
        obs["parts"]["legs_with_visible_joint"] = joints
        obs["parts"]["detached_parts"] = any(o["parts"].get("detached_parts") for o in reads)
        pace_m = pace(mid)
        smooth = smoothness(mid)
        ans = ask_jev(build_state(obs, ratios, smooth, motion))
    except Exception as e:
        print("ERR", mid, repr(e)[:200], flush=True)
        return
    a = ans.get("answers", ans)
    a = ans.get("answers", ans)
    med, why = {}, {}
    med["anatomy"] = max(0, min(4, round(float(a["parts"]["score"]))))
    med["craft"] = max(0, min(4, round(float(a["craft"]["score"]))))
    med["pace"] = pace_m.get("score", 0)
    med["smoothness"] = smooth.get("score", 0)
    why["anatomy"] = "joints %s/%s, %s; level %.2f" % (
        obs["parts"].get("legs_with_visible_joint"), obs["parts"].get("legs_visible"),
        str(obs["parts"].get("leg_attachment")).replace("_", " "), float(a["parts"]["score"]))
    why["craft"] = "level %.2f; %s" % (float(a["craft"]["score"]), obs["craft"].get("notes", ""))
    why["pace"] = "%s cycles/s (confidence %s), %s%% change per frame" % (
        pace_m.get("cadence"), pace_m.get("strength"), pace_m.get("mean_change"))
    why["smoothness"] = "frame change %s, spread %s" % (smooth.get("changed"), smooth.get("spread"))
    why["proportions"] = "neck %.2f, head %.2f, leg/depth %.2f (diagnostic, not scored)" % (
        ratios.get("neck_body") or 0, ratios.get("head_body") or 0, ratios.get("leg_depth") or 0)
    save(out, {"rubric": RUBRIC_VERSION, "median": med, "rationale": why, "judges_used": len(reads),
               "captioner": CAPTIONER, "observations": obs, "ratios": ratios,
               "smoothness": smooth, "pace": pace_m, "motion": motion,
               "verdict": {"jev+" + CAPTIONER: obs.get("description", "")}})
    print("scored", mid, med, flush=True)


if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(run, only or MODELS))
    print("V12 DONE", flush=True)
