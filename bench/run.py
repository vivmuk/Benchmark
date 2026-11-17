"""Phase 1: every model call. Resumable: each result is one JSON file in bench/raw/<task>/<model>.json."""
import base64, sys, time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from common import *

ALPACA = """Create one single self-contained HTML file (inline CSS and JS only; no external assets, fonts, libraries or network requests) that shows one beautiful animated component: an alpaca walking.

Requirements:
- Draw the alpaca in code (SVG, CSS or canvas). It must be clearly recognisable as an alpaca: long neck, fluffy fleece, small head with upright ears, four legs.
- It walks in a smooth, continuous, believable loop: the legs must actually move in a walking gait, with some body motion.
- Place it in a small, tasteful scene.
- It must fill a 1280x720 viewport with no scrollbars and start animating on load with no interaction.
- Make it as beautiful as you can.

Return only the HTML, in one ```html code block."""

DESIGN = """Design and build one single self-contained HTML landing page (inline CSS and JS only; no external assets, fonts, images, libraries or network requests) for "Dune Line", a fictional overnight train that crosses a desert to a neon city.

It must include: a navigation bar, a hero section, three feature highlights, a timetable with four departures, pricing with three tiers, one testimonial, and a footer.

It must be responsive and look excellent at 1280px wide. Show your best front-end design taste: typography, spacing, colour, hierarchy and detail. Any illustration must be drawn in code (SVG/CSS).

Return only the HTML, in one ```html code block."""

VISION = """Study the attached image closely. Write a text-to-image prompt that would make an image model recreate this image as exactly as possible: every subject, its position in the frame, counts, colours, any visible text, lighting, sky, style and composition.

Return only the prompt text, nothing else, in at most 250 words."""

SPEED = "Write a plain-prose explanation, about 500 words long, of how a suspension bridge carries load from the deck to the ground. No headings, no lists, no preamble."

VALUE_Q = [
    ("q1", "What is the sum of all prime numbers below 200?"),
    ("q2", "How many trailing zeros does 250! (250 factorial) have?"),
    ("q3", "What day of the week is 29 February 2032? (English day name)"),
    ("q4", "What is 3^200 mod 1000?"),
    ("q5", "How many distinct arrangements are there of the letters in ALPACALLAMA?"),
    ("q6", "What is the least common multiple of the integers 1 through 20?"),
    ("q7", "$12,000 is invested at 7% interest compounded annually for 9 years. What is the final balance, rounded to the nearest dollar? (integer)"),
    ("q8", "How many integers from 1 to 1000 inclusive are divisible by none of 3, 5 and 7?"),
    ("q9", "What is the 30th Fibonacci number, with F1 = F2 = 1?"),
    ("q10", "What is decimal 48879 in hexadecimal? (uppercase, no prefix)"),
    ("q11", "How many times does the letter r appear in the phrase 'strawberry raspberry cranberry'?"),
    ("q12", "How many squares of all sizes are there on a standard 8x8 chessboard?"),
]
VALUE = ("Answer these 12 questions. Reply with one JSON object only, mapping each id to its answer, "
         "for example {\"q1\": 123, \"q3\": \"Monday\"}. No explanation outside the JSON.\n\n"
         + "\n".join("%s. %s" % q for q in VALUE_Q))


def specs():
    out = {}
    for x in get("/models?type=text")["data"]:
        if x["id"] in MODELS:
            s = x["model_spec"]
            out[x["id"]] = {"id": x["id"], "name": s["name"], "created": x["created"],
                            "in": s["pricing"]["input"]["usd"], "out": s["pricing"]["output"]["usd"],
                            "max_out": s["maxCompletionTokens"], "context": x.get("context_length"),
                            "vision": s["capabilities"]["supportsVision"],
                            "reasoning": s["capabilities"]["supportsReasoning"],
                            "family": family(x["id"]), "lab": LABS.get(family(x["id"]), "Venice")}
    return out


def call(task, sp, messages, suffix=""):
    p = RAW / task / (sp["id"] + suffix + ".json")
    old = load(p)
    if old and not old.get("error"):
        return old
    r = {"error": "not run"}
    for attempt in range(2):
        try:
            # Standing rule: every model gets its full allowed output budget.
            r = stream(sp["id"], messages, max_tokens=sp["max_out"])
        except Exception as e:  # network / timeout
            r = {"error": "exception", "body": repr(e)[:300]}
        if not r.get("error") and r.get("text"):
            break
        if not r.get("error"):
            r = {"error": "empty", "body": "no content returned", "usage": r.get("usage"), "finish": r.get("finish")}
        time.sleep(5)
    r["cost"] = cost(r.get("usage"), sp)
    save(p, r)
    print(task + suffix, sp["id"], "ERR %s" % r.get("body", "")[:120] if r.get("error") else "ok %.0fs" % r["t_total"], flush=True)
    return r


def source_jpeg():
    from PIL import Image
    out = SITE / "img" / "source.jpg"
    if not out.exists():
        im = Image.open(RAW / "source.png").convert("RGB")
        im.thumbnail((1280, 1280))
        im.save(out, quality=88)
    return out


def recon(sp, prompt):
    out = SITE / "img" / "recon" / (sp["id"] + ".jpg")
    if out.exists():
        return True
    from PIL import Image
    for _ in range(2):
        d = post("/image/generate", {"model": IMAGE_MODEL, "prompt": prompt[:4000], "aspect_ratio": "16:9",
                                     "resolution": "1K", "format": "png", "safe_mode": False,
                                     "hide_watermark": True, "return_binary": False})
        if d.get("images"):
            im = Image.open(BytesIO(base64.b64decode(d["images"][0]))).convert("RGB")
            im.thumbnail((1280, 1280))
            im.save(out, quality=88)
            return True
        print("recon fail", sp["id"], str(d)[:200], flush=True)
    return False


def run_model(sp):
    u = lambda t: [{"role": "user", "content": t}]
    call("alpaca", sp, u(ALPACA))
    call("design", sp, u(DESIGN))
    call("value", sp, u(VALUE))
    for i in range(3):  # sequential, so the three speed runs do not compete with each other
        call("speed", sp, u(SPEED), suffix="-%d" % i)
    if sp["vision"]:
        v = call("vision", sp, [{"role": "user", "content": [
            {"type": "text", "text": VISION},
            {"type": "image_url", "image_url": {"url": data_url(source_jpeg())}}]}])
        if not v.get("error"):
            recon(sp, v["text"].strip())


if __name__ == "__main__":
    sp = specs()
    save(RAW / "specs.json", sp)
    assert len(sp) == len(MODELS), set(MODELS) - set(sp)
    source_jpeg()
    only = sys.argv[1:]
    todo = [sp[m] for m in MODELS if not only or m in only]
    with ThreadPoolExecutor(5) as ex:
        list(ex.map(run_model, todo))
    print("PHASE1 DONE", flush=True)
