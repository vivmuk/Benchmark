"""Shared helpers for the BenchmarkViv runner."""
import base64, http.client, json, os, re, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "bench" / "raw"
SITE = ROOT / "site"
API = "https://api.venice.ai/api/v1"

# The ten most recently released text models on the Venice API (by `created`), 2026-11-16.
MODELS = [
    "qwen-4-max",
    "gemini-4-hydrogen",
    "glm-5-3-flash-uncensored",
    "gemini-4-carbon",
    "claude-fable-5-2",
    "e2ee-deepseek-v4-1-flash-1017-abliterated",
    "deepseek-v4-1-flash-1017-uncensored",
    "openai-gpt-61-terra",
    "kimi-k3-1-pro",
    "kimi-k3-1-pro-highspeed",
    "inkling-2-mini",
]
ICONS = [("qwen", "qwen-color"), ("gemini", "gemini-color"), ("glm", "zai"), ("claude", "claude-color"),
         ("deepseek", "deepseek-color"), ("openai", "openai"), ("kimi", "kimi-color"),
         ("inkling", "thinkingmachines")]
LABS = {"qwen": "Alibaba", "gemini": "Google", "glm": "Z.ai", "claude": "Anthropic",
        "deepseek": "DeepSeek", "openai": "OpenAI", "kimi": "Moonshot AI",
        "inkling": "Thinking Machines"}
IMAGE_MODEL = "nano-banana-2-1"
JUDGES = ["claude-opus-5-5", "openai-gpt-6-sol"]  # neither is a contestant


def key():
    k = os.environ.get("VENICE_API_KEY")
    if k:
        return k.strip()
    local = Path.home() / ".hermes/secrets/venice_api_key"
    if local.exists():
        return local.read_text().strip()
    env = Path.home() / ".hermes/.env"
    if env.exists():
        m = re.search(r"VENICE_API_KEY=(.+)", env.read_text())
        if m:
            return m.group(1).strip().strip('"')
    cfg = (Path.home() / ".hermes/profiles/pani/config.yaml").read_text()
    return re.search(r"api_key:\s*[\"']?([A-Za-z0-9_\-]+)", cfg).group(1)


def family(mid):
    for k, _ in ICONS:
        if k in mid:
            return k
    return "venice"


def get(path):
    r = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + key()})
    return json.load(urllib.request.urlopen(r, timeout=60))


def post(path, body, timeout=300):
    r = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                               headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(r, timeout=timeout))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:600]}


def stream(model, messages, max_tokens=None, timeout=1500):
    """Streamed chat completion with timing. No temperature (some models lock it)."""
    body = {"model": model, "messages": messages, "stream": True,
            "stream_options": {"include_usage": True},
            "venice_parameters": {"include_venice_system_prompt": False}}
    if max_tokens:
        body["max_completion_tokens"] = max_tokens
    c = http.client.HTTPSConnection("api.venice.ai", timeout=timeout)
    t0 = time.monotonic()
    c.request("POST", "/api/v1/chat/completions", json.dumps(body),
              {"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    r = c.getresponse()
    if r.status != 200:
        return {"error": r.status, "body": r.read().decode()[:600]}
    txt, rea, usage, t_any, t_content, finish = [], [], None, None, None, None
    for line in r:
        line = line.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        d = line[5:].strip()
        if d == "[DONE]":
            break
        try:
            j = json.loads(d)
        except ValueError:
            continue
        if j.get("usage"):
            usage = j["usage"]
        for ch in j.get("choices") or []:
            dl = ch.get("delta") or {}
            if ch.get("finish_reason"):
                finish = ch["finish_reason"]
            rc = dl.get("reasoning_content") or dl.get("reasoning")
            if rc:
                t_any = t_any or time.monotonic() - t0
                rea.append(rc if isinstance(rc, str) else json.dumps(rc))
            if dl.get("content"):
                t_any = t_any or time.monotonic() - t0
                t_content = t_content or time.monotonic() - t0
                txt.append(dl["content"])
    total = time.monotonic() - t0
    return {"text": "".join(txt), "reasoning_chars": len("".join(rea)), "usage": usage, "finish": finish,
            "t_first_delta": t_any, "t_first_content": t_content, "t_total": total}


def cost(usage, pricing):
    if not usage:
        return None
    return (usage.get("prompt_tokens", 0) * pricing["in"] + usage.get("completion_tokens", 0) * pricing["out"]) / 1e6


def extract_html(text):
    m = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.S | re.I)
    if m and "<" in m.group(1):
        return m.group(1).strip()
    m = re.search(r"(<!DOCTYPE.*</html>)", text, re.S | re.I) or re.search(r"(<html.*</html>)", text, re.S | re.I)
    return (m.group(1) if m else text).strip()


def data_url(path):
    mime = "image/png" if str(path).endswith(".png") else "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(Path(path).read_bytes()).decode())


def load(p, default=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else default


def save(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1))


def incomplete(r):
    """Venice closed the stream before the model finished (no finish reason, no usage)."""
    return bool(r) and not r.get("error") and not r.get("finish") and not r.get("usage")
