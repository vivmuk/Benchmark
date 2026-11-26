"""Alpaca scoring v6: a cheap vision model records observations, Jev turns them into calibrated scores.

The division of labour is the point:
  - the captioner answers only factual questions about what is in the four frames;
  - Jev (a decision model) maps those facts onto the 0-4 rubric with probabilities;
  - code owns the two things neither should judge: the measured gait band and brief compliance.
One captioner call plus one Jev call per model costs about $0.0002.
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import *
import judge as J

CAPTIONER = "openai-gpt-6-luna"
RUBRIC_VERSION = "v9"
LEVELS = [
    "0 - failing: the aspect is absent or the output is broken",
    "1 - poor: present but badly wrong",
    "2 - weak: recognisable but with a clear structural flaw",
    "3 - good: correct with a minor flaw",
    "4 - excellent: nothing you would fix",
]

OBSERVE = """You are looking at four frames, 400 ms apart, of one animated HTML component: an alpaca walking in a small scene, drawn in code.
Answer only what you can see. Do not rate quality, do not score anything, do not guess. Report facts as JSON:

{"description":"one sentence on what is on screen",
 "anatomy":{"detached_parts":false,"jointless_legs":false,"wrong_proportions":false,"missing_cues":false,
            "notes":"name the specific parts affected, or 'none'"},
 "gait":{"feet_planted":true,"sliding_or_popping":false,"legs_change_between_frames":true,"notes":"what the legs do"},
 "scene":{"depth_planes":1,"elements":["list every distinct thing in the setting, e.g. sky, ground, sun, clouds, hills, trees, flowers, rocks, buildings; do not list the alpaca"],"palette":"one clause","placement":"where the animal sits in the frame","clutter":false},
 "craft":{"seams_or_stray_shapes":false,"inconsistent_light":false,"clipped_elements":false,"contact_shadow":true,
          "notes":"specific artifacts, or 'none'"}}

