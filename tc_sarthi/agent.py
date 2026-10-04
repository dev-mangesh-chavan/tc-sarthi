"""
agent.py — The AI brain.

What this file does:
1. Loads the API key from .env based on the PROVIDER variable.
2. Initialises the correct client (Gemini or OpenAI).
3. Sends the SYSTEM_PROMPT + built user prompt to the AI.
4. Parses the JSON response safely.
5. Validates the structure with Pydantic.
6. Returns a clean dict the UI can render directly.

Why this file exists separately:
- It is the ONLY file that talks to an external AI provider.
- Switching between Gemini and OpenAI is a single .env change.
- The rest of the app never imports google-genai or openai directly.

Supported providers (set in .env):
    PROVIDER=gemini   + GEMINI_API_KEY=...
    PROVIDER=openai   + OPENAI_API_KEY=...
"""

import os
import json
from typing import Literal, List, Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from tc_sarthi import prompts
from tc_sarthi import checks


# ─────────────────────────────────────────────────────────────
# Load environment variables from .env once, at import time.
# ─────────────────────────────────────────────────────────────
load_dotenv()


# ─────────────────────────────────────────────────────────────
# Pydantic models — validate the AI's JSON before we trust it.
# If the AI returns a wrong shape, we catch it here, not in the UI.
# ─────────────────────────────────────────────────────────────

RiskLevel = Literal["low", "medium", "high"]


class RiskArea(BaseModel):
    """One risk category (money / privacy / data / rights)."""
    level: RiskLevel
    summary: str = Field(min_length=1)


class Verdict(BaseModel):
    """Overall verdict shown at the bottom of the UI."""
    level: RiskLevel
    message: str = Field(min_length=1)


class AIResult(BaseModel):
    """Full structured output expected from the AI."""
    main_points: List[str] = Field(min_length=1)
    risk_areas: Dict[str, RiskArea]
    verdict: Verdict


# ─────────────────────────────────────────────────────────────
# Model names — change here if you want a different model.
# ─────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-3.8-flash"
OPENAI_MODEL = "gpt-4o-mini"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _read_provider() -> str:
    """
    Read PROVIDER from .env.
    If missing or unknown, default to 'gemini'.
    """
    provider = (os.getenv("PROVIDER") or "gemini").strip().lower()
    if provider not in ("gemini", "openai"):
        return "gemini"
    return provider


def _strip_code_fences(text: str) -> str:
    """
    Some models wrap JSON in ```json ... ``` fences even when told not to.
    This removes those fences so json.loads() does not fail.
    """
    text = text.strip()
    if text.startswith("```"):
        # Drop the first line (``` or ```json)
        text = text.split("\n", 1)[1] if "\n" in text else text
        # Drop the trailing ```
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


def _parse_json(raw: str) -> dict:
    """
    Parse the AI's raw text into a Python dict.
    Raises ValueError if parsing fails.
    """
    cleaned = _strip_code_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI did not return valid JSON: {e}") from e


# ─────────────────────────────────────────────────────────────
# Provider callers — one function per provider.
# Each returns the raw text response from the model.
# ─────────────────────────────────────────────────────────────

def _call_gemini(user_prompt: str) -> str:
    """
    Send the prompt to Google Gemini using the new Interactions API
    and return the text response. Reads GEMINI_API_KEY from .env.

    Uses client.interactions.create(...) which is the current SDK entry
    point for text generation. The convenience property
    `interaction.output_text` gives us the final text directly.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing in .env")

    # Imported inside the function so the app can still run with
    # only openai installed (and vice-versa).
    from google import genai

    client = genai.Client(api_key=api_key)

    # Combine the system prompt with the user prompt.
    # The Interactions API takes a single `input` string; we pass
    # the system rules first so the model treats them as authoritative.
    full_input = f"{prompts.SYSTEM_PROMPT}\n\n---\n\n{user_prompt}"

    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        input=full_input,
    )

    # Convenience property for the final text output.
    text = getattr(interaction, "output_text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def _call_openai(user_prompt: str) -> str:
    """
    Send the prompt to OpenAI and return the text response.
    Reads OPENAI_API_KEY from .env.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("OpenAI returned an empty response.")
    return text


# ─────────────────────────────────────────────────────────────
# Main public function
# ─────────────────────────────────────────────────────────────

def run(text: str) -> dict:
    """
    Full pipeline: T&C text in → structured result out.

    Steps:
      1. checks.analyze(text)       → keyword scan + context chunks
      2. prompts.build_user_prompt  → final prompt string
      3. call the selected provider → raw JSON text
      4. parse + validate           → clean dict

    Returns a dict with this exact shape:
        {
            "main_points": [str, ...],
            "risk_areas": {
                "money":   {"level": ..., "summary": ...},
                "privacy": {"level": ..., "summary": ...},
                "data":    {"level": ..., "summary": ...},
                "rights":  {"level": ..., "summary": ...},
            },
            "verdict": {"level": ..., "message": ...},
            "meta": {
                "provider":      "gemini" | "openai",
                "word_count":    int,
                "section_count": int,
                "flags":         {category: int},
            },
        }

    Raises RuntimeError on any provider or parse failure, with a
    readable message so the UI can show it to the user.
    """

    # ── 1. Pure-Python pre-processing ─────────────────────────
    analysis = checks.analyze(text)

    # ── 2. Build the prompt ───────────────────────────────────
    user_prompt = prompts.build_user_prompt(analysis)

    # ── 3. Pick provider and call it ──────────────────────────
    provider = _read_provider()
    if provider == "gemini":
        raw_text = _call_gemini(user_prompt)
    else:
        raw_text = _call_openai(user_prompt)

    # ── 4. Parse + validate ───────────────────────────────────
    parsed = _parse_json(raw_text)

    try:
        validated = AIResult(**parsed)
    except ValidationError as e:
        raise RuntimeError(f"AI returned an unexpected structure: {e}") from e

    # ── 5. Attach meta and return as plain dict ───────────────
    result = validated.model_dump()
    result["meta"] = {
        "provider": provider,
        "word_count": analysis["word_count"],
        "section_count": analysis["section_count"],
        "flags": analysis["flags"],
    }
    return result