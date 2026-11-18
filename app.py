"""Auronix learningAI V2 — Streamlit single-file learning platform."""
from __future__ import annotations

import concurrent.futures
import html
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from io import BytesIO
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

st.set_page_config(page_title="Auronix learningAI V2", page_icon="🦁", layout="centered")

APP_VERSION = "2.0.0"
MAX_INPUT_CHARS = 18_000
MAX_NOTES_CHARS = 24_000
MAX_TRANSCRIPT_CHARS = 45_000

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

st.markdown("""
<style>
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
.block-container {padding-top:1.4rem; padding-bottom:5rem; max-width:1050px;}
.auronix-hero {background:linear-gradient(135deg,rgba(255,165,0,.16),rgba(255,94,0,.055));border:1px solid rgba(255,165,0,.38);border-radius:20px;padding:23px 20px;margin-bottom:22px;box-shadow:0 8px 28px rgba(255,140,0,.09);text-align:center;}
.auronix-title {background:linear-gradient(90deg,#FFB300,#FF6F00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:clamp(2rem,6vw,2.65rem);font-weight:950;margin:0;line-height:1.15;}
.auronix-badge {display:inline-block;background:rgba(255,165,0,.16);color:#FFB300;font-size:12px;font-weight:750;padding:6px 14px;border-radius:20px;margin-top:10px;border:1px solid rgba(255,165,0,.32);}
div.stButton>button,div.stDownloadButton>button {background:linear-gradient(90deg,#FF9800,#F57C00)!important;color:white!important;font-weight:750!important;border:0!important;border-radius:12px!important;box-shadow:0 4px 14px rgba(255,152,0,.25)!important;}
div.stButton>button:hover,div.stDownloadButton>button:hover {transform:translateY(-1px);box-shadow:0 6px 18px rgba(255,152,0,.38)!important;}
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

def get_video_id(url: str) -> Optional[str]:
    patterns = [r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id: str) -> Optional[str]:
    if YouTubeTranscriptApi is None:
        return None
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=["hi", "en", "en-IN"])
        text = " ".join(segment.text for segment in fetched)
        return text[:MAX_TRANSCRIPT_CHARS] if text.strip() else None
    except Exception:
        return None

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
            fusion_prompt = f"""You are the Auronix master editor. Combine these two independent educational drafts into one accurate, coherent, non-repetitive exam guide. Preserve useful derivations, units, examples and exam traps.\n\nDRAFT A:\n{candidates[0][:15000]}\n\nDRAFT B:\n{candidates[1][:15000]}\n\nReturn only the final study guide in clean Markdown."""
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

with st.sidebar:
    st.markdown("## 🦁 Auronix Menu")
    page = st.radio("Navigate", ["Study Studio", "Student Dashboard", "About & Setup"], label_visibility="collapsed")
    st.divider()
    st.caption("AI provider status")
    st.write("Groq:", "🟢 Connected" if GROQ_API_KEY else "⚪ Not configured")
    st.write("Gemini:", "🟢 Connected" if GEMINI_API_KEY else "⚪ Not configured")

if page == "About & Setup":
    st.subheader("⚙️ Setup Auronix learningAI V2")
    st.write("Both Groq and Gemini APIs are configured via Streamlit Secrets.")
    st.stop()

if page == "Student Dashboard":
    st.subheader("📊 Student Dashboard")
    rows = get_activity()
    quiz_rows = [r for r in rows if r["activity_type"] == "quiz" and r["score"] is not None]
    total_tests = len(quiz_rows)
    avg_pct = sum((r["score"] / r["total"] * 100) for r in quiz_rows if r["total"]) / max(1, len(quiz_rows))
    total_study = sum(1 for r in rows if r["activity_type"] in ("notes", "formula", "explanation"))
    c1, c2, c3 = st.columns(3)
    c1.metric("Tests attempted", total_tests)
    c2.metric("Average score", f"{avg_pct:.1f}%" if quiz_rows else "—")
    c3.metric("Study generations", total_study)
    st.markdown("### Recent activity")
    if rows:
        for r in rows[:20]:
            date_label = r["created_at"].replace("T", " ")[:16]
            suffix = f" · {r['score']}/{r['total']}" if r["score"] is not None else ""
            st.write(f"**{r['activity_type'].title()}** — {r['topic']}{suffix}")
            st.caption(date_label + " UTC")
    else:
        st.info("Your study and test history will appear here after you use Auronix.")
    st.stop()

st.markdown("### 🎓 Your AI Study Studio")
mode = st.radio("1️⃣ Choose input method", ["🔗 YouTube Lecture Link", "📝 Topic Name / Lecture Text"], horizontal=True)
col1, col2 = st.columns(2)
with col1:
    output_type = st.selectbox("2️⃣ What do you want?", [
        "📚 Deep Topper Exam Notes & Formulas",
        "⚡ Complete Formula & Trick Sheet",
        "📖 Zero-to-Pro Detailed Explanation",
    ])
with col2:
    lang_choice = st.selectbox("3️⃣ Explanation language", ["English (Exam Ready)", "Hinglish (Easy Concept Clarity)"])

source_text = ""
source_topic = ""
if mode == "🔗 YouTube Lecture Link":
    youtube_url = st.text_input("🔗 Paste educational YouTube lecture link")
    if st.button("✨ Extract Lecture & Generate", use_container_width=True):
        vid = get_video_id(youtube_url.strip())
        if not vid:
            st.error("Please enter a valid YouTube link.")
        elif not GEMINI_API_KEY and not GROQ_API_KEY:
            st.error("Add at least one AI API key in Streamlit secrets.")
        else:
            with st.spinner("🔍 Fetching available subtitles..."):
                transcript = fetch_transcript(vid)
            if transcript:
                source_text = transcript
                source_topic = f"YouTube lecture {vid}"
            else:
                st.warning("No accessible captions were found. Try pasting lecture text.")
else:
    manual_input = st.text_area("📝 Enter chapter/topic or paste lecture notes", height=130, max_chars=MAX_INPUT_CHARS)
    if st.button("✨ Generate Notes Now", use_container_width=True):
        if not manual_input.strip():
            st.warning("Please enter a topic or lecture text first.")
        elif not GEMINI_API_KEY and not GROQ_API_KEY:
            st.error("Add at least one AI API key in Streamlit secrets.")
        else:
            source_text = manual_input.strip()
            source_topic = source_text[:120].replace("\n", " ")

if source_text:
    reset_study_state()
    st.session_state.topic_context = source_text[:MAX_TRANSCRIPT_CHARS]
    st.session_state.active_topic = source_topic
    st.session_state.lang_saved = lang_choice
    if output_type == "📚 Deep Topper Exam Notes & Formulas":
        task = "Create comprehensive exam-mastery notes with: (1) core concepts and intuition, (2) definitions/laws/theorems, (3) formula bank with SI units, (4) two solved exam-level numericals, (5) JEE/NEET strategy, traps and quick revision."
    elif output_type == "⚡ Complete Formula & Trick Sheet":
        task = "Create a structured formula and trick sheet. Include standard formulas, conditions/assumptions, SI units, 5 useful shortcuts and 5 common exam traps."
    else:
        task = "Teach this topic from zero to advanced applications step by step. Explain prerequisites, concepts, derivations, formulas, examples and common misconceptions."
    prompt = f"You are Auronix learningAI, an accurate JEE/NEET tutor. Language: {lang_choice}. Topic:\n{source_text[:MAX_TRANSCRIPT_CHARS]}\n\nTask: {task}\n\nUse clean Markdown and LaTeX."
    with st.spinner("🧠 Groq + Gemini are preparing your study guide..."):
        notes, error = generate_ai(prompt, mode="notes")
    if notes:
        st.session_state.study_notes = notes[:MAX_NOTES_CHARS]
        st.session_state.active_topic = source_topic
        log_activity("notes", source_topic)
        st.success("Your study guide is ready!")
    else:
        st.error(error or "Could not generate notes.")

if st.session_state.study_notes:
    st.divider()
    st.markdown(st.session_state.study_notes)
    d1, d2 = st.columns(2)
    with d1:
        html_data = make_html_download(st.session_state.study_notes, "Auronix Study Notes")
        st.download_button("⬇️ Download HTML Notes", data=html_data, file_name="Auronix_Study_Notes.html", mime="text/html", use_container_width=True)
    with d2:
        if REPORTLAB_OK:
            try:
                pdf_data = make_pdf(st.session_state.study_notes, "Auronix Study Notes")
                st.download_button("📄 Download PDF Notes", data=pdf_data, file_name="Auronix_Study_Notes.pdf", mime="application/pdf", use_container_width=True)
            except Exception as exc:
                st.caption(f"PDF export unavailable: {type(exc).__name__}")
        else:
            st.caption("Install reportlab to enable PDF downloads.")

    st.divider()
    st.markdown("### 🧠 Create a practice test")
    q1, q2, q3 = st.columns(3)
    with q1:
        num_q = st.selectbox("Questions", [5, 10, 20, 30], index=1)
    with q2:
        exam_type = st.selectbox("Exam mode", ["NEET", "JEE Main", "JEE Advanced", "Practice"])
    with q3:
        diff_level = st.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Mixed"])
    test_format = st.radio("Question format", ["Interactive MCQs", "Subjective Q&A"], horizontal=True)
    if st.button("🚀 Generate Test", use_container_width=True):
        for state_key in list(st.session_state.keys()):
            if state_key.startswith("auronix_q_"):
                del st.session_state[state_key]
        st.session_state.quiz_data = None
        st.session_state.quiz_submitted = False
        st.session_state.qa_output = ""
        if test_format == "Interactive MCQs":
            qprompt = f"Create exactly {num_q} multiple-choice questions for {exam_type}, difficulty {diff_level}, language {st.session_state.lang_saved}, based on:\n{st.session_state.topic_context[:14000]}\nReturn JSON object with key 'questions', array of objects containing q, options (four strings), answer (matches one option), explanation. Return JSON only."
            with st.spinner(f"Preparing {num_q} {exam_type} MCQs..."):
                raw, err = generate_ai(qprompt, mode="quiz", json_mode=True)
            if raw:
                try:
                    obj = parse_json_object(raw)
                    valid = [item for item in obj.get("questions", []) if isinstance(item.get("options"), list) and len(item["options"]) == 4]
                    st.session_state.quiz_data = valid
                except Exception:
                    st.error("Invalid quiz format. Please retry.")
            else:
                st.error(err or "Quiz generation failed.")
        else:
            qprompt = f"Create exactly {num_q} subjective questions with step-by-step model answers for {exam_type}, difficulty {diff_level}, language {st.session_state.lang_saved}. Base on:\n{st.session_state.topic_context[:14000]}\nUse clean Markdown and label Q1, Q2 etc."
            with st.spinner("Preparing written questions..."):
                answer, err = generate_ai(qprompt, mode="qa")
            if answer:
                st.session_state.qa_output = answer

    if st.session_state.quiz_data:
        st.markdown(f"#### 📝 Live Test · {len(st.session_state.quiz_data)} questions")
        marks_per_correct = 4 if exam_type in ("NEET", "JEE Main", "JEE Advanced") else 1
        marks_per_wrong = 1 if exam_type in ("NEET", "JEE Main", "JEE Advanced") else 0
        with st.form("auronix_quiz_form"):
            for idx, item in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{idx + 1}. {item['q']}**")
                st.radio(f"Answer Q{idx + 1}", item["options"], key=f"auronix_q_{idx}", index=None, label_visibility="collapsed")
            submitted = st.form_submit_button("📊 Submit & Check Score", use_container_width=True)
        if submitted:
            correct = wrong = attempted = 0
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"auronix_q_{idx}")
                if chosen:
                    attempted += 1
                    if chosen == item["answer"]: correct += 1
                    else: wrong += 1
            raw_score = correct * marks_per_correct - wrong * marks_per_wrong
            max_score = len(st.session_state.quiz_data) * marks_per_correct
            st.session_state.quiz_submitted = True
            log_activity("quiz", st.session_state.active_topic, raw_score, max_score)
        if st.session_state.quiz_submitted:
            st.success("Test Submitted! Check your dashboard.")
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"auronix_q_{idx}")
                if chosen == item["answer"]:
                    st.markdown(f"✅ **Q{idx+1}: Correct** — {html.escape(item['answer'])}")
                else:
                    st.markdown(f"❌ **Q{idx+1}:** Your answer: `{chosen or 'Not attempted'}` · Correct: `{item['answer']}`")

    if st.session_state.qa_output:
        st.markdown("#### 📖 Subjective practice questions")
        st.markdown(st.session_state.qa_output)

    st.divider()
    st.markdown("### 🗂️ Smart Flashcards")
    flash_count = st.select_slider("Number of flashcards", options=[5, 10, 15, 20], value=10)
    if st.button("✨ Generate Flashcards", use_container_width=True):
        fp = f"Create exactly {flash_count} concise flashcards from this content, language {st.session_state.lang_saved}. Return JSON {{'cards':[{{'front':'question','back':'answer'}}]}}. Content:\n{st.session_state.topic_context[:14000]}"
        with st.spinner("Making revision flashcards..."):
            raw, err = generate_ai(fp, mode="flashcards", json_mode=True)
        if raw:
            try:
                cards = parse_json_object(raw).get("cards", [])
                st.session_state.flashcards = cards
                log_activity("flashcards", st.session_state.active_topic)
            except Exception:
                st.error("Flashcards error. Please retry.")
                
    if st.session_state.flashcards:
        for i, card in enumerate(st.session_state.flashcards):
            with st.expander(f"Card {i+1}: {card['front']}"):
                st.write(card["back"])

with st.popover(" "):
    st.markdown("""<div style='background:linear-gradient(135deg,rgba(255,165,0,.18),rgba(15,23,42,.96));padding:14px 16px;border-radius:14px;border:1px solid rgba(0,229,255,.4);margin-bottom:12px'>
    <div style='font-size:17px;font-weight:900;color:#00E5FF'>🤖 Auronix AI Buddy</div>
    <div style='font-size:13px;color:#E2E8F0;margin-top:5px'>Ask anything about your current study notes.</div></div>""", unsafe_allow_html=True)
    if not st.session_state.study_notes:
        st.info("Generate study notes first. Then I can answer doubts from those notes.")
    else:
        for msg in st.session_state.buddy_chat[-6:]:
            if msg["role"] == "user":
                st.markdown("🧑‍🎓 **You:** " + msg["text"])
            else:
                st.success("🤖 **Buddy:** " + msg["text"])
        doubt = st.text_input("Type your doubt", key="buddy_doubt_input", max_chars=1500)
        if st.button("💡 Solve My Doubt", key="buddy_ask_btn", use_container_width=True):
            if doubt.strip():
                bp = f"You are Auronix AI Buddy. Answer in {st.session_state.lang_saved}. Use these notes:\n{st.session_state.study_notes[:12000]}\n\nStudent doubt: {doubt.strip()}"
                with st.spinner("🤖 Buddy is thinking..."):
                    answer, err = generate_ai(bp, mode="buddy")
                if answer:
                    st.session_state.buddy_chat.append({"role": "user", "text": doubt.strip()})
                    st.session_state.buddy_chat.append({"role": "bot", "text": answer[:5000]})
                    st.rerun()
