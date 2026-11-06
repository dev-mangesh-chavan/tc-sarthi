"""
agent.py — TC Sarthi AI brain.

Chain: 3 Gemini models → offline Python scan. Never fails.
Output: risk_percent, risk_level, reasons, action, mode.
"""

import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
MAX_CHARS = 4000
MAX_OUTPUT_TOKENS = 200

MODEL_CHAIN = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

_API_KEY = os.getenv("GEMINI_API_KEY")
if not _API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in .env")

_client = genai.Client(api_key=_API_KEY)


# ─────────────────────────────────────────────────────────────
# Prompt + schema
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a Terms & Conditions risk checker. "
    "Return ONLY JSON with: risk_percent (0-100), "
    "risk_level (Low|Medium|High), "
    "reasons (2-3 short bullets, max 10 words each), "
    "action (1 short line, max 15 words). "
    "Rubric: start 10; +20 auto-renewal; +20 personal data shared; "
    "+20 data sold; +15 arbitration. Cap 95. "
    "0-30=Low, 31-60=Medium, 61-95=High. "
    "Be direct. Warn the user. Never invent clauses."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_percent": {"type": "integer"},
        "risk_level":   {"type": "string", "enum": ["Low", "Medium", "High"]},
        "reasons":      {"type": "array", "items": {"type": "string"}},
        "action":       {"type": "string"},
    },
    "required": ["risk_percent", "risk_level", "reasons", "action"],
}


# ─────────────────────────────────────────────────────────────
# One Gemini call — no thinking_config, AFC disabled
# ─────────────────────────────────────────────────────────────
def _call_model(model: str, prompt: str) -> dict:
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        temperature=0.0,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    response = _client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    raw = getattr(response, "text", None)
    if not raw:
        raise RuntimeError(f"{model} returned empty.")

    return json.loads(raw)


# ─────────────────────────────────────────────────────────────
# Offline fallback — pure Python, 0 ms
# ─────────────────────────────────────────────────────────────
def _offline_scan(text: str) -> dict:
    t = text.lower()
    score = 10
    reasons = []

    if "auto-renew" in t or "auto renew" in t or "subscription" in t:
        score += 20
        reasons.append("Auto-renewal without reminder")
    if "share your data" in t or "third party" in t or "advertis" in t:
        score += 20
        reasons.append("Data shared with third parties")
    if "sell" in t or "transfer" in t:
        score += 20
        reasons.append("Data may be sold or transferred")
    if "arbitration" in t or "class action" in t:
        score += 15
        reasons.append("Disputes go to arbitration")

    score = min(95, score)
    if score <= 30:
        level, action = "Low", "Looks fine, but still skim the document."
    elif score <= 60:
        level, action = "Medium", "Read the risky parts before signing."
    else:
        level, action = "High", "Don't sign without cancelling auto-renew first."

    if not reasons:
        reasons = ["No major risk keywords found"]

    return {
        "risk_percent": score,
        "risk_level":   level,
        "reasons":      reasons[:3],
        "action":       action,
        "mode":         "offline",
    }


# ─────────────────────────────────────────────────────────────
# Clean AI output
# ─────────────────────────────────────────────────────────────
def _clean(data: dict, model: str) -> dict:
    percent = max(0, min(100, int(data.get("risk_percent", 0))))

    level = str(data.get("risk_level", "Low")).capitalize()
    if level not in ("Low", "Medium", "High"):
        level = "Low"

    reasons = data.get("reasons", []) or []
    if not isinstance(reasons, list):
        reasons = []
    reasons = [str(r).strip() for r in reasons if str(r).strip()][:3] or ["No major risk keywords found"]

    action = str(data.get("action", "")).strip() or "Read the full document before signing."

    return {
        "risk_percent": percent,
        "risk_level":   level,
        "reasons":      reasons,
        "action":       action,
        "mode":         "ai",
        "model":        model,
    }


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def run(text: str) -> dict:
    if not text or not text.strip():
        raise RuntimeError("No text provided.")

    trimmed = text.strip()[:MAX_CHARS]
    prompt = f"{SYSTEM_PROMPT}\n\nTerms & Conditions text:\n\n{trimmed}"

    for model in MODEL_CHAIN:
        try:
            data = _call_model(model, prompt)
            print(f"[TC Sarthi] ✓ {model}")
            return _clean(data, model)
        except Exception as e:
            print(f"[TC Sarthi] ✗ {model}: {type(e).__name__}: {e}")
            continue

    print("[TC Sarthi] ⚠ All models failed → offline scan")
    return _offline_scan(trimmed)