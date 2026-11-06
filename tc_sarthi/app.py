"""
app.py — TC Sarthi UI (horizontal layout).

Layout:
    ┌──────────────┬──────────────┐
    │  ✍️ Paste    │  📥 Upload   │
    └──────────────┴──────────────┘
    ┌──────────────────────────────┐
    │   🚀 Analyze                 │
    └──────────────────────────────┘
    ┌──────────────────────────────┐
    │   📊 Output card             │
    └──────────────────────────────┘
    ┌────┬────┬────┬────┐
    │ ⚡ │ 🔒 │ 🎯 │ 💡 │
    └────┴────┴────┴────┘
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from tc_sarthi.agent import run


# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TC Sarthi",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MAX_FILE_KB = 50
MAX_FILE_BYTES = MAX_FILE_KB * 1024
MAX_PASTE_CHARS = 50000


@st.cache_data(ttl=600, show_spinner=False)
def _analyze_cached(text: str) -> dict:
    return run(text)


# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 50%, #f0f9ff 100%); }
    .block-container { padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1150px; }

    .tc-header {
        background: #fff; border: 1px solid #e2e8f0; border-radius: 16px;
        padding: 26px 30px; margin-bottom: 22px; position: relative; overflow: hidden;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 16px rgba(15,23,42,0.04);
    }
    .tc-header::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, #4f46e5, #7c3aed, #ec4899);
    }
    .tc-header h1 { margin: 0; font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; }
    .tc-header p  { margin: 8px 0 0 0; font-size: 14px; color: #64748b; }

    .tc-card {
        background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
        padding: 20px; margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 16px rgba(15,23,42,0.04);
    }
    .tc-sec { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
    .tc-icon {
        width: 32px; height: 32px; border-radius: 9px;
        background: linear-gradient(135deg, #eef2ff, #e0e7ff);
        display: inline-flex; align-items: center; justify-content: center; font-size: 15px;
    }
    .tc-title { font-size: 14px; font-weight: 700; color: #0f172a; }

    .res-card { border-radius: 16px; padding: 30px 26px; border: 1px solid; }
    .res-card.low    { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-color: #a7f3d0; }
    .res-card.medium { background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-color: #fde68a; }
    .res-card.high   { background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #fecaca; }

    .res-pct { font-size: 68px; font-weight: 800; line-height: 1; letter-spacing: -2px; }
    .res-pct.low    { color: #047857; }
    .res-pct.medium { color: #b45309; }
    .res-pct.high   { color: #b91c1c; }

    .res-label {
        font-size: 12px; font-weight: 700; letter-spacing: 1.5px;
        text-transform: uppercase; color: #64748b; margin-top: 8px;
    }
    .res-bar {
        width: 100%; height: 10px; background: rgba(255,255,255,0.65);
        border-radius: 999px; overflow: hidden; margin: 18px 0 22px;
        border: 1px solid rgba(0,0,0,0.04);
    }
    .res-bar > span { display: block; height: 100%; border-radius: 999px; }
    .res-bar > span.low    { background: linear-gradient(90deg, #10b981, #059669); }
    .res-bar > span.medium { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .res-bar > span.high   { background: linear-gradient(90deg, #ef4444, #dc2626); }

    .res-sub {
        font-size: 11px; font-weight: 700; letter-spacing: 1.3px;
        text-transform: uppercase; color: #64748b; margin-bottom: 10px;
    }
    .res-reasons { list-style: none; margin: 0 0 20px 0; padding: 0; }
    .res-reasons li {
        display: flex; gap: 10px; font-size: 14.5px; color: #0f172a;
        line-height: 1.55; margin-bottom: 8px; font-weight: 500;
    }
    .res-reasons li::before { content: "▸"; color: #4f46e5; font-weight: 700; flex-shrink: 0; }
    .res-action {
        background: rgba(255,255,255,0.75); border-left: 3px solid #4f46e5;
        padding: 14px 16px; border-radius: 8px;
        font-size: 14px; color: #0f172a; font-weight: 600; line-height: 1.5;
    }
    .res-mode {
        display: inline-block; font-size: 11px; font-weight: 600;
        padding: 3px 10px; border-radius: 999px; margin-top: 14px;
    }
    .res-mode.ai      { background: #eef2ff; color: #4f46e5; }
    .res-mode.offline { background: #fef3c7; color: #b45309; }

    .tc-muted { color: #64748b; font-size: 12px; line-height: 1.5; }

    /* Text area */
    .stTextArea textarea {
        background: #f8fafc !important; color: #0f172a !important;
        border: 1.5px solid #e2e8f0 !important; border-radius: 10px !important;
        font-size: 13.5px !important; line-height: 1.6 !important;
    }
    .stTextArea textarea:focus {
        border-color: #4f46e5 !important; background: #fff !important;
        box-shadow: 0 0 0 3px rgba(79,70,229,0.1) !important;
    }
    .stTextArea textarea::placeholder { color: #94a3b8 !important; }

    /* File uploader */
    [data-testid="stFileUploaderDropzone"] {
        background: #f8fafc !important; border: 2px dashed #cbd5e1 !important;
        border-radius: 12px !important; padding: 12px !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: #4f46e5 !important; }
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] p { color: #64748b !important; }
    [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploaderFileName"] *,
    div[data-testid="stFileUploaderFileName"] span,
    div[data-testid="stFileUploaderFileName"] small {
        color: #0f172a !important; font-weight: 600 !important; opacity: 1 !important;
    }
    [data-testid="stFileUploaderDeleteBtn"] button,
    [data-testid="stFileUploaderDeleteBtn"] svg {
        color: #0f172a !important; fill: #0f172a !important; opacity: 0.7 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: #eef2ff !important; color: #4f46e5 !important;
        border: 1px solid #c7d2fe !important; font-weight: 600 !important;
    }

    /* Primary button */
    .stButton button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        color: #fff !important; border: none !important; border-radius: 10px !important;
        font-weight: 700 !important; padding: 12px !important; font-size: 14.5px !important;
        box-shadow: 0 4px 12px rgba(79,70,229,0.25) !important;
    }
    .stButton button:hover { box-shadow: 0 6px 18px rgba(79,70,229,0.35) !important; }

    /* Info cards */
    .info-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 24px; }
    @media (max-width: 900px) { .info-row { grid-template-columns: repeat(2, 1fr); } }
    .info-item {
        background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 18px; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    }
    .info-icon { font-size: 22px; margin-bottom: 10px; }
    .info-title { font-size: 13.5px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
    .info-text { font-size: 12.5px; color: #64748b; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def _section(icon: str, title: str) -> str:
    return (
        f'<div class="tc-sec">'
        f'<span class="tc-icon">{icon}</span>'
        f'<span class="tc-title">{title}</span>'
        f'</div>'
    )


def _render_result(result: dict) -> None:
    pct = int(result.get("risk_percent", 0))
    level = str(result.get("risk_level", "Low")).lower()
    if level not in ("low", "medium", "high"):
        level = "low"

    reasons = result.get("reasons", []) or []
    reasons_html = "".join(f"<li>{r}</li>" for r in reasons)
    action = result.get("action", "Read the full document before signing.")
    mode = result.get("mode", "ai")
    mode_label = "⚡ Live AI" if mode == "ai" else "🔌 Offline"

    st.markdown(
        f'<div class="res-card {level}">'
        f'<div class="res-pct {level}">{pct}%</div>'
        f'<div class="res-label">{level.upper()} RISK</div>'
        f'<div class="res-bar"><span class="{level}" style="width:{pct}%"></span></div>'
        f'<div class="res-sub">Why</div>'
        f'<ul class="res-reasons">{reasons_html}</ul>'
        f'<div class="res-sub">What to do</div>'
        f'<div class="res-action">{action}</div>'
        f'<div><span class="res-mode {mode}">{mode_label}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="tc-header">'
    '<h1>📜 TC Sarthi</h1>'
    '<p>Paste or upload a Terms &amp; Conditions document. '
    'Get a risk score, the real reasons, and what to do — in seconds, in plain English.</p>'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# HORIZONTAL INPUT — paste | upload
# ─────────────────────────────────────────────────────────────
col_paste, col_file = st.columns(2, gap="large")

with col_paste:
    st.markdown(
        '<div class="tc-card">' + _section("✍️", "Paste text") + '</div>',
        unsafe_allow_html=True,
    )
    pasted_text = st.text_area(
        "paste",
        height=200,
        max_chars=MAX_PASTE_CHARS,
        placeholder="Paste the full T&C here...",
        label_visibility="collapsed",
    )

with col_file:
    st.markdown(
        '<div class="tc-card">' + _section("📥", "Upload .txt file") + '</div>',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "upload",
        type=["txt"],
        accept_multiple_files=False,
        help=f"Only .txt files under {MAX_FILE_KB} KB.",
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        kb = uploaded_file.size / 1024
        if uploaded_file.size > MAX_FILE_BYTES:
            st.error(f"Too large: {kb:.1f} KB — max {MAX_FILE_KB} KB.")
        else:
            st.success(f"✓ {uploaded_file.name} · {kb:.1f} KB")


# ─────────────────────────────────────────────────────────────
# ANALYZE button
# ─────────────────────────────────────────────────────────────
analyze_clicked = st.button("🚀 Analyze", use_container_width=True, type="primary")

st.markdown(
    f'<div class="tc-muted" style="text-align:center; margin:6px 0 20px 0;">'
    f'If both are given, the pasted text wins · Limits: {MAX_PASTE_CHARS:,} chars / {MAX_FILE_KB} KB'
    f'</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# OUTPUT — full width, below
# ─────────────────────────────────────────────────────────────
if analyze_clicked:
    text_to_analyze = ""
    source = ""

    if pasted_text and pasted_text.strip():
        text_to_analyze = pasted_text.strip()
        source = "pasted text"
    elif uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_BYTES:
            st.error(f"File too large. Max {MAX_FILE_KB} KB.")
        else:
            try:
                raw = uploaded_file.getvalue()
                if not raw:
                    st.error("The file is empty.")
                else:
                    try:
                        text_to_analyze = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        text_to_analyze = raw.decode("latin-1", errors="ignore")
                    text_to_analyze = text_to_analyze.strip()
                    source = uploaded_file.name
                    if not text_to_analyze:
                        st.error("The file has no readable text.")
            except Exception as e:
                st.error(f"Could not read file: {e}")

    if not text_to_analyze:
        st.warning("Please paste some text or upload a .txt file first.")
    else:
        with st.spinner("Analyzing..."):
            try:
                st.session_state["last_result"] = _analyze_cached(text_to_analyze)
                st.session_state["last_source"] = source
            except Exception as e:
                st.session_state["last_result"] = None
                st.error(f"Analysis failed: {e}")

last = st.session_state.get("last_result")
if last:
    _render_result(last)
    src = st.session_state.get("last_source", "")
    if src:
        st.markdown(
            f'<div class="tc-muted" style="text-align:center; margin-top:8px;">'
            f'Analyzed: {src}</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="tc-card" style="text-align:center; padding:56px 20px;">'
        '<div style="font-size:42px; opacity:0.55; margin-bottom:12px;">📄</div>'
        '<div style="font-size:15px; font-weight:600; color:#0f172a; margin-bottom:6px;">'
        'Your analysis will appear here'
        '</div>'
        '<div class="tc-muted">Paste text or upload a .txt file, then hit Analyze.</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# INFO row with emojis
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="info-row">'
    '<div class="info-item">'
    '<div class="info-icon">⚡</div>'
    '<div class="info-title">Fast</div>'
    '<div class="info-text">Results in 2–3 seconds. No 20-minute reading.</div>'
    '</div>'
    '<div class="info-item">'
    '<div class="info-icon">🔒</div>'
    '<div class="info-title">Private</div>'
    '<div class="info-text">Your text is never stored. Analyzed and discarded.</div>'
    '</div>'
    '<div class="info-item">'
    '<div class="info-icon">🎯</div>'
    '<div class="info-title">Accurate</div>'
    '<div class="info-text">Money, Privacy, Data, Rights — all four risk areas.</div>'
    '</div>'
    '<div class="info-item">'
    '<div class="info-icon">💡</div>'
    '<div class="info-title">Clear</div>'
    '<div class="info-text">Plain English. A 15-year-old can understand the output.</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)