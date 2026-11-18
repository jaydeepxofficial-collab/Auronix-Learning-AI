"""Auronix learningAI V2 — Streamlit single-file learning platform.

Secrets (Streamlit secrets or environment variables):
  GEMINI_API_KEY = "..."
  GROQ_API_KEY = "..."
"""
from __future__ import annotations

import concurrent.futures
import html
import json
import os
import re
import sqlite3
import textwrap
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import streamlit as st

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None

try:
    from groq import Groq
except Exception:
    Groq = None

try:
    from google import genai
except Exception:
    genai = None

try:
    import bleach
except Exception:
    bleach = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Preformatted, KeepTogether
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# ----------------------------- Configuration -----------------------------
st.set_page_config(page_title="Auronix learningAI V2", page_icon="🦁", layout="centered")

APP_VERSION = "2.0.0"
MAX_INPUT_CHARS = 18_000
MAX_NOTES_CHARS = 24_000
MAX_TRANSCRIPT_CHARS = 45_000

# ⚡ FIXED REAL MODELS: Llama 3.3, Gemma 2, and Gemini 1.5 Flash
GROQ_PRIMARY_MODEL = os.getenv("AURONIX_GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_SECONDARY_MODEL = os.getenv("AURONIX_GROQ_SECONDARY_MODEL", "gemma2-9b-it")
GEMINI_MODEL = os.getenv("AURONIX_GEMINI_MODEL", "gemini-1.5-flash")
DB_PATH = os.getenv("AURONIX_DB_PATH", "auronix.db")

def get_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, "")).strip()

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# ----------------------------- Styling (With EMO Mobile Fix) --------------
st.markdown("""
<style>
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
.block-container {padding-top:1.4rem; padding-bottom:5rem; max-width:1050px;}
.auronix-hero {background:linear-gradient(135deg,rgba(255,165,0,.16),rgba(255,94,0,.055));border:1px solid rgba(255,165,0,.38);border-radius:20px;padding:23px 20px;margin-bottom:22px;box-shadow:0 8px 28px rgba(255,140,0,.09);text-align:center;}
.auronix-title {background:linear-gradient(90deg,#FFB300,#FF6F00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:clamp(2rem,6vw,2.65rem);font-weight:950;margin:0;line-height:1.15;}
.auronix-badge {display:inline-block;background:rgba(255,165,0,.16);color:#FFB300;font-size:12px;font-weight:750;padding:6px 14px;border-radius:20px;margin-top:10px;border:1px solid rgba(255,165,0,.32);}
div.stButton>button,div.stDownloadButton>button {background:linear-gradient(90deg,#FF9800,#F57C00)!important;color:white!important;font-weight:750!important;border:0!important;border-radius:12px!important;box-shadow:0 4px 14px rgba(255,152,0,.25)!important;}
div.stButton>button:hover,div.stDownloadButton>button:hover {transform:translateY(-1px);box-shadow:0 6px 18px rgba(255,152,0,.38)!important;}

/* ⚡ MOBILE EMO ROBOT POSITION FIX */
[data-testid="stPopover"] {position:fixed!important;bottom:85px!important;right:20px!important;z-index:99999!important;}
[data-testid="stPopover"]>button {width:74px!important;height:64px!important;background:radial-gradient(circle at 50% 30%,#333 0%,#050505 80%)!important;border:4px solid #9CA3AF!important;border-radius:22px!important;padding:0!important;color:transparent!important;box-shadow:-9px 0 0 -2px #5B21B6,9px 0 0 -2px #5B21B6,0 10px 25px rgba(0,0,0,.5)!important;animation:robotFloat 3.5s ease-in-out infinite!important;}
[data-testid="stPopover"]>button p {display:none!important;}
[data-testid="stPopover"]>button:before,[data-testid="stPopover"]>button:after {content:''!important;position:absolute!important;top:22px!important;width:14px!important;height:12px!important;background:#00E5FF!important;border-radius:4px!important;box-shadow:0 0 10px #00E5FF,0 0 18px #00E5FF!important;animation:eyeBlink 4s infinite!important;}
[data-testid="stPopover"]>button:before {left:15px!important;} [data-testid="stPopover"]>button:after {right:15px!important;}
[data-testid="stPopover"]>button:hover {transform:scale(1.07) translateY(-4px)!important;}
[data-testid="stPopover"]:before {content:"Ask Doubt! ✨";position:absolute;top:-39px;left:50%;transform:translateX(-50%);background:white;color:#111827;padding:5px 11px;border-radius:12px;font-size:12px;font-weight:800;white-space:nowrap;opacity:0;transition:.25s;pointer-events:none;}
[data-testid="stPopover"]:hover:before {opacity:1;top:-45px;}
@keyframes robotFloat {0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes eyeBlink {0%,94%,98%,100%{height:12px}96%{height:2px;transform:translateY(4px)}}
@media(max-width:600px){
    .block-container{padding-left:1rem;padding-right:1rem;}
    [data-testid="stPopover"]{right:15px!important;bottom:85px!important;}
}
</style>
""", unsafe_allow_html=True)

