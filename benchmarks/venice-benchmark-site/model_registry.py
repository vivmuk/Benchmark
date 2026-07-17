"""Canonical BenchmarkViv model roster.

Both scored benchmarks and Arcade imports this module. Keeping a single registry
prevents a model appearing in one public surface but not the other.
"""
MODELS = [
    {"id": "openai-gpt-56-luna",      "display": "GPT-5.6 Luna"},
    {"id": "openai-gpt-56-luna-pro",  "display": "GPT-5.6 Luna Pro"},
    {"id": "openai-gpt-56-sol",       "display": "GPT-5.6 Sol"},
    {"id": "openai-gpt-56-sol-pro",   "display": "GPT-5.6 Sol Pro"},
    {"id": "openai-gpt-56-terra",     "display": "GPT-5.6 Terra"},
    {"id": "openai-gpt-56-terra-pro", "display": "GPT-5.6 Terra Pro"},
    {"id": "openai-gpt-55",           "display": "GPT-5.5"},
    {"id": "claude-fable-5",          "display": "Fable 5"},
    {"id": "claude-opus-4-8",         "display": "Opus 4.8"},
    {"id": "zai-org-glm-5-2",         "display": "GLM 5.2"},
    {"id": "deepseek-v4-pro",         "display": "DeepSeek V4"},
    {"id": "minimax-m3-preview",      "display": "MiniMax M3"},
    {"id": "grok-4-5",                "display": "Grok 4.5"},
    {"id": "kimi-k3",                  "display": "Kimi K3"},
]