depth_planes is an integer 1-3: 1 = a single flat fill, 2 = sky and ground (or equivalent), 3 = distinct foreground, middle and background. List scene elements literally, one per item.
Every field is required. Reply with the JSON object only."""


def caption(images):
    import re
    content = [{"type": "text", "text": OBSERVE}]
    content += [{"type": "image_url", "image_url": {"url": data_url(i)}} for i in images]
    last = None
    for _ in range(3):
        r = post("/chat/completions", {"model": CAPTIONER, "messages": [{"role": "user", "content": content}],
                                       "max_completion_tokens": 2000, "temperature": 0,
                                       "venice_parameters": {"include_venice_system_prompt": False}})
        try:
            txt = r["choices"][0]["message"].get("content") or ""
            i = txt.find("{")
            if i < 0:
                raise ValueError("no JSON in reply: %r" % txt[:120])
            depth = 0
            for j2 in range(i, len(txt)):
                if txt[j2] == "{":
                    depth += 1
                elif txt[j2] == "}":
                    depth -= 1
                    if depth == 0:
                        d = json.loads(txt[i:j2 + 1])
                        break
            else:
                raise ValueError("unbalanced JSON")
            for k in ("description", "anatomy", "gait", "scene", "craft"):
                if k not in d:
                    raise ValueError("missing " + k)
            return d
        except Exception as e:
            last = e
    raise RuntimeError("captioner failed: %r" % last)


def jev(state, questions):
    req = Path(RAW / "jev_req.json")
    req.write_text(json.dumps({"state": state, "questions": questions}, indent=1))
    r = subprocess.run([str(Path.home() / ".local/bin/jev-decide"), "--file", str(req)],
                       capture_output=True, text=True, timeout=180)
    if not r.stdout.strip():
        raise RuntimeError("jev failed: " + (r.stderr or "")[:200])
    return json.loads(r.stdout)


def build_state(obs, motion):
    a, g, s, c = obs["anatomy"], obs["gait"], obs["scene"], obs["craft"]
    yes = lambda b: "yes" if b else "no"
    lines = []
    lines.append("ANATOMY REPORT")
    lines.append("All parts attached: %s." % yes(not a["detached_parts"]))
    lines.append("Legs have joints: %s." % yes(not a["jointless_legs"]))
    lines.append("Proportions right for a camelid: %s." % yes(not a["wrong_proportions"]))
    lines.append("Species cues present (upright ears, muzzle, fleece): %s." % yes(not a["missing_cues"]))
    if a.get("notes") and a["notes"].strip().lower() not in ("none", "n/a", ""):
        lines.append("Captioner note on anatomy: " + a["notes"])
    lines.append("")
    lines.append("GAIT REPORT")
    lines.append("Legs change between frames: %s." % yes(g["legs_change_between_frames"]))
    lines.append("Feet stay planted: %s." % yes(g["feet_planted"]))
    lines.append("Any sliding or popping: %s." % yes(g["sliding_or_popping"]))
    if g.get("notes"):
        lines.append("Captioner note on gait: " + g["notes"])
    lines.append("")
    lines.append("SCENE REPORT")
    lines.append("Distinct depth planes: %d (1 = flat fill, 2 = sky and ground, 3 = foreground, middle, background)." % int(s.get("depth_planes") or 1))
    lines.append("Palette: %s." % s.get("palette", ""))
    lines.append("Placement: %s." % s.get("placement", ""))
    lines.append("Clutter competing with the subject: %s." % yes(s.get("clutter")))
    lines.append("")
    lines.append("CRAFT REPORT")
    lines.append("Seams or stray shapes: %s." % yes(c["seams_or_stray_shapes"]))
    lines.append("Light direction inconsistent: %s." % yes(c["inconsistent_light"]))
    lines.append("Elements clipped by the frame: %s." % yes(c["clipped_elements"]))
    lines.append("Contact shadow under the animal: %s." % yes(c["contact_shadow"]))
    if c.get("notes") and c["notes"].strip().lower() not in ("none", "n/a", ""):
        lines.append("Captioner note on craft: " + c["notes"])
    lines.append("")
    lines.append("MEASURED MOTION: %.2f%% of all pixels changed between consecutive frames, %.2f%% in the leg band." % (
        motion.get("changed_pct", 0), motion.get("leg_pct", 0)))
    lines.append("")
    lines.append("Description of the frames: " + obs.get("description", ""))
    return "\n".join(lines)


ANATOMY_LEVELS = [
    "0 - not recognisably an animal",
    "1 - several structural faults: detached parts, missing legs, or no camelid shape",
    "2 - one structural fault, or two cosmetic faults",
    "3 - one cosmetic fault only",
    "4 - no fault reported in the anatomy report",
]
SCENE_LEVELS = [
    "0 - no scene at all",
    "1 - accidental or cluttered",
    "2 - a basic backdrop with one depth plane",
    "3 - two or three depth planes with a coherent palette",
    "4 - three depth planes, a considered palette and deliberate placement",
]
CRAFT_LEVELS = [
    "0 - blank or unrenderable",
    "1 - broken layout or missing parts",
    "2 - several visible artifacts",
    "3 - one visible artifact",
    "4 - no artifact reported in the craft report",
]


def ask_jev(state):
    q = {
        "anatomy": {"type": "score", "instructions":
                    "Read only the ANATOMY REPORT and the captioner note. How good is the animal's anatomy? "
                    "Pick the level that matches the faults actually reported. Ignore the scene and the motion.",
                    "criteria": ANATOMY_LEVELS},
        "craft": {"type": "score", "instructions":
                  "Read only the CRAFT REPORT. How clean is the execution? "
                  "Count the artifacts actually reported: seams, inconsistent light, clipping, missing shadow.",
                  "criteria": CRAFT_LEVELS},
        "feet": {"type": "noul", "instructions":
                 "According to the GAIT REPORT, do the hooves stay planted and does the leg cycle stay coherent across the frames?",
                 "criteria": {"true": "feet planted and cycle coherent, no sliding or popping reported",
                              "false": "sliding, popping, or no planted foot reported"}},
    }
    return jev(state, q)


def run(mid):
    out = RAW / "judge" / ("alpaca-%s.json" % mid)
    old = load(out, {}) or {}
    if old.get("rubric") == RUBRIC_VERSION and old.get("median"):
        print("skip", mid, flush=True)
        return
    pngs = [J.SHOTS / ("alpaca-%s-%d.png" % (mid, i)) for i in range(4)]
    if not all(p.exists() for p in pngs):
        print("no frames", mid, flush=True)
        return
    images = [J.jpeg(p, RAW / "judge_in" / (p.stem + ".jpg"), 1024) for p in pngs]
    try:
        obs = caption(images)
        motion = J.motion_stats(mid) or {}
        ans = ask_jev(build_state(obs, motion))
    except Exception as e:
        print("ERR", mid, repr(e)[:200], flush=True)
        return
    a = ans.get("answers", ans)
    med, rationale, probs = {}, {}, {}
    for k in ("anatomy", "craft"):
        v = a[k]
        raw = float(v["score"])
        med[k] = max(0, min(4, round(raw)))
        probs[k] = v.get("probabilities")
        rationale[k] = "%s (level %.2f of 4)" % (obs.get(k if k != "anatomy" else "anatomy", {}).get("notes", ""), raw)
    setting = obs.get("scene", {})
    rationale["setting"] = "%s. Palette: %s. Placement: %s." % (
        ", ".join(str(e) for e in (setting.get("elements") or [])) or "nothing beyond the animal",
        setting.get("palette", ""), setting.get("placement", ""))
    band = 4 if motion.get("changed_pct", 0) >= 6 else 3 if motion.get("changed_pct", 0) >= 3 else 2 if motion.get("changed_pct", 0) >= 1 else 1 if motion.get("changed_pct", 0) > 0 else 0
    planted = float((a.get("feet") or {}).get("noul", 0))
    med["gait"] = max(0, band - (0 if planted >= 0.5 else 1))
    rationale["gait"] = "band %d from %.2f%% pixel change; P(planted, coherent)=%.2f" % (
        band, motion.get("changed_pct", 0), planted)
    save(out, {"rubric": RUBRIC_VERSION, "median": med, "judges_used": 1, "setting": setting,
               "captioner": CAPTIONER, "observations": obs, "motion": motion,
               "rationale": rationale, "probabilities": probs,
               "verdict": {("jev+" + CAPTIONER): obs.get("description", "")}})
    print("scored", mid, med, flush=True)


if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    models = only or MODELS
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(run, models))
    print("JEV SCORING DONE", flush=True)
