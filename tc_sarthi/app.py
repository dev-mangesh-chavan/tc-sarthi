"""
app.py — Streamlit UI for TC Sarthi.

Layout:
    Header (full width)
    ┌──────────────────────┬───────────────────────────────┐
    │  LEFT: input         │  RIGHT: result                │
    └──────────────────────┴───────────────────────────────┘

Theme:
    Dark grey background. Cards slightly lighter.
    Icon chips, risk meter, coloured verdict block.

IMPORTANT:
    All HTML is written as ONE-LINE strings with no indentation.
    Streamlit treats 4+ leading spaces as a code block, which
    makes raw HTML show up as text instead of rendering it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from tc_sarthi.agent import run


# ─────────────────────────────────────────────────────────────
# Page config — first Streamlit call.
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TC Sarthi",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─────────────────────────────────────────────────────────────
# Dark theme CSS.
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0b0e13;
            color: #e6e8eb;
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        /* ── Header ───────────────────────────────────────── */
        .tc-header {
            background: linear-gradient(135deg, #111827 0%, #1a2332 100%);
            border: 1px solid #1f2937;
            border-left: 4px solid #4aa3ff;
            padding: 20px 26px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .tc-header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            color: #f5f7fa;
            letter-spacing: 0.2px;
        }
        .tc-header p {
            margin: 6px 0 0 0;
            font-size: 13.5px;
            color: #9aa3af;
            line-height: 1.5;
        }
        .tc-badge-live {
            display: inline-block;
            background: #0f2d1f;
            color: #6ee7a6;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 999px;
            margin-left: 8px;
            vertical-align: middle;
        }

        /* ── Card ─────────────────────────────────────────── */
        .tc-card {
            background: #12161d;
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 16px 18px;
            margin-bottom: 12px;
        }

        /* ── Section title with icon chip ─────────────────── */
        .tc-sec {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }
        .tc-chip {
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
        }
        .tc-chip-blue   { background: #10243d; }
        .tc-chip-amber  { background: #2d2110; }
        .tc-chip-green  { background: #10291c; }
        .tc-title {
            font-size: 14.5px;
            font-weight: 700;
            color: #e6e8eb;
            letter-spacing: 0.2px;
        }

        /* ── Main points list ─────────────────────────────── */
        .tc-points { margin: 0; padding: 0; list-style: none; }
        .tc-points li {
            display: flex;
            gap: 10px;
            font-size: 13.5px;
            color: #cfd3d8;
            line-height: 1.55;
            margin-bottom: 8px;
        }
        .tc-points li::before {
            content: "▸";
            color: #4aa3ff;
            font-weight: 700;
            flex-shrink: 0;
        }

        /* ── Risk card ────────────────────────────────────── */
        .risk-card {
            background: #12161d;
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }
        .risk-card.low    { border-left: 4px solid #22c55e; }
        .risk-card.medium { border-left: 4px solid #f59e0b; }
        .risk-card.high   { border-left: 4px solid #ef4444; }

        .risk-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .risk-name {
            display: flex;
            align-items: center;
            gap: 9px;
            font-size: 13.5px;
            font-weight: 700;
            color: #e6e8eb;
        }
        .risk-icon {
            width: 26px; height: 26px;
            border-radius: 7px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        .risk-icon.low    { background: #0f2d1f; }
        .risk-icon.medium { background: #2d2110; }
        .risk-icon.high   { background: #2d1010; }

        .risk-body {
            font-size: 13px;
            color: #b8bec7;
            line-height: 1.55;
        }

        /* ── Pill badge ───────────────────────────────────── */
        .pill {
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            padding: 3px 10px;
            border-radius: 999px;
        }
        .pill.low    { background: #0f2d1f; color: #6ee7a6; }
        .pill.medium { background: #2d2110; color: #fcd34d; }
        .pill.high   { background: #2d1010; color: #fca5a5; }

        /* ── Risk meter bar ───────────────────────────────── */
        .meter {
            width: 100%;
            height: 6px;
            background: #1a1f28;
            border-radius: 999px;
            overflow: hidden;
            margin-top: 4px;
        }
        .meter > span {
            display: block;
            height: 100%;
            border-radius: 999px;
        }
        .meter > span.low    { width: 33%;  background: #22c55e; }
        .meter > span.medium { width: 66%;  background: #f59e0b; }
        .meter > span.high   { width: 100%; background: #ef4444; }

        /* ── Verdict ──────────────────────────────────────── */
        .verdict {
            border-radius: 12px;
            padding: 18px 20px;
            margin-top: 6px;
        }
        .verdict.low {
            background: linear-gradient(135deg, #0f2d1f 0%, #10291c 100%);
            border: 1px solid #166534;
        }
        .verdict.medium {
            background: linear-gradient(135deg, #2d2110 0%, #2a1e0d 100%);
            border: 1px solid #a16207;
        }
        .verdict.high {
            background: linear-gradient(135deg, #2d1010 0%, #2a0d0d 100%);
            border: 1px solid #991b1b;
        }
        .verdict-label {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            color: #9aa3af;
        }
        .verdict-level {
            font-size: 22px;
            font-weight: 800;
            margin-top: 4px;
            letter-spacing: 0.4px;
        }
        .verdict.low    .verdict-level { color: #6ee7a6; }
        .verdict.medium .verdict-level { color: #fcd34d; }
        .verdict.high   .verdict-level { color: #fca5a5; }
        .verdict-msg {
            font-size: 13.5px;
            color: #d1d5db;
            line-height: 1.6;
            margin-top: 8px;
        }

        /* ── Meta footer ──────────────────────────────────── */
        .tc-meta {
            color: #6b7280;
            font-size: 11.5px;
            margin-top: 12px;
            letter-spacing: 0.3px;
        }
        .tc-meta b { color: #9aa3af; }

        /* ── Muted text ───────────────────────────────────── */
        .tc-muted { color: #6b7280; font-size: 12px; line-height: 1.5; }

        /* ── Dark inputs ──────────────────────────────────── */
        .stTextArea textarea,
        .stTextInput input {
            background-color: #0f1319 !important;
            color: #e6e8eb !important;
            border: 1px solid #1f2937 !important;
            border-radius: 8px !important;
        }
        .stTextArea textarea::placeholder {
            color: #4b5563 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            background-color: #0f1319 !important;
            border: 1px dashed #1f2937 !important;
            border-radius: 8px !important;
        }
        [data-testid="stFileUploaderDropzone"] * {
            color: #9aa3af !important;
        }
        .stButton button {
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# Small helpers for one-line HTML.
# NOTE: no leading whitespace — that's what broke rendering.
# ─────────────────────────────────────────────────────────────
def _pill(level: str) -> str:
    level = (level or "low").lower()
    if level not in ("low", "medium", "high"):
        level = "low"
    return f'<span class="pill {level}">{level}</span>'


def _section_header(icon: str, chip_class: str, title: str) -> str:
    return (
        f'<div class="tc-sec">'
        f'<span class="tc-chip {chip_class}">{icon}</span>'
        f'<span class="tc-title">{title}</span>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="tc-header">'
    '<h1>📜 TC Sarthi <span class="tc-badge-live">● live</span></h1>'
    '<p>Paste or upload a Terms &amp; Conditions document. '
    'Get the important facts, risky clauses, and a clear verdict — in seconds.</p>'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# Two columns
# ─────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.15], gap="large")


# ─────────────────────────────────────────────────────────────
# Render the final result. Every markdown call is ONE line of HTML.
# ─────────────────────────────────────────────────────────────
def _render_result(result: dict) -> None:

    # ── Main points ───────────────────────────────────────────
    points = result.get("main_points", []) or []
    points_html = "".join(f"<li>{p}</li>" for p in points)
    st.markdown(
        '<div class="tc-card">'
        + _section_header("🔎", "tc-chip-blue", "Main Points")
        + f'<ul class="tc-points">{points_html}</ul>'
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Risk areas ────────────────────────────────────────────
    labels = [
        ("money",   "💰", "Money"),
        ("privacy", "🔒", "Privacy"),
        ("data",    "📦", "Data"),
        ("rights",  "⚖️", "Rights"),
    ]

    risk_html = ""
    for key, icon, label in labels:
        area = result.get("risk_areas", {}).get(key, {}) or {}
        level = (area.get("level") or "low").lower()
        if level not in ("low", "medium", "high"):
            level = "low"
        summary = area.get("summary", "—")

        risk_html += (
            f'<div class="risk-card {level}">'
            f'<div class="risk-head">'
            f'<div class="risk-name">'
            f'<span class="risk-icon {level}">{icon}</span>'
            f'{label}'
            f'</div>'
            f'{_pill(level)}'
            f'</div>'
            f'<div class="risk-body">{summary}</div>'
            f'<div class="meter"><span class="{level}"></span></div>'
            f'</div>'
        )

    st.markdown(
        _section_header("⚠️", "tc-chip-amber", "Risk Areas") + risk_html,
        unsafe_allow_html=True,
    )

    # ── Verdict ───────────────────────────────────────────────
    verdict = result.get("verdict", {}) or {}
    v_level = (verdict.get("level") or "low").lower()
    if v_level not in ("low", "medium", "high"):
        v_level = "low"
    v_msg = verdict.get("message", "—")

    st.markdown(
        f'<div class="verdict {v_level}">'
        f'<div class="verdict-label">Final Verdict</div>'
        f'<div class="verdict-level">{v_level.upper()} RISK</div>'
        f'<div class="verdict-msg">{v_msg}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Meta footer ───────────────────────────────────────────
    meta = result.get("meta", {}) or {}
    st.markdown(
        f'<div class="tc-meta">'
        f'Provider <b>{meta.get("provider", "—")}</b>'
        f' &nbsp;·&nbsp; Words <b>{meta.get("word_count", 0)}</b>'
        f' &nbsp;·&nbsp; Sections <b>{meta.get("section_count", 0)}</b>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# LEFT COLUMN — input
# ─────────────────────────────────────────────────────────────
with left_col:
    st.markdown(
        '<div class="tc-card">'
        + _section_header("📥", "tc-chip-blue", "Input")
        + '</div>',
        unsafe_allow_html=True,
    )

    pasted_text = st.text_area(
        "Paste Terms & Conditions text",
        height=240,
        placeholder="Paste the full T&C here...",
    )

    st.markdown(
        '<div style="text-align:center; color:#4b5563; font-size:11.5px; margin:6px 0; letter-spacing:2px;">— OR —</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload a .txt file",
        type=["txt"],
        accept_multiple_files=False,
    )

    analyze_clicked = st.button(
        "🚀 Analyze",
        use_container_width=True,
        type="primary",
    )

    st.markdown(
        '<div class="tc-muted" style="margin-top:6px;">'
        'Tip: if both a file and text are given, the pasted text wins.'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Decide input source. Pasted text wins.
# ─────────────────────────────────────────────────────────────
final_text = ""
if pasted_text and pasted_text.strip():
    final_text = pasted_text.strip()
elif uploaded_file is not None:
    try:
        final_text = uploaded_file.read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        st.error(f"Could not read the file: {e}")


# ─────────────────────────────────────────────────────────────
# RIGHT COLUMN — output
# ─────────────────────────────────────────────────────────────
with right_col:
    if analyze_clicked:
        if not final_text:
            st.warning("Please paste some text or upload a .txt file first.")
        else:
            with st.spinner("Analyzing the document..."):
                try:
                    st.session_state["last_result"] = run(final_text)
                except Exception as e:
                    st.session_state["last_result"] = None
                    st.error(f"Analysis failed: {e}")

    last = st.session_state.get("last_result")
    if last:
        _render_result(last)
    else:
        st.markdown(
            '<div class="tc-card" style="text-align:center; padding:44px 20px;">'
            '<div style="font-size:38px; opacity:0.7;">📄</div>'
            '<div style="font-size:14px; font-weight:600; margin-top:8px; color:#e6e8eb;">'
            'Your analysis will appear here'
            '</div>'
            '<div class="tc-muted" style="margin-top:6px;">'
            'Paste or upload a T&amp;C, then hit Analyze.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )