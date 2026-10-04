"""
checks.py — Keyword scanner (pure Python, no AI).

What this file does:
1. Takes the full Terms & Conditions text.
2. Counts total words and total sections.
3. Searches for risky keywords across 4 categories.
4. Pulls a small context window around each keyword hit.
5. Returns a small, clean payload that the AI can consume.

Why this file exists separately:
- Sending the full T&C to the AI is expensive, slow, and noisy.
- Sending only relevant chunks is cheaper, faster, and more focused.
- This is pure Python, so it can be unit-tested without touching the AI.
"""

import re


# ─────────────────────────────────────────────────────────────
# Keyword dictionary — grouped by risk category.
# To add/remove a keyword, edit ONLY this block. Nothing else.
#
# money   → things that cost the user money
# privacy → how personal information is collected or shared
# data    → what happens to user data (sold, stored, deleted)
# rights  → legal rights the user gives up (court, content, etc.)
# ─────────────────────────────────────────────────────────────
KEYWORDS = {
    "money": [
        "auto-renew", "auto renew", "subscription", "billing",
        "charge", "payment", "refund", "cancel", "price change",
        "trial", "fee",
    ],
    "privacy": [
        "personal information", "collect", "cookies", "tracking",
        "share your data", "third party", "advertis", "opt-out",
    ],
    "data": [
        "sell", "transfer", "retention", "delete your data",
        "store", "process", "aggregate",
    ],
    "rights": [
        "arbitration", "class action", "governing law", "liability",
        "indemnif", "terminate", "suspend", "modify these terms",
        "license", "intellectual property",
    ],
}


def _count_sections(text):
    """
    Count how many sections the document has.

    A section is a line that starts with a number, a roman numeral,
    or a keyword like ARTICLE / SECTION / CLAUSE.

    Examples that match:
        "1. Introduction"
        "ARTICLE 5"
        "SECTION 3"
        "IV. Liability"

    If nothing matches, we return 1 (not 0) so the UI never shows
    a meaningless "0 sections".
    """
    pattern = r"^\s*(?:\d+\.|[IVX]+\.|ARTICLE|SECTION|CLAUSE)\s"
    count = 0
    for line in text.splitlines():
        if re.match(pattern, line.strip(), re.IGNORECASE):
            count += 1
    return max(count, 1)


def _extract_context(text, match_start, match_end, window=200):
    """
    Pull the text surrounding a keyword hit.

    Why: a single word like "auto-renew" is meaningless on its own.
    The AI needs the full sentence/clause around it to judge risk.

    window = how many characters to grab on each side (default 200).

    We also collapse all whitespace (newlines, tabs, multiple spaces)
    into a single space so the output is clean and readable.
    """
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    snippet = text[start:end].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet


def analyze(text):
    """
    Main entry point — called by app.py.

    Input:
        text (str) → the raw Terms & Conditions text.

    Output (dict):
        {
            "word_count":    int,
            "section_count": int,
            "chunks": [                       # this goes to the AI
                {
                    "keyword":  str,
                    "category": str,
                    "context":  str,
                },
                ...
            ],
            "flags": {                        # category-wise hit counts
                "money":   int,
                "privacy": int,
                "data":    int,
                "rights":  int,
            },
        }
    """

    # ── Guard: empty or whitespace-only input ─────────────────
    if not text or not text.strip():
        return {
            "word_count": 0,
            "section_count": 0,
            "chunks": [],
            "flags": {cat: 0 for cat in KEYWORDS},
        }

    # ── Prepare search state ──────────────────────────────────
    # We search in a lowercase copy so matching is case-insensitive.
    # But we slice context from the ORIGINAL text so casing is preserved.
    lower_text = text.lower()
    chunks = []
    flags = {cat: 0 for cat in KEYWORDS}
    seen = set()  # tracks (keyword, block_index) to avoid duplicates

    # ── Walk every category → every keyword → every hit ───────
    for category, words in KEYWORDS.items():
        for kw in words:
            for m in re.finditer(re.escape(kw.lower()), lower_text):

                # Deduplicate: if the same keyword appears twice within
                # the same 150-character block, count it only once.
                # Without this, a single dense clause could spam chunks.
                block_index = m.start() // 150
                dedup_key = (kw, block_index)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Build one chunk: keyword + category + surrounding text.
                chunks.append({
                    "keyword": kw,
                    "category": category,
                    "context": _extract_context(text, m.start(), m.end()),
                })

                # Increment the counter for this category.
                flags[category] += 1

    # ── Final payload ─────────────────────────────────────────
    return {
        "word_count": len(text.split()),
        "section_count": _count_sections(text),
        "chunks": chunks,
        "flags": flags,
    }