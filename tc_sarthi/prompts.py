"""
prompts.py — All AI prompt text lives here.

Why this file exists separately:
- Prompts change often. Keeping them isolated means agent.py never
  has to be touched when we tweak wording, tone, or output format.
- Both Gemini and OpenAI get the SAME prompt, so switching providers
  does not change the AI's behaviour.

What this file provides:
1. SYSTEM_PROMPT   → fixed rules that define the AI's role and tone.
2. OUTPUT_SCHEMA   → the exact JSON shape we expect back (for validation).
3. build_user_prompt(analysis) → builds the per-request prompt from
   the output of checks.analyze().
"""


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# This is sent on every request. It defines who the AI is and
# how it must behave. Do not change tone casually — the whole
# product experience depends on these rules.
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are TC Sarthi, a plain-language Terms & Conditions explainer.

YOUR ROLE
You explain a Terms & Conditions document to a normal user — not to a lawyer.
Your job is to protect the user, not to sound neutral or corporate.

TONE RULES
- Be direct. Be honest. Warn the user when something is against their interest.
- Use everyday language. No legal jargon. No "hereby", "aforesaid", "pursuant".
- If a clause is dangerous, say so clearly.
- If something is fine, say so — do not invent problems.
- Never write long paragraphs. Short, punchy sentences only.

STRICT RULES
- ONLY use the information given to you in the user message.
- Never invent clauses that are not present in the provided chunks.
- If a category has no relevant chunks, mark its risk as "low" and say
  "no risky clause found".
- Every risk summary must be understandable by a 15-year-old.
- Do not use the words: "indemnification", "liability", "arbitration clause",
  "governing law", "intellectual property". Instead explain what they MEAN.

OUTPUT FORMAT
You MUST return ONLY valid JSON. No markdown. No code fences. No extra text.
The JSON must match the schema given in the user message exactly.

REMEMBER
The user is not reading the T&C. They are reading YOUR output instead.
Your output IS the T&C for them. Make it count.
"""


# ─────────────────────────────────────────────────────────────
# OUTPUT SCHEMA
# Reference copy of the exact JSON the AI must return.
# This is embedded into the user prompt AND used by agent.py
# to validate the response before showing it to the user.
# ─────────────────────────────────────────────────────────────
OUTPUT_SCHEMA = {
    "main_points": [
        "5 to 7 short bullet strings. Each one a single clear fact."
    ],
    "risk_areas": {
        "money": {
            "level": "low | medium | high",
            "summary": "1-2 lines. Simple language.",
        },
        "privacy": {
            "level": "low | medium | high",
            "summary": "1-2 lines. Simple language.",
        },
        "data": {
            "level": "low | medium | high",
            "summary": "1-2 lines. Simple language.",
        },
        "rights": {
            "level": "low | medium | high",
            "summary": "1-2 lines. Simple language.",
        },
    },
    "verdict": {
        "level": "low | medium | high",
        "message": "One line. Direct advice for the user.",
    },
}


# ─────────────────────────────────────────────────────────────
# USER PROMPT BUILDER
# Called by agent.py with the dict returned from checks.analyze().
# Returns a single string — the full message the AI receives.
# ─────────────────────────────────────────────────────────────
def build_user_prompt(analysis: dict) -> str:
    """
    Build the per-request user prompt.

    Input:
        analysis (dict) → exact output of checks.analyze()
            {
                "word_count":    int,
                "section_count": int,
                "chunks":        [ {keyword, category, context}, ... ],
                "flags":         {category: count},
            }

    Output:
        str → the full user prompt, ready to send to the AI.
    """

    # ── Pull values with safe defaults ────────────────────────
    word_count = analysis.get("word_count", 0)
    section_count = analysis.get("section_count", 0)
    chunks = analysis.get("chunks", [])
    flags = analysis.get("flags", {})

    # ── Build the "facts" section ─────────────────────────────
    # These numbers help the AI understand the size and density
    # of the document at a glance.
    facts_lines = [
        f"- Total words: {word_count}",
        f"- Total sections: {section_count}",
        f"- Hits in 'money'   category: {flags.get('money', 0)}",
        f"- Hits in 'privacy' category: {flags.get('privacy', 0)}",
        f"- Hits in 'data'    category: {flags.get('data', 0)}",
        f"- Hits in 'rights'  category: {flags.get('rights', 0)}",
    ]
    facts_block = "\n".join(facts_lines)

    # ── Build the "chunks" section ────────────────────────────
    # Each chunk is one risky snippet with its category and keyword.
    # If there are no chunks, we tell the AI explicitly.
    if chunks:
        chunk_lines = []
        for i, c in enumerate(chunks, start=1):
            chunk_lines.append(
                f"[{i}] category={c.get('category', '?')} "
                f"keyword={c.get('keyword', '?')}\n"
                f"    context: {c.get('context', '').strip()}"
            )
        chunks_block = "\n\n".join(chunk_lines)
    else:
        chunks_block = "(No risky keywords were found in this document.)"

    # ── Build the schema block ────────────────────────────────
    # We show the AI the exact JSON shape it must return.
    # Written as plain text (not json.dumps) so it reads like a spec.
    schema_block = """{
  "main_points": [
    "short bullet 1",
    "short bullet 2",
    "short bullet 3",
    "short bullet 4",
    "short bullet 5"
  ],
  "risk_areas": {
    "money":   { "level": "low|medium|high", "summary": "1-2 lines" },
    "privacy": { "level": "low|medium|high", "summary": "1-2 lines" },
    "data":    { "level": "low|medium|high", "summary": "1-2 lines" },
    "rights":  { "level": "low|medium|high", "summary": "1-2 lines" }
  },
  "verdict": {
    "level": "low|medium|high",
    "message": "one direct line for the user"
  }
}"""

    # ── Assemble the final user prompt ────────────────────────
    user_prompt = f"""Analyze the Terms & Conditions data below and return ONLY the JSON.

DOCUMENT FACTS
{facts_block}

RISKY CHUNKS (each one is a snippet from the document)
{chunks_block}

WHAT YOU MUST DO
1. Read every chunk carefully.
2. Write "main_points": 5 to 7 short bullets covering the most important
   facts a user must know. Plain language only.
3. Fill "risk_areas" for all four categories: money, privacy, data, rights.
   - level must be one of: "low", "medium", "high".
   - summary must be 1-2 lines in simple language.
   - If a category has no risky chunks, set level to "low" and write
     "No risky clause found in this document."
4. Write "verdict":
   - level = the single overall risk level of the whole document.
   - message = one direct line telling the user what to do.
5. Return ONLY the JSON. No explanation. No markdown. No code fences.

OUTPUT JSON SCHEMA (return exactly this shape)
{schema_block}
"""

    return user_prompt