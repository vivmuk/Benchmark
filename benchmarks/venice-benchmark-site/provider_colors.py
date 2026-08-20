"""Provider → base color for BenchmarkViv. Single source of truth.

Every model inherits its provider's base hue; individual models in a
provider are shaded (lightness/alpha) rather than given arbitrary colors.
Both the Python build scripts (make_model_pages, infographics, SVG) and the
JS (`assets/app.js`) read this mapping so the site never drifts from the
benchmark code.

Light theme: DeepSeek = blue, Claude = orange, GPT = violet, Grok = red,
Gemini = cyan, Qwen = purple, Kimi(monthsun) = amber, MiniMax = rose,
GLM/Z-AI = green, NVIDIA = yellow-green, Mistral = crimson.
"""

PROVIDER_COLORS = {
    # provider_key: (pretty name, base color hex)
    "openai":      ("OpenAI",        "#7C3AED"),  # GPT violet
    "claude":      ("Claude",        "#F97316"),  # orange (user's wish)
    "deepseek":    ("DeepSeek",      "#2563EB"),  # blue (user's wish)
    "gemini":      ("Gemini",        "#06B6D4"),  # cyan
    "grok":        ("Grok",          "#EF4444"),  # red
    "qwen":        ("Qwen",          "#8B5CF6"),  # purple
    "kimi":        ("Kimi/Moonshot", "#F59E0B"),  # amber
    "minimax":     ("MiniMax",       "#EC4899"),  # pink
    "glm":         ("Z-AI / GLM",    "#00C2A8"),  # teal
    "nvidia":      ("NVIDIA",        "#76B900"),  # yellow-green
    "mistral":     ("Mistral",       "#D90429"),  # crimson
    "aion":        ("Aion Labs",     "#F43F5E"),  # rose
    "inkling":     ("Inkling",       "#64748B"),  # slate
    "xiaomi":      ("Xiaomi",        "#FF6900"),  # orange
    "other":       ("Other",         "#64748B"),  # slate
}

def provider_of(model_id: str) -> str:
    mid = (model_id or "").lower()
    if mid.startswith(("openai-", "gpt-")) or "gpt" in mid:
        return "openai"
    if mid.startswith(("claude", "opus", "sonnet", "fable")):
        return "claude"
    if mid.startswith("deepseek"):
        return "deepseek"
    if mid.startswith("gemini"):
        return "gemini"
    if mid.startswith(("grok", "xai")):
        return "grok"
    if mid.startswith(("qwen", "qwen3")):
        return "qwen"
    if mid.startswith("kimi"):
        return "kimi"
    if mid.startswith("minimax"):
        return "minimax"
    if mid.startswith(("glm", "zai", "z-ai", "z-ai")):
        return "glm"
    if "nemotron" in mid or mid.startswith("nvidia"):
        return "nvidia"
    if "mistral" in mid:
        return "mistral"
    if mid.startswith("aion"):
        return "aion"
    if mid.startswith(("inkling",)):
        return "inkling"
    if mid.startswith("xiaomi"):
        return "xiaomi"
    return "other"

def provider_color(model_id: str) -> str:
    return PROVIDER_COLORS[provider_of(model_id)][1]

def provider_name(model_id: str) -> str:
    return PROVIDER_COLORS[provider_of(model_id)][0]

def color_for_model(model_id: str, alpha: float = 1.0) -> str:
    """Return hex color (or rgba if alpha < 1)."""
    hexc = provider_color(model_id)
    if alpha >= 1.0:
        return hexc
    r = int(hexc[1:3], 16); g = int(hexc[3:5], 16); b = int(hexc[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"