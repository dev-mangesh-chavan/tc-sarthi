# 📜 TC Sarthi

> A simple AI agent that reads Terms & Conditions for you and tells you what actually matters — in plain language, in seconds.

---

## Why this exists

Nobody reads Terms & Conditions. They are 15–20 pages long, written in legal English, and every "I Agree" button hides clauses that cost you money, take your data, or remove your right to go to court.

**TC Sarthi reads it for you.** Paste the text (or upload a file), and get:

- **Main points** — 5–7 plain-language facts you must know
- **Risk areas** — Money, Privacy, Data, and Rights, each scored Low / Medium / High
- **Final verdict** — one direct line telling you what to do

Built as a small, focused project. No bloat. No dashboard. One job, done cleanly.

---

## How it works

```
User pastes T&C text
        │
        ▼
┌───────────────────────┐
│  checks.py            │   Pure Python. Scans the text for risky
│  (keyword scanner)    │   keywords across 4 categories, pulls a
│                       │   context window around each hit, counts
│                       │   words & sections. No AI yet.
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  prompts.py           │   Builds the system prompt + user prompt
│  (prompt builder)     │   from the scanned chunks. Enforces a
│                       │   fixed JSON output schema.
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  agent.py             │   Sends the prompt to Gemini or OpenAI,
│  (AI brain)           │   parses the JSON response, validates it
│                       │   with Pydantic, returns a clean dict.
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  app.py               │   Streamlit UI. Two columns: input on
│  (UI)                 │   the left, styled result on the right.
└───────────────────────┘
```

**Why split like this?**

- `checks.py` runs without AI — fast, free, testable in isolation
- Only the filtered chunks go to the AI — cheaper and more focused than sending 20 pages
- `prompts.py` is separate so prompt tuning never touches logic
- `agent.py` is the only file that talks to a provider — swap Gemini ↔ OpenAI with one `.env` change

---

## Project structure

```
tc-sarthi/
│
├── .env                    # API keys (never pushed)
├── .env.example            # template for keys
├── .gitignore
├── requirements.txt
├── README.md
│
└── tc_sarthi/
    ├── __init__.py
    ├── app.py              # Streamlit UI
    ├── agent.py            # AI caller + validation
    ├── checks.py           # keyword scanner (no AI)
    └── prompts.py          # prompt + output schema
```

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/tc-sarthi.git
cd tc-sarthi
```

### 2. Create a virtual environment

```bash
python -m venv tenv
# Windows
tenv\Scripts\activate
# macOS / Linux
source tenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

Copy `.env.example` to `.env` and fill in your key.

**Option A — Gemini (default):**
```
PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

**Option B — OpenAI:**
```
PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

Get a Gemini key: https://aistudio.google.com/app/apikey
Get an OpenAI key: https://platform.openai.com/api-keys

### 5. Run the app

```bash
streamlit run tc_sarthi/app.py
```

Open http://localhost:8501 in your browser.

---

## How to use

1. Paste a T&C document into the left text box, **or** upload a `.txt` file
2. Click **🚀 Analyze**
3. Read the result on the right:
   - Main points
   - Four risk cards (Money / Privacy / Data / Rights)
   - Final verdict

If both a file and text are provided, the pasted text wins.

---

## The 4 risk categories

| Category | What it looks at |
|---|---|
| 💰 **Money** | Charges, auto-renewal, refunds, cancellation, price changes |
| 🔒 **Privacy** | What personal data is collected, tracked, and shared |
| 📦 **Data** | Whether data is sold, retained, transferred, or deleted |
| ⚖️ **Rights** | Arbitration clauses, class-action waivers, content licences, termination |

Each category gets a risk level: **Low**, **Medium**, or **High**.

---

## Tech stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| AI (primary) | Google Gemini via `google-genai` |
| AI (fallback) | OpenAI via `openai` |
| Validation | Pydantic |
| Config | python-dotenv |
| Testing | pytest |

---

## Configuration

All settings live in `.env`.

| Variable | Required when | Description |
|---|---|---|
| `PROVIDER` | Always | `gemini` or `openai` (defaults to `gemini`) |
| `GEMINI_API_KEY` | `PROVIDER=gemini` | Gemini API key |
| `OPENAI_API_KEY` | `PROVIDER=openai` | OpenAI API key |

Switching providers does **not** require any code change — just swap two lines in `.env`.

---

## Design principles

1. **Python filters, AI judges.** The keyword scanner narrows the input. The AI only sees what matters.
2. **Evidence over opinion.** Every chunk sent to the AI comes from the actual document, so the AI cannot invent clauses.
3. **One job per file.** UI, logic, prompt, and provider live separately.
4. **Plain language always.** No legal jargon in the output — the AI is explicitly instructed to explain, not paraphrase.
5. **Fail loud, fail clean.** Empty inputs, missing keys, bad JSON — every failure produces a readable message, never a crash.

---

## Limitations

- Only `.txt` files are accepted for upload. PDF support is not implemented yet.
- Keyword scanning is English-only.
- The AI can still make mistakes. Treat the output as a strong guide, not legal advice.
- Very long documents (50,000+ words) may hit model token limits; behaviour in that case is untested.

---

## Disclaimer

TC Sarthi is **not legal advice**. It is a reading aid. For anything with real consequences, consult a qualified lawyer.

---

## License

MIT