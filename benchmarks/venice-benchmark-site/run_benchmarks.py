#!/usr/bin/env python3
"""
BenchmarkViv - practical benchmark runner for the Venice API.

Usage:
    python run_benchmarks.py            # dry-run (default, no API calls)
    python run_benchmarks.py --dry-run  # explicit dry-run
    python run_benchmarks.py --run-real # real API calls (needs VENICE_INFERENCE_KEY)
"""

from __future__ import annotations                                    # enables PEP 604 union (str|None) on Py <= 3.9
import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: the 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL = "https://api.venice.ai/api/v1/chat/completions"
MODELS_URL = "https://api.venice.ai/api/v1/models"
API_KEY_ENV = "VENICE_INFERENCE_KEY"

RESULTS_PATH = Path("data") / "results.json"

# No artificial cap. Reasoning-heavy models routinely produce longer answers; the
# benchmark measures "cost to deliver value", which requires we let them actually
# deliver. Pass --max-tokens on the CLI to lower this if a particular model is
# spamming (or to enforce a fairness budget for an apples-to-apples run).
MAX_TOKENS = 32768
TEMPERATURE = 0.5
RATE_LIMIT_SLEEP_SECONDS = 1.0
# Reasoning models on long-context prompts can take several minutes. The 180 s
# reading timeout used to be the bottleneck for kimi-k3 / opus benchmarks.
REQUEST_TIMEOUT_SECONDS = 600

from model_registry import MODELS


# Optional per-model benchmark allowlists. Empty = all models run all tracks
# for apples-to-apples comparison.
MODEL_BENCHMARK_LIMITS = {}

# Approximate fallback pricing (USD per 1M tokens: input, output).
# Used if the /models endpoint does not return pricing.
FALLBACK_PRICING = {
    "openai-gpt-56-luna":      {"input": 1.25,  "output": 7.5},
    "openai-gpt-56-luna-pro":  {"input": 1.25,  "output": 7.5},
    "openai-gpt-56-sol":       {"input": 6.25,  "output": 37.5},
    "openai-gpt-56-sol-pro":   {"input": 6.25,  "output": 37.5},
    "openai-gpt-56-terra":     {"input": 3.125, "output": 18.75},
    "openai-gpt-56-terra-pro": {"input": 3.125, "output": 18.75},
    "openai-gpt-55":           {"input": 10.00, "output": 30.00},
    "claude-fable-5":          {"input": 8.00,  "output": 24.00},
    "claude-opus-4-8":         {"input": 15.00, "output": 75.00},
    "zai-org-glm-5-2":         {"input": 1.00,  "output": 3.00},
    "deepseek-v4-pro":         {"input": 0.60,  "output": 2.20},
    "deepseek-v4-flash-0731": {"input": 0.175, "output": 0.35},
    "deepseek-v4-flash-0731-fast": {"input": 0.35, "output": 0.70},
    "minimax-m3-preview":      {"input": 0.40,  "output": 1.60},
    "grok-4-5":                {"input": 2.27,  "output": 6.80},
    # Live Venice /models pricing supersedes this conservative fallback.
    "kimi-k3":                 {"input": 1.00,  "output": 3.00},
    "qwen-3-8-max":            {"input": 2.50,  "output": 7.50},
    "qwen-3-8-2-4t-a95b":      {"input": 2.50,  "output": 7.50},
    "claude-sonnet-5":         {"input": 3.00,  "output": 15.00},
    "gemini-3-6-flash":        {"input": 1.875, "output": 9.375},
    "grok-4-6":                {"input": 2.27,  "output": 6.80},
    "nvidia-nemotron-3-5-lightning-30b-a3b": {"input": 0.10, "output": 0.25},
    # ---- Phase 2: new models ----
    "gemini-3-7-flash":              {"input": 1.875, "output": 9.375},
    "qwen-3-7-max":                  {"input": 2.50,  "output": 7.50},
    "qwen-3-7-plus":                 {"input": 2.50,  "output": 7.50},
    "grok-4-20":                     {"input": 5.00,  "output": 15.00},
    "claude-opus-5-fast":            {"input": 12.00, "output": 60.00},
    "claude-opus-4-8-fast":          {"input": 12.00, "output": 60.00},
    "deepseek-v4-flash":             {"input": 0.15,  "output": 0.30},
    "aion-labs-aion-3-0":            {"input": 2.00,  "output": 6.00},
    "aion-labs-aion-3-0-mini":       {"input": 0.50,  "output": 1.50},
    "nvidia-nemotron-3-super-120b-a12b": {"input": 0.50, "output": 1.50},
    "qwen3-235b-a22b-thinking-2507": {"input": 3.00,  "output": 9.00},
    "minimax-m27":                   {"input": 0.50,  "output": 2.00},
}
DEFAULT_PRICING = {"input": 5.00, "output": 15.00}