engine_label = "🧠 Groq + Gemini Parallel Fusion" if GROQ_API_KEY and GEMINI_API_KEY else (
    "⚡ Groq AI" if GROQ_API_KEY else ("✨ Gemini AI" if GEMINI_API_KEY else "🔑 Add API keys to activate AI")
)
st.markdown(f"""
<div class="auronix-hero">
  <div class="auronix-title">🦁 Auronix learningAI</div>
  <p style="color:#B0B8C4;font-size:15px;margin:9px 0 0">AI-powered exam notes, formula sheets, practice tests & smart revision.</p>
  <div class="auronix-badge">{html.escape(engine_label)} · V{APP_VERSION}</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Database -----------------------------------
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with db_connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            topic TEXT NOT NULL,
            score REAL,
            total INTEGER,
            details TEXT
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_session ON activity(session_id, created_at)")

def log_activity(activity_type: str, topic: str, score: Optional[float] = None,
                 total: Optional[int] = None, details: str = "") -> None:
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO activity(session_id,created_at,activity_type,topic,score,total,details) VALUES(?,?,?,?,?,?,?)",
            (st.session_state.session_id, datetime.now(timezone.utc).isoformat(),
             activity_type[:40], topic[:180], score, total, details[:1000])
        )

def get_activity() -> list[sqlite3.Row]:
    with db_connect() as conn:
        return conn.execute(
            "SELECT * FROM activity WHERE session_id=? ORDER BY id DESC LIMIT 100",
            (st.session_state.session_id,)
        ).fetchall()

init_db()

# ----------------------------- Session state ------------------------------
DEFAULTS = {
    "study_notes": "", "topic_context": "", "lang_saved": "English (Exam Ready)",
    "quiz_data": None, "quiz_submitted": False, "qa_output": "", "buddy_chat": [],
    "flashcards": [], "flashcards_topic": "", "exam_started": False,
    "exam_start_time": None, "session_id": str(uuid.uuid4()), "active_topic": "",
    "last_quiz_score": None, "last_quiz_total": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ----------------------------- Helpers ------------------------------------
def get_video_id(url: str) -> Optional[str]:
    patterns = [r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id: str) -> Optional[str]:
    if YouTubeTranscriptApi is None:
        raise RuntimeError("YouTube transcript package is missing. Install youtube-transcript-api.")
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=["hi", "en", "en-IN"])
        text = " ".join(segment.text for segment in fetched)
        return text[:MAX_TRANSCRIPT_CHARS] if text.strip() else None
    except Exception as exc:
        st.session_state.transcript_error = type(exc).__name__
        return None

def strip_marker(text: str, marker: str) -> str:
    text = (text or "").strip()
    if marker in text:
        text = text.split(marker, 1)[1].strip()
    text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.I | re.S).strip()
    return text

def groq_generate(prompt: str, model: str = GROQ_PRIMARY_MODEL, json_mode: bool = False,
                  max_tokens: int = 6000) -> Optional[str]:
    if not GROQ_API_KEY or Groq is None:
        return None
    try:
        client = Groq(api_key=GROQ_API_KEY, timeout=75, max_retries=1)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are Auronix learningAI, a precise and helpful JEE/NEET educator. Do not reveal private reasoning."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.25,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        result = client.chat.completions.create(**kwargs)
        content = result.choices[0].message.content
        return content.strip() if content else None
    except Exception:
        return None

def gemini_generate(prompt: str, json_mode: bool = False, max_tokens: int = 6000) -> Optional[str]:
    if not GEMINI_API_KEY or genai is None:
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        config: dict[str, Any] = {"temperature": 0.25, "max_output_tokens": max_tokens}
        if json_mode:
            config["response_mime_type"] = "application/json"
        response = client.models.generate_content(
            model=GEMINI_MODEL, contents=prompt, config=config
        )
        output = getattr(response, "text", None)
        return output.strip() if output else None
    except Exception:
        return None

def generate_ai(prompt: str, mode: str = "notes", json_mode: bool = False) -> tuple[Optional[str], Optional[str]]:
    if not GROQ_API_KEY and not GEMINI_API_KEY:
        return None, "API keys are not configured. Add GROQ_API_KEY and/or GEMINI_API_KEY in Streamlit secrets."

    if mode == "notes" and GROQ_API_KEY and GEMINI_API_KEY:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f_groq = pool.submit(groq_generate, prompt, GROQ_PRIMARY_MODEL, False, 6500)
            f_gemini = pool.submit(gemini_generate, prompt, False, 6500)
            groq_out, gemini_out = f_groq.result(), f_gemini.result()
        candidates = [x for x in [groq_out, gemini_out] if x]
        if len(candidates) == 2:
            fusion_prompt = f"""You are the Auronix master editor. Combine these two independent educational drafts into one accurate, coherent, non-repetitive exam guide. Resolve contradictions carefully; do not invent facts. Preserve useful derivations, units, examples and exam traps. If a claim is uncertain, label it for verification.\n\nDRAFT A:\n{candidates[0][:15000]}\n\nDRAFT B:\n{candidates[1][:15000]}\n\nReturn only the final study guide in clean Markdown."""
            fused = groq_generate(fusion_prompt, GROQ_PRIMARY_MODEL, False, 7500)
            if fused:
                return fused[:MAX_NOTES_CHARS], None
            return max(candidates, key=len)[:MAX_NOTES_CHARS], None
        if len(candidates) == 1:
            return candidates[0][:MAX_NOTES_CHARS], None
        return None, "Both AI providers are temporarily unavailable. Please retry shortly."

    if GROQ_API_KEY:
        result = groq_generate(prompt, GROQ_PRIMARY_MODEL, json_mode)
        if result:
            return result, None
    if GEMINI_API_KEY:
        result = gemini_generate(prompt, json_mode)
        if result:
            return result, None
    if GROQ_API_KEY:
        result = groq_generate(prompt, GROQ_SECONDARY_MODEL, json_mode)
        if result:
            return result, None
    return None, "AI providers could not complete this request. Check model availability, quota and API keys."

def parse_json_object(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?|```", "", raw or "", flags=re.I).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object found")
    data = json.loads(cleaned[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("JSON response must be an object")
    return data

def safe_markdown_html(markdown_text: str) -> str:
    try:
        import markdown as md
        rendered = md.markdown(markdown_text, extensions=["extra", "sane_lists", "tables"])
    except Exception:
        rendered = "<pre>" + html.escape(markdown_text) + "</pre>"
    if bleach is not None:
        allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS) | {
            "p", "h1", "h2", "h3", "h4", "hr", "br", "pre", "code", "blockquote",
            "table", "thead", "tbody", "tr", "th", "td", "ul", "ol", "li", "strong", "em"
        }
        allowed_attrs = {"a": ["href", "title", "rel"], "th": ["align"], "td": ["align"]}
        rendered = bleach.clean(rendered, tags=allowed_tags, attributes=allowed_attrs,
                                protocols=["http", "https", "mailto"], strip=True)
    else:
        rendered = "<pre>" + html.escape(markdown_text) + "</pre>"
    return rendered

def make_html_download(markdown_text: str, title: str) -> str:
    safe_title = html.escape(title)
    body = safe_markdown_html(markdown_text)
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>{safe_title}</title>
<style>body{{font:16px/1.7 system-ui,Arial;max-width:900px;margin:30px auto;padding:0 18px;background:#f6f7f9;color:#243041}}main{{background:white;padding:35px;border-radius:14px;box-shadow:0 5px 24px #0001}}h1,h2,h3{{color:#b45309}}pre,code{{background:#f3f4f6;padding:3px 6px;border-radius:5px;overflow-wrap:anywhere}}pre{{padding:14px;overflow:auto}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px}}.print{{display:block;margin:0 auto 18px;padding:11px 18px;background:#e67e22;color:white;border:0;border-radius:24px;font-weight:bold}}@media print{{body{{background:white;margin:0}}main{{box-shadow:none;padding:0}}.print{{display:none}}}}</style></head>
<body><button class='print' onclick='window.print()'>🖨️ Print / Save as PDF</button><main><h1>{safe_title}</h1>{body}<hr><p style='text-align:center;color:#7b8490'>Generated by Auronix learningAI</p></main></body></html>"""

def make_pdf(markdown_text: str, title: str) -> bytes:
    if not REPORTLAB_OK:
        raise RuntimeError("PDF support is not installed.")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=17*mm, bottomMargin=17*mm, title=title)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="AuronixTitle", parent=styles["Title"], textColor=colors.HexColor("#D97706"), alignment=TA_CENTER, spaceAfter=16))
    styles.add(ParagraphStyle(name="AuronixH2", parent=styles["Heading2"], textColor=colors.HexColor("#B45309"), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="AuronixBody", parent=styles["BodyText"], leading=15, spaceAfter=6))
    story: list[Any] = [Paragraph(html.escape(title), styles["AuronixTitle"])]
    in_code = False
    code_lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["Code"]))
                story.append(Spacer(1, 6))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            story.append(Spacer(1, 4))
            continue
        if line.startswith("### "):
            story.append(Paragraph(html.escape(line[4:]), styles["Heading3"]))
        elif line.startswith("## "):
            story.append(Paragraph(html.escape(line[3:]), styles["AuronixH2"]))
        elif line.startswith("# "):
            story.append(Paragraph(html.escape(line[2:]), styles["Heading1"]))
        elif re.match(r"^\s*[-*]\s+", line):
            text = re.sub(r"^\s*[-*]\s+", "", line)
            story.append(Paragraph("• " + html.escape(text), styles["AuronixBody"]))
        elif re.match(r"^\s*\d+[.)]\s+", line):
            story.append(Paragraph(html.escape(line), styles["AuronixBody"]))
        elif line.startswith("> "):
            story.append(Paragraph("<i>" + html.escape(line[2:]) + "</i>", styles["AuronixBody"]))
        else:
            clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html.escape(line))
            clean = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", clean)
            story.append(Paragraph(clean, styles["AuronixBody"]))
    if in_code and code_lines:
        story.append(Preformatted("\n".join(code_lines), styles["Code"]))
    doc.build(story)
    return buffer.getvalue()

def reset_study_state() -> None:
    st.session_state.quiz_data = None
    st.session_state.quiz_submitted = False
    st.session_state.qa_output = ""
    st.session_state.buddy_chat = []
    st.session_state.flashcards = []
    st.session_state.last_quiz_score = None

# ----------------------------- Sidebar / Dashboard -----------------------
with st.sidebar:
    st.markdown("## 🦁 Auronix Menu")
    page = st.radio("Navigate", ["Study Studio", "Student Dashboard", "About & Setup"], label_visibility="collapsed")
    st.divider()
    st.caption("AI provider status")
    st.write("Groq:", "🟢 Connected" if GROQ_API_KEY else "⚪ Not configured")
    st.write("Gemini:", "🟢 Connected" if GEMINI_API_KEY else "⚪ Not configured")

if page == "About & Setup":
    st.subheader("⚙️ Setup Auronix learningAI V2")
    st.markdown("""
**1. Install packages**
```bash
pip install -r requirements.txt