BENCHMARKS = [
    {
        "id": "intent_understanding",
        "name": "Intent Understanding",
        "prompt": (
            "I need something built for my team but I'm not sure what. We are "
            "overwhelmed by Slack notifications and duplicate work. Suggest a "
            "solution and ask clarifying questions before assuming details."
        ),
        "scoring": "manual: clarifying questions (0-40), structured proposal (0-30), avoids hallucination (0-30)",
    },
    {
        "id": "one_shot_ui",
        "name": "One-Shot UI Generation",
        "prompt": (
            "Generate a single self-contained HTML file for a dark-mode dashboard "
            "card showing a user's daily focus score, weekly trend sparkline, and "
            "a 'Start Focus' button. Use only HTML/CSS/JS. No external images."
        ),
        "scoring": "heuristic placeholder 70-95; real scoring is manual/LLM-judge",
    },
    # --- Pharma domain benchmarks (future/unregistered) ---
    {
        "id": "pharma_drug_interaction",
        "name": "Pharma: Drug-Drug Interaction Identification",
        "prompt": (
            "You are a clinical pharmacist reviewing a patient's medication list. "
            "For each pair of medications below, identify any clinically significant "
            "drug-drug interactions. For each interaction found, provide:\n\n"
            "1. The interacting drug pair\n"
            "2. Severity classification (Major / Moderate / Minor)\n"
            "3. The pharmacological mechanism (e.g., CYP enzyme inhibition/induction, "
            "pharmacodynamic synergy)\n"
            "4. Recommended clinical action\n\n"
            "Patient medication list:\n"
            "- warfarin 5 mg once daily (atrial fibrillation)\n"
            "- ibuprofen 400 mg three times daily as needed (osteoarthritis pain)\n"
            "- lisinopril 10 mg once daily (hypertension)\n\n"
            "Be precise about mechanisms. If you are uncertain about an interaction, "
            "state that explicitly rather than guessing."
        ),
        "scoring": "heuristic: interaction detection (0-35), severity classification (0-20), mechanism accuracy (0-25), clinical action (0-10), avoids hallucination (0-10); total 100",
    },
    {
        "id": "pharma_regulatory_comprehension",
        "name": "Pharma: Regulatory Guideline Comprehension",
        "prompt": (
            "You are a regulatory affairs specialist. Answer the following questions "
            "about clinical trial regulatory requirements. Cite specific guideline "
            "sections where possible.\n\n"
            "Scenario: A clinical research organization (CRO) is designing a monitoring "
            "plan for a Phase III randomized controlled trial in oncology. The sponsor "
            "plans to use centralized monitoring only, with no on-site visits.\n\n"
            "Questions:\n"
            "1. Does ICH E6(R2) permit centralized-only monitoring without any on-site "
            "visits? What does the guideline say about the monitor's responsibilities "
            "for verifying data at investigative sites?\n"
            "2. What are the investigator's responsibilities for obtaining informed "
            "consent under ICH E6(R2)?\n\n"
            "For each answer:\n"
            "1. State the requirement clearly\n"
            "2. Cite the relevant guideline section (e.g., ICH E6 Section 5.x)\n"
            "3. Note any exceptions or conditions\n\n"
            "If you are unsure of the exact section number, state the principle and "
            "note that the specific citation should be verified."
        ),
        "scoring": "heuristic: requirement accuracy (0-35), citation specificity (0-25), completeness (0-20), avoids fabrication (0-20); total 100",
    },
    {
        "id": "startup_in_a_weekend",
        "name": "Startup in a Weekend",
        "prompt": (
            "You have 7 days and a team of 3 engineers to build an MVP for a B2B SaaS product: "
            "an AI-powered contract review assistant for legal teams. Users upload contracts "
            "(PDF/Word), the system extracts clauses, flags risks, suggests redlines, and "
            "produces a summary report.\n\n"
            "Deliver a complete, buildable plan. Your response must include all of the following:\n"
            "1. System architecture (text description of components and data flow).\n"
            "2. Database schema with concrete tables/collections and key fields.\n"
            "3. Backend API endpoints with HTTP methods, paths, and example request/response shapes.\n"
            "4. Authentication and authorization strategy.\n"
            "5. Frontend key screens and navigation.\n"
            "6. AI/LLM pipeline for clause extraction, risk classification, and redline generation.\n"
            "7. Deployment stack and infrastructure (name concrete services).\n"
            "8. Observability, logging, and error handling.\n"
            "9. Day-by-day 7-day schedule with deliverables per day.\n"
            "10. Cost estimate for infrastructure and AI usage at 100 active users/month.\n"
            "11. Top 5 technical risks and specific mitigations.\n"
            "12. What is explicitly out of MVP scope.\n\n"
            "Be specific: name concrete languages, frameworks, cloud services, and libraries."
        ),
        "scoring": "heuristic: section coverage, tech specificity, cost numbers, 7-day schedule, risk/mitigations, scope boundaries; total 100",
    },
]

# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

def fetch_pricing(api_key: str) -> dict:
    """Try to fetch per-model pricing from the Venice /models endpoint.
    Falls back to hardcoded approximate pricing on any failure."""
    pricing = dict(FALLBACK_PRICING)
    try:
        resp = requests.get(
            MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for entry in data.get("data", []):
            model_id = entry.get("id")
            spec = entry.get("model_spec", {}) or {}
            price = spec.get("pricing", {}) or entry.get("pricing", {}) or {}
            inp = price.get("input") or price.get("prompt")
            out = price.get("output") or price.get("completion")
            # Venice may return nested {"usd": N, "diem": N} pricing objects.
            if isinstance(inp, dict):
                inp = inp.get("usd", inp.get("diem"))
            if isinstance(out, dict):
                out = out.get("usd", out.get("diem"))
            if model_id and inp is not None and out is not None:
                try:
                    pricing[model_id] = {"input": float(inp), "output": float(out)}
                except (TypeError, ValueError):
                    pass
        print("Pricing: fetched from Venice /models endpoint (with fallbacks).")
    except Exception as exc:
        print(f"Pricing: could not fetch /models ({exc}); using hardcoded approximate rates.")
    return pricing


def estimate_cost(model_id: str, prompt_tokens: int, completion_tokens: int, pricing: dict) -> float:
    rates = pricing.get(model_id, DEFAULT_PRICING)
    cost = (prompt_tokens / 1_000_000) * rates["input"] + \
           (completion_tokens / 1_000_000) * rates["output"]
    return round(cost, 6)

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_intent_understanding(text: str) -> int:
    """Placeholder auto-score; real scoring is manual."""
    if not text:
        return 0
    score = 0
    lower = text.lower()
    # Clarifying questions (0-40): count question marks, cap at 40.
    question_count = text.count("?")
    score += min(question_count * 10, 40)
    # Structured proposal (0-30): headings / bullets / numbering.
    structure_hits = sum(
        1 for marker in ("- ", "* ", "1.", "2.", "##", "**")
        if marker in text
    )
    score += min(structure_hits * 6, 30)
    # Avoids hallucination (0-30): rough proxy - hedging / asking before assuming.
    hedges = sum(
        1 for w in ("clarify", "before", "depends", "assume", "confirm", "could you")
        if w in lower
    )
    score += min(hedges * 6, 30)
    return min(score, 100)


def score_one_shot_ui(text: str) -> int:
    """Heuristic score for one-shot HTML generation (0-100).

    Penalizes incomplete/near-empty responses. Rewards UI completeness,
    not just tag presence. Empty or placeholder-only output scores 0.
    """
    if not text or not text.strip():
        return 0
    lower = text.lower()

    # Structural completeness (35 points)
    # A truly complete HTML page has these structural elements
    has_doctype = "<!doctype" in lower
    has_html_tag = "<html" in lower
    has_head = "<head" in lower
    has_body = "<body" in lower
    has_closing_html = "</html>" in lower

    structure_score = 0
    if has_doctype and has_html_tag and has_head and has_body and has_closing_html:
        structure_score = 35
    elif has_doctype and has_html_tag and has_body and has_closing_html:
        structure_score = 25
    elif has_html_tag and has_body:
        structure_score = 15
    elif has_html_tag or has_doctype:
        structure_score = 5

    # If no HTML tag at all, this isn't generating a UI — score 0
    if not has_html_tag:
        return 0

    # Embedded CSS (15 points) — must have actual CSS rules, not just a <style> tag
    css_rules_found = 0
    if "<style" in lower:
        # Rough heuristic: count CSS rule markers (curly braces)
        style_start = lower.find("<style")
        style_section = lower[style_start:lower.find("</style>", style_start)] if "</style>" in lower else lower[style_start:]
        css_rules_found = style_section.count("{") + style_section.count("@")
        if css_rules_found >= 3:
            css_score = 15
        elif css_rules_found >= 1:
            css_score = 8
        else:
            css_score = 0
    else:
        css_score = 0

    # Interactive JS (15 points)
    js_found = "<script" in lower and "</script>" in lower
    has_event = any(e in lower for e in ("onclick", "onchange", "oninput", "onsubmit", "addEventListener"))
    if js_found and has_event:
        js_score = 15
    elif js_found:
        js_score = 8
    else:
        js_score = 0

    # Visual UI elements (20 points)
    has_button = "button" in lower
    has_form_input = "input" in lower or "<form" in lower
    has_card = "card" in lower or "container" in lower
    has_focus_display = ("focus" in lower or "score" in lower) or ("sparkline" in lower or "chart" in lower)
    ui_score = sum([
        5 if has_button else 0,
        5 if has_form_input else 0,
        5 if has_card else 0,
        5 if has_focus_display else 0,
    ])

    # Responsiveness (5 points)
    has_viewport = "viewport" in lower or "meta name" in lower
    has_media_query = "@media" in lower
    has_flex = "flex" in lower or "grid" in lower
    responsive_score = 0
    if has_viewport and has_media_query:
        responsive_score = 5
    elif has_viewport and has_flex:
        responsive_score = 3
    elif has_viewport:
        responsive_score = 2

    # Verbosity penalty (up to -10) — very long responses that still lack structure
    length_penalty = 0
    if len(text) > 3000 and (not has_head or not has_body):
        length_penalty = -10

    # Anti-windowing penalty (-10) — raw text with minor HTML interspersed
    words = text.split()
    html_ratio = sum(1 for w in words if w.startswith("<")) / max(len(words), 1)
    if html_ratio < 0.15 and len(words) > 50:
        length_penalty = min(length_penalty, -10)

    total = structure_score + css_score + js_score + ui_score + responsive_score + length_penalty
    return max(0, min(100, int(total)))




def score_startup_in_a_weekend(text: str) -> int:
    """Score the Startup-in-a-Weekend plan (0-100)."""
    if not text:
        return 0
    import re
    low = text.lower()
    score = 0

    # Section coverage (0-48) - 12 sections, 4 pts each
    sections = [
        r"\barchitecture\b|data flow|component",
        r"\bschema\b|tables?\b|collections?|database",
        r"\bapi\b|\bendpoints?\b|request/response|http method",
        r"\bauth\b|authentication|authorization|oauth|jwt|rbac",
        r"\bfrontend\b|\bscreen\b|\bui\b|navigation|dashboard",
        r"\bllm\b|clause extraction|risk classification|redline|prompt",
        r"\bdeplo\b|infrastructure|aws|gcp|azure|docker|kubernetes|hosting",
        r"\bobservability\b|logging|monitoring|error handling|tracing|sentry",
        r"\bday\s*1\b|\bday\s*7\b|schedule|timeline|phased",
        r"\bcost\b|\$\d|pricing|estimate|\bmonth\b",
        r"\brisk\b|mitigation|failure mode",
        r"\bscope\b|out of scope|defer|not in mvp|post-mvp",
    ]
    section_hits = sum(1 for pat in sections if re.search(pat, low))
    score += section_hits * 4

    # Tech specificity (0-24)
    tech_terms = [
        "postgresql", "mysql", "mongodb", "sqlite", "redis",
        "s3", "blob storage", "gcs", "azure blob",
        "fastapi", "flask", "django", "express", "next.js", "rails",
        "react", "vue", "svelte", "typescript", "tailwind",
        "docker", "kubernetes", "terraform", "pulumi", "github actions",
        "aws", "gcp", "azure", "vercel", "netlify", "fly.io", "heroku",
        "openai", "anthropic", "langchain", "llamaindex", "huggingface",
        "celery", "rq", "kafka", "rabbitmq",
        "sentry", "datadog", "grafana", "prometheus", "cloudwatch",
    ]
    tech_hits = sum(1 for t in tech_terms if t in low)
    score += min(tech_hits * 2, 24)

    # Quantitative / schedule rigor (0-16)
    if re.search(r"\$\d{1,4}(\.\d{2})?|\d+\s*(usd|gb|tb|k|m)\b", low):
        score += 6
    if re.search(r"\bday\s*1\b.*\bday\s*7\b|\b7-day\b|\bseven days\b", low, re.DOTALL):
        score += 5
    if re.search(r"\b100\s+active\b|\b100\s+users\b|\busers/month\b", low):
        score += 5

    # Risk & scope quality (0-12)
    risk_lines = [line for line in text.splitlines() if re.search(r"\brisk\b|\bmitigation\b", line.lower())]
    if len(risk_lines) >= 5:
        score += 6
    scope_lines = [line for line in text.splitlines() if re.search(r"\bscope\b|\bout of scope\b|\bdefer\b|\bpost-mvp\b", line.lower())]
    if len(scope_lines) >= 2:
        score += 6

    return min(score, 100)


def score_pharma_drug_interaction(text: str) -> int:
    """Heuristic scorer for Pharma DDI identification (0-100)."""
    if not text:
        return 0
    import re
    low = text.lower()
    score = 0

    # Interaction detection (0-35): must mention warfarin+ibuprofen pair
    if ("warfarin" in low and "ibuprofen" in low and
            any(w in low for w in ("interact", "risk", "combination", "concomitant", "co-admin"))):
        score += 25
    # Should NOT flag lisinopril+warfarin as a major interaction
    if not ("lisinopril" in low and "warfarin" in low and
            any(w in low for w in ("major", "severe", "significant interact"))):
        score += 10

    # Severity classification (0-20)
    severity_terms = {"major": 0, "moderate": 0, "minor": 0}
    for sev in severity_terms:
        if sev in low:
            severity_terms[sev] = 1
    if severity_terms["major"] >= 1:
        score += 12
    if sum(severity_terms.values()) >= 2:
        score += 8

    # Mechanism accuracy (0-25)
    mechanism_terms = [
        "cyp", "enzyme", "inhibitor", "inducer", "substrate",
        "pharmacodynamic", "pharmacokinetic", "protein binding",
        "platelet", "bleeding", "gastric", "mucosa", "coagulat",
        "nsaid", "anticoagulant", "synerg", "additive"
    ]
    mech_hits = sum(1 for t in mechanism_terms if t in low)
    score += min(mech_hits * 3, 25)

    # Clinical action (0-10)
    action_terms = ["avoid", "monitor", "discontinue", "alternative", "separate",
                    "dose adjustment", "contraindicated", "caution", "recommend"]
    action_hits = sum(1 for t in action_terms if t in low)
    score += min(action_hits * 3, 10)

    # Avoids hallucination (0-10): bonus for expressing uncertainty
    uncertainty_terms = ["uncertain", "may", "possible", "potential", "should verify",
                         "consult", "clinical judgment", "evidence"]
    unc_hits = sum(1 for t in uncertainty_terms if t in low)
    score += min(unc_hits * 3, 10)

    return min(score, 100)


def score_pharma_regulatory_comprehension(text: str) -> int:
    """Heuristic scorer for Pharma regulatory comprehension (0-100)."""
    if not text:
        return 0
    import re
    low = text.lower()
    score = 0

    # Requirement accuracy (0-35)
    requirement_terms = [
        "monitor", "on-site", "source data", "verification",
        "informed consent", "written", "documented",
        "investigator", "subject", "prior to"
    ]
    req_hits = sum(1 for t in requirement_terms if t in low)
    score += min(req_hits * 4, 35)

    # Citation specificity (0-25)
    citation_patterns = [
        r"ich\s*e6", r"ich\s*e8", r"ich\s*e9", r"ich\s*e2a",
        r"21\s*cfr\s*312", r"section\s*\d", r"§\s*\d",
        r"5\.18", r"4\.8", r"312\.23", r"312\.40"
    ]
    cite_hits = sum(1 for p in citation_patterns if re.search(p, low))
    score += min(cite_hits * 5, 25)

    # Completeness (0-20)
    completeness_terms = [
        "exception", "condition", "unless", "however", "note",
        "additionally", "furthermore", "representative", "legally"
    ]
    comp_hits = sum(1 for t in completeness_terms if t in low)
    score += min(comp_hits * 4, 20)

    # Avoids fabrication (0-20): bonus for hedging/uncertainty
    hedge_terms = [
        "should be verified", "consult", "confirm", "check",
        "exact section", "may vary", "approximate", "believe",
        "to my knowledge", "not certain"
    ]
    hedge_hits = sum(1 for t in hedge_terms if t in low)
    score += min(hedge_hits * 5, 20)

    return min(score, 100)


SCORERS = {
    "intent_understanding": score_intent_understanding,
    "one_shot_ui": score_one_shot_ui,
    "startup_in_a_weekend": score_startup_in_a_weekend,
    "pharma_drug_interaction": score_pharma_drug_interaction,
    "pharma_regulatory_comprehension": score_pharma_regulatory_comprehension,
}

# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def call_venice(api_key: str, model_id: str, prompt: str) -> dict:
    """Make a single chat completion call. Returns a result dict; never raises."""
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    start = time.monotonic()
    try:
        resp = requests.post(API_URL, headers=headers, json=payload,
                             timeout=REQUEST_TIMEOUT_SECONDS)
        latency = round(time.monotonic() - start, 3)
        if resp.status_code != 200:
            return {
                "status": "error",
                "http_status": resp.status_code,
                "latency": latency,
                "error": resp.text[:500],
                "raw_response": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        data = resp.json()
        usage = data.get("usage", {}) or {}
        content = ""
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        if not content.strip():
            return {
                "status": "error",
                "http_status": 200,
                "latency": latency,
                "error": "API returned no final response content (likely exhausted its completion budget).",
                "raw_response": "",
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "completion_tokens": int(usage.get("completion_tokens", 0)),
                "total_tokens": int(usage.get("total_tokens", 0)),
            }
        return {
            "status": "ok",
            "http_status": 200,
            "latency": latency,
            "raw_response": content,
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
    except Exception as exc:
        latency = round(time.monotonic() - start, 3)
        return {
            "status": "error",
            "http_status": None,
            "latency": latency,
            "error": str(exc)[:500],
            "raw_response": "",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

# ---------------------------------------------------------------------------
# Dry-run sample data
# ---------------------------------------------------------------------------

def fake_response(benchmark_id: str, model_display: str) -> str:
    if benchmark_id == "intent_understanding":
        return (
            f"({model_display} sample) Before proposing a solution, could you clarify: "
            "1. How large is the team? 2. Which Slack channels generate the most noise? "
            "3. Where does duplicate work usually happen?\n\n"
            "**Preliminary proposal:**\n- A Slack digest bot\n- A shared task board integration\n"
            "This depends on your workflow, so I'd like to confirm details first."
        )
    if benchmark_id == "one_shot_ui":
        return (
            f"<!DOCTYPE html>\n<html>\n<head><style>body{{background:#111;color:#eee}}"
            ".card{{padding:16px}}</style></head>\n<body>\n<div class='card'>"
            f"<h2>Focus Score</h2><p>82</p><svg width='120' height='30'></svg>"
            "<button onclick='start()'>Start Focus</button></div>\n"
            "<script>function start(){console.log('focus')}</script>\n</body>\n</html>"
        )
    if benchmark_id == "startup_in_a_weekend":
        return (
            f"({model_display} sample) 7-day build plan for an AI contract review MVP:\n\n"
            "## Architecture\n"
            "React frontend + FastAPI backend + PostgreSQL + Redis + S3 + OpenAI GPT-4o.\n\n"
            "## Database schema\n"
            "users(id, email), organizations(id, name), contracts(id, user_id, s3_key, status), "
            "clauses(id, contract_id, type, risk_level, text), redlines(id, clause_id, suggestion).\n\n"
            "## API endpoints\n"
            "POST /auth/login (JWT), POST /contracts (upload), GET /contracts/{id}, "
            "GET /contracts/{id}/report, POST /contracts/{id}/redlines.\n\n"
            "## AI pipeline\n"
            "PDF text extraction (PyMuPDF) → clause segmentation → LLM risk classification → redline generation.\n\n"
            "## Deployment\n"
            "Docker + AWS ECS/Fargate + RDS PostgreSQL + S3 + CloudFront.\n\n"
            "## 7-day schedule\n"
            "Day 1: Auth + DB schema. Day 2: Upload + storage. Day 3: Extraction pipeline. "
            "Day 4: LLM classification + redlines. Day 5: Frontend report screen. Day 6: Polish + tests. Day 7: Deploy.\n\n"
            "## Cost estimate at 100 users/month\n"
            "~$450/month: AWS $250, OpenAI $150, Sentry/Datadog $50.\n\n"
            "## Risks & mitigations\n"
            "1. PDF parsing errors → fallback to OCR. 2. LLM hallucinations → constrained prompts + human review loop.\n"
            "3. Data privacy → encrypt at rest, SOC 2 prep deferred. 4. Latency → async processing + Redis queue.\n"
            "5. Scope creep → explicit out-of-scope list.\n\n"
            "## Out of scope\n"
            "Negotiation AI, e-signature, multi-language, enterprise SSO, SOC 2 audit."
        )
    if benchmark_id == "pharma_drug_interaction":
        return (
            f"({model_display} sample) Drug-Drug Interaction Analysis:\n\n"
            "1. Warfarin + Ibuprofen — **Major**\n"
            "Mechanism: NSAIDs inhibit platelet function and increase gastric bleeding risk; "
            "ibuprofen may also displace warfarin from protein binding, enhancing anticoagulant effect.\n"
            "Clinical action: Avoid concurrent use; consider acetaminophen as alternative analgesic.\n\n"
            "2. Warfarin + Lisinopril — **Minor**\n"
            "No clinically significant pharmacokinetic interaction expected. ACE inhibitors do not "
            "meaningfully affect warfarin metabolism or coagulation.\n"
            "Clinical action: Monitor INR routinely as standard practice.\n\n"
            "I am uncertain about the exact magnitude of protein binding displacement and would "
            "recommend verifying with a clinical decision support tool."
        )
    if benchmark_id == "pharma_regulatory_comprehension":
        return (
            f"({model_display} sample) Regulatory Analysis:\n\n"
            "1. Centralized-only monitoring under ICH E6(R2):\n"
            "ICH E6 Section 5.18 states that the monitor should verify source data at investigative sites. "
            "Centralized monitoring is encouraged as a supplement, but Section 5.18.3 indicates that "
            "on-site monitoring remains important for source data verification.\n"
            "Exception: Risk-based approaches may reduce but not eliminate on-site visits.\n\n"
            "2. Investigator responsibilities for informed consent (Section 4.8):\n"
            "The investigator must obtain written, dated, and signed informed consent from each subject "
            "prior to participation. The consent process must be documented.\n"
            "Note: The exact section number should be verified against the current guideline version."
        )
    raise ValueError(f"Unknown benchmark fixture: {benchmark_id}")

    return (
        f"({model_display} sample) Plan:\n"
        "1. Step 1: Monitor arXiv via the arXiv API with a cron scheduler.\n"
        "2. Step 2: Summarize papers with an LLM.\n"
        "3. Step 3: Store embeddings in a vector database (Chroma/Pinecone).\n"
        "4. Step 4: Answer questions with retrieval + citations.\n"
        "5. Step 5: Add evaluation and monitoring.\n\n"
        "Tools: arXiv API, embedding model, vector DB, LangChain.\n"
        "Failure modes: rate limits, hallucinated citations, stale index, API downtime."
    )


def simulate_call(benchmark_id: str, model: dict) -> dict:
    text = fake_response(benchmark_id, model["display"])
    prompt_tokens = random.randint(60, 140)
    completion_tokens = random.randint(300, 1200)
    return {
        "status": "ok",
        "http_status": 200,
        "latency": round(random.uniform(1.5, 18.0), 3),
        "raw_response": text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }

# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def estimate_total_cost(pricing: dict) -> float:
    """Rough pre-run cost estimate: assume ~150 input tokens and full
    max_tokens output per call."""
    total = 0.0
    for model in MODELS:
        for _ in BENCHMARKS:
            total += estimate_cost(model["id"], 150, MAX_TOKENS, pricing)
    return round(total, 4)


def run(dry_run: bool, model_filter: str | None = None,
        benchmark_filter: str | None = None,
        max_tokens_override: int | None = None,
        request_timeout_override: float | None = None) -> None:
    # Per-run cap overrides (see CLI flags). Mutating module globals is the
    # minimal-blast-radius way; the caller's in-flight process has its own
    # imported copy and is unaffected.
    global MAX_TOKENS, REQUEST_TIMEOUT_SECONDS
    if max_tokens_override is not None:
        MAX_TOKENS = max_tokens_override
    if request_timeout_override is not None:
        REQUEST_TIMEOUT_SECONDS = request_timeout_override

    api_key = os.environ.get(API_KEY_ENV, "")
    pricing = dict(FALLBACK_PRICING)

    selected_models = MODELS
    if model_filter:
        selected_models = [m for m in MODELS if m["id"] == model_filter or m["display"].lower() == model_filter.lower()]
        if not selected_models:
            known = ", ".join(m["id"] for m in MODELS)
            print(f"ERROR: model '{model_filter}' not found. Known ids: {known}")
            sys.exit(1)

    selected_benchmarks = BENCHMARKS
    if benchmark_filter:
        selected_benchmarks = [b for b in BENCHMARKS if b["id"] == benchmark_filter]
        if not selected_benchmarks:
            known = ", ".join(b["id"] for b in BENCHMARKS)
            print(f"ERROR: benchmark '{benchmark_filter}' not found. Known ids: {known}")
            sys.exit(1)

    if not dry_run:
        if not api_key:
            print(f"ERROR: environment variable {API_KEY_ENV} is not set.")
            sys.exit(1)
        pricing = fetch_pricing(api_key)
        est = 0.0
        for model in selected_models:
            for _ in selected_benchmarks:
                est += estimate_cost(model["id"], 150, MAX_TOKENS, pricing)
        print(f"\nEstimated maximum total cost for this run: ${est:.4f} "
              f"({len(selected_models)} model(s) x up to {len(selected_benchmarks)} benchmarks, "
              f"assuming full {MAX_TOKENS}-token outputs)\n")
    else:
        print("Mode: DRY RUN (no API calls, sample data will be generated).\n")

    results = []
    total_cost = 0.0
    total_calls = sum(
        len([b for b in selected_benchmarks if model["id"] not in MODEL_BENCHMARK_LIMITS or b["id"] in MODEL_BENCHMARK_LIMITS[model["id"]]])
        for model in selected_models
    )
    call_index = 0

    for model in selected_models:
        allowed = MODEL_BENCHMARK_LIMITS.get(model["id"])
        benches = [b for b in selected_benchmarks if not allowed or b["id"] in allowed]
        for bench in benches:
            call_index += 1
            print(f"[{call_index}/{total_calls}] {model['display']} ({model['id']}) "
                  f"-> {bench['name']} ... ", end="", flush=True)

            if dry_run:
                call = simulate_call(bench["id"], model)
            else:
                call = call_venice(api_key, model["id"], bench["prompt"])

            if call["status"] == "ok":
                score = SCORERS[bench["id"]](call["raw_response"])
                cost = estimate_cost(model["id"], call["prompt_tokens"],
                                     call["completion_tokens"], pricing)
                total_cost += cost
                print(f"ok  score={score}  latency={call['latency']}s  "
                      f"tokens={call['total_tokens']}  cost=${cost:.6f}")
            else:
                score = 0
                cost = 0.0
                print(f"ERROR ({call.get('error', 'unknown')[:120]}) - continuing.")

            results.append({
                "model_id": model["id"],
                "benchmark_id": bench["id"],
                "status": call["status"],
                "score": score,
                "latency": call["latency"],
                "prompt_tokens": call["prompt_tokens"],
                "completion_tokens": call["completion_tokens"],
                "total_tokens": call["total_tokens"],
                "estimated_cost_usd": cost,
                "raw_response": call["raw_response"],
                "error": call.get("error"),
            })

            if not dry_run and call_index < total_calls:
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)

    # Partial runs merge into existing results so we can add models without
    # re-running the full matrix.
    existing = None
    if (model_filter or benchmark_filter) and RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception as exc:
            print(f"Warning: could not load existing results for merge ({exc}).")

    if existing and isinstance(existing.get("results"), list):
        selected_pairs = {(r["model_id"], r["benchmark_id"]) for r in results}
        kept = [r for r in existing["results"]
                if (r.get("model_id"), r.get("benchmark_id")) not in selected_pairs]
        merged_results = kept + results
        # Prefer the canonical MODELS list, but preserve any unknown extras.
        existing_models = existing.get("models") or []
        known_ids = {m["id"] for m in MODELS}
        extras = [m for m in existing_models if m.get("id") not in known_ids]
        models_out = MODELS + extras
        prior_cost = float(existing.get("total_estimated_cost_usd") or 0.0)
        prior_cost_kept = sum(
            float(r.get("estimated_cost_usd") or 0.0)
            for r in kept
        )
        total_cost_out = round(prior_cost_kept + total_cost, 6)
        dry_run_out = bool(existing.get("dry_run")) and dry_run
        print(f"Merging {len(results)} new result(s) into existing file "
              f"({len(kept)} prior rows kept).")
    else:
        merged_results = results
        models_out = MODELS
        total_cost_out = round(total_cost, 6)
        dry_run_out = dry_run

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run_out,
        "models": models_out,
        "benchmarks": [
            {"id": b["id"], "name": b["name"], "prompt": b["prompt"], "scoring": b["scoring"]}
            for b in BENCHMARKS
        ],
        "results": merged_results,
        "total_estimated_cost_usd": total_cost_out,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(merged_results)} results written to {RESULTS_PATH}")
    print(f"Run estimated cost: ${total_cost:.6f}  |  file total: ${total_cost_out:.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BenchmarkViv - run practical benchmarks against the Venice API."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true",
                       help="Generate sample data without API calls (default).")
    group.add_argument("--run-real", action="store_true",
                       help="Make real API calls (requires VENICE_INFERENCE_KEY).")
    parser.add_argument("--model", metavar="ID",
                        help="Run only one model id/display name; merges into existing results.json.")
    parser.add_argument("--benchmark", metavar="ID",
                        help="Run only one benchmark id; merges only the matching result rows.")
    parser.add_argument("--max-tokens", type=int, metavar="N",
                        help=f"Override completion cap (default {MAX_TOKENS}).")
    parser.add_argument("--request-timeout", type=float, metavar="SEC",
                        help=f"Override HTTP read timeout (default {REQUEST_TIMEOUT_SECONDS}s).")
    args = parser.parse_args()

    dry_run = not args.run_real  # default to dry-run
    run(dry_run, model_filter=args.model, benchmark_filter=args.benchmark,
        max_tokens_override=args.max_tokens,
        request_timeout_override=args.request_timeout)


if __name__ == "__main__":
    main()
