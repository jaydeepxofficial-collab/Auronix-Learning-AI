"""Auronix learningAI V4.0 — 3-Layer YouTube Extractor, 6-Step Topper Notes, Hardcore Exam Tests & As-It-Is Calligraphy Export"""
import json
import os
import re
import sqlite3
import html
import urllib.request
import urllib.parse
from io import BytesIO
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
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

st.set_page_config(page_title="Auronix learningAI V4.0", page_icon="🦁", layout="centered")

DB_PATH = "auronix.db"

def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "").strip()
    except Exception:
        return os.getenv(name, "").strip()

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# ==========================================
# 🎨 UI, BIG HEADINGS & STRICT ROUND ROBOT CSS (UNTOUCHED)
# ==========================================
st.markdown("""
<style>
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
.block-container {padding-top:1.4rem; padding-bottom:5rem; max-width:1050px;}
.auronix-hero {background:linear-gradient(135deg,rgba(255,165,0,.16),rgba(255,94,0,.055));border:1px solid rgba(255,165,0,.38);border-radius:20px;padding:23px 20px;margin-bottom:22px;text-align:center;}
.auronix-title {background:linear-gradient(90deg,#FFB300,#FF6F00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:clamp(2rem,6vw,2.65rem);font-weight:950;margin:0;}
.auronix-badge {display:inline-block;background:rgba(255,165,0,.16);color:#FFB300;font-size:12px;font-weight:750;padding:6px 14px;border-radius:20px;margin-top:10px;border:1px solid rgba(255,165,0,.32);}
div.stButton>button, div.stDownloadButton>button {background:linear-gradient(90deg,#FF9800,#F57C00)!important;color:white!important;font-weight:750!important;border:0!important;border-radius:12px!important;}

/* 🔥 BIG, BOLD, EYE-CATCHING NOTES HEADINGS */
.auronix-notes-box h1 {
    font-size: 2.15rem !important;
    font-weight: 900 !important;
    color: #FFB300 !important;
    border-bottom: 2px solid rgba(255, 179, 0, 0.35) !important;
    padding-bottom: 8px !important;
    margin-top: 1.5rem !important;
}
.auronix-notes-box h2 {
    font-size: 1.65rem !important;
    font-weight: 850 !important;
    color: #FF8F00 !important;
    margin-top: 1.4rem !important;
}
.auronix-notes-box h3 {
    font-size: 1.3rem !important;
    font-weight: 750 !important;
    color: #38BDF8 !important;
    margin-top: 1rem !important;
}

/* 🤖 100% GOL (ROUND) FLOATING ROBOT FACE */
div[data-testid="stPopover"] {
    position: fixed !important;
    bottom: 25px !important;
    right: 25px !important;
    width: 65px !important;
    height: 65px !important;
    z-index: 99999 !important;
}
div[data-testid="stPopover"] > button {
    width: 65px !important;
    height: 65px !important;
    border-radius: 50% !important; 
    background: radial-gradient(circle at 50% 30%, #222 0%, #000 100%) !important;
    border: 3px solid #00E5FF !important;
    padding: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    box-shadow: 0 5px 20px rgba(0, 229, 255, 0.4) !important;
    transition: transform 0.3s ease !important;
}
div[data-testid="stPopover"] > button:hover {
    transform: scale(1.1) !important;
}
div[data-testid="stPopover"] > button p { display: none !important; }
div[data-testid="stPopover"] > button::after {
    content: '🤖' !important;
    font-size: 32px !important;
}
@media(max-width:600px){
    div[data-testid="stPopover"] { right: 15px !important; bottom: 15px !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="auronix-hero">
  <div class="auronix-title">🦁 Auronix learningAI</div>
  <p style="color:#B0B8C4;font-size:15px;margin:9px 0 0">6-Step Topper Notes · 3-Layer YouTube Lecture Extractor · Hardcore Tests · As-It-Is Calligraphy Export</p>
  <div class="auronix-badge">⚡ V4.0 Smart Radar Engine · Boards · JEE · NEET</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🎬 3-LAYER YOUTUBE LECTURE EXTRACTOR
# ==========================================
def extract_youtube_lecture(yt_url: str, manual_notes_paste: str = ""):
    """
    Layer 1: Fetch captions (supports both new & old youtube_transcript_api).
    Layer 2: Auto-fetch Video Title & Teacher/Channel via YouTube oEmbed (works even if captions are blocked!).
    Layer 3: Combine with optional pasted description/transcript.
    """
    vid_match = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([A-Za-z0-9_-]{11})", yt_url.strip())
    if not vid_match:
        return None, None, "❌ Invalid YouTube URL. Please paste a valid lecture link."

    vid_id = vid_match.group(1)
    video_title = ""
    channel_name = ""

    # Layer 2: oEmbed Metadata (Never gets IP-blocked easily)
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
            video_title = meta.get("title", "").strip()
            channel_name = meta.get("author_name", "").strip()
    except Exception:
        pass

    # Layer 1: Transcript Fetcher
    transcript_text = ""
    if YouTubeTranscriptApi:
        try:
            # New API syntax (v1.x)
            if hasattr(YouTubeTranscriptApi, "fetch"):
                api = YouTubeTranscriptApi()
                fetched = api.fetch(vid_id, languages=["hi", "en", "en-IN"])
                transcript_text = " ".join([snippet.text for snippet in fetched])
            else:
                # Classic API syntax (v0.6.x)
                fetched = YouTubeTranscriptApi.get_transcript(vid_id, languages=["hi", "en", "en-IN"])
                transcript_text = " ".join([t["text"] for t in fetched])
        except Exception:
            transcript_text = ""

    # Build final lecture payload
    parts = []
    if video_title:
        parts.append(f"YOUTUBE LECTURE TITLE: {video_title}")
    if channel_name:
        parts.append(f"TEACHER / CHANNEL: {channel_name}")
    if transcript_text:
        parts.append(f"LECTURE TRANSCRIPT:\n{transcript_text[:13000]}")
    if manual_notes_paste.strip():
        parts.append(f"ADDITIONAL LECTURE DESCRIPTION / POINTS:\n{manual_notes_paste.strip()[:5000]}")

    if not parts:
        return None, None, "❌ YouTube blocked captions & metadata for this private/restricted video. Please paste the lecture title/description in the box below!"

    status_msg = (
        f"🎥 Extracted Lecture: **{video_title or vid_id}**"
        + (f" by *{channel_name}*" if channel_name else "")
        + (" (✅ Full Captions Loaded)" if transcript_text else " (⚡ Smart Title & Syllabus Mode — Captions Unavailable on Server)")
    )
    return "\n\n".join(parts), status_msg, None

# ==========================================
# 🧹 MATH & AS-IT-IS CALLIGRAPHY EXPORT ENGINE
# ==========================================
def clean_math_formatting(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("\\(", "$")
        .replace("\\)", "$")
        .replace("\\[", "$$")
        .replace("\\]", "$$")
    )

def clean_latex_for_pdf(line: str) -> str:
    line = re.sub(r"\\(?:d)?frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1 / \2)", line)
    line = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", line)
    line = re.sub(r"\\text\{([^{}]+)\}", r"\1", line)
    replacements = {
        "\\theta": "theta", "\\pi": "pi", "\\alpha": "alpha", "\\beta": "beta",
        "\\gamma": "gamma", "\\delta": "delta", "\\Delta": "Delta", "\\omega": "omega",
        "\\Omega": "Ohm", "\\lambda": "lambda", "\\mu": "mu", "\\sigma": "sigma",
        "\\times": "x", "\\cdot": "*", "\\pm": "+/-", "\\leq": "<=", "\\geq": ">=",
        "\\neq": "!=", "\\approx": "~=", "\\infty": "infinity", "\\rightarrow": "->",
        "\\Rightarrow": "=>", "\\circ": " deg", "\\left": "", "\\right": "",
        "$$": "", "$": ""
    }
    for k, v in replacements.items():
        line = line.replace(k, v)
    line = re.sub(r"\\([a-zA-Z]+)", r"\1", line)
    line = line.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", line).strip()

def build_clean_pdf(markdown_text: str, exam_title: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Auronix Notes - {exam_title}"
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("AuronixTitle", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#D97706"), spaceAfter=10, alignment=TA_LEFT)
    h1_style = ParagraphStyle("AuronixH1", parent=styles["Heading1"], fontSize=14, leading=18, textColor=colors.HexColor("#B45309"), spaceBefore=12, spaceAfter=6)
    h2_style = ParagraphStyle("AuronixH2", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#1D4ED8"), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("AuronixBody", parent=styles["BodyText"], fontSize=10.5, leading=15, textColor=colors.HexColor("#1F2937"), spaceAfter=5)
    bullet_style = ParagraphStyle("AuronixBullet", parent=body_style, leftIndent=14, firstLineIndent=-8, spaceAfter=4)

    clean_exam = clean_latex_for_pdf(exam_title)
    story = [Paragraph(f"Auronix learningAI — {html.escape(clean_exam)}", title_style), Spacer(1, 6)]

    for raw_line in markdown_text.split("\n"):
        stripped = raw_line.strip()
        if not stripped or re.match(r"^[-|: ]+$", stripped):
            continue
        if stripped.startswith("### "):
            txt = clean_latex_for_pdf(stripped[4:])
            if txt: story.append(Paragraph(html.escape(txt), h2_style))
        elif stripped.startswith("## "):
            txt = clean_latex_for_pdf(stripped[3:])
            if txt: story.append(Paragraph(html.escape(txt), h1_style))
        elif stripped.startswith("# "):
            txt = clean_latex_for_pdf(stripped[2:])
            if txt: story.append(Paragraph(html.escape(txt), h1_style))
        elif stripped.startswith(("- ", "* ")):
            txt = clean_latex_for_pdf(stripped[2:])
            if txt:
                escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html.escape(txt))
                story.append(Paragraph(f"&bull; {escaped}", bullet_style))
        else:
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [clean_latex_for_pdf(c) for c in stripped.strip("|").split("|")]
                txt = "  |  ".join([c for c in cells if c])
            else:
                txt = clean_latex_for_pdf(stripped)
            if txt:
                escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html.escape(txt))
                story.append(Paragraph(escaped, body_style))

    doc.build(story)
    return buffer.getvalue()

def build_as_it_is_calligraphy_html(markdown_text: str, exam_title: str) -> bytes:
    """
    Renders the EXACT notes AS-IT-IS with KaTeX math, Markdown tables,
    beautiful calligraphy-grade typography, and a 1-click Save-as-PDF Print button!
    """
    safe_title = html.escape(exam_title)
    md_json = json.dumps(markdown_text)
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Auronix learningAI — {safe_title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #FFFDF8;
    color: #1E293B;
    max-width: 860px;
    margin: 0 auto;
    padding: 36px 28px 60px;
    line-height: 1.75;
    font-size: 15.5px;
  }}
  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
    border: 1px solid #F59E0B;
    border-radius: 14px;
    padding: 14px 20px;
    margin-bottom: 28px;
  }}
  .brand {{
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 900;
    color: #B45309;
  }}
  .sub-brand {{ font-size: 12.5px; color: #78350F; font-weight: 600; }}
  .print-btn {{
    background: linear-gradient(90deg, #F59E0B, #EA580C);
    color: #fff;
    border: none;
    padding: 10px 18px;
    border-radius: 10px;
    font-weight: 700;
    cursor: pointer;
    font-size: 14px;
  }}
  h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    color: #9A3412;
    border-bottom: 2.5px solid #F59E0B;
    padding-bottom: 8px;
    margin-top: 28px;
  }}
  h2 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.55rem;
    color: #C2410C;
    margin-top: 26px;
  }}
  h3 {{
    font-size: 1.2rem;
    color: #0369A1;
    font-weight: 700;
    margin-top: 18px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 18px 0;
    font-size: 14.5px;
  }}
  th, td {{
    border: 1px solid #CBD5E1;
    padding: 10px 12px;
    text-align: left;
  }}
  th {{
    background: #FEF3C7;
    color: #92400E;
    font-weight: 700;
  }}
  tr:nth-child(even) {{ background: #F8FAFC; }}
  blockquote {{
    border-left: 4px solid #F59E0B;
    background: #FFFBEB;
    padding: 10px 16px;
    margin: 14px 0;
    border-radius: 0 10px 10px 0;
  }}
  code {{
    background: #F1F5F9;
    padding: 2px 6px;
    border-radius: 5px;
    font-size: 13.5px;
  }}
  pre {{
    background: #0F172A;
    color: #F8FAFC;
    padding: 14px;
    border-radius: 10px;
    overflow-x: auto;
  }}
  pre code {{ background: transparent; color: inherit; }}
  @media print {{
    .print-btn {{ display: none !important; }}
    body {{ padding: 10px; background: #fff; }}
    .top-bar {{ border: 1px solid #D97706; }}
  }}
</style>
</head>
<body>
  <div class="top-bar">
    <div>
      <div class="brand">🦁 Auronix learningAI</div>
      <div class="sub-brand">{safe_title} · As-It-Is Calligraphy Study Sheet</div>
    </div>
    <button class="print-btn" onclick="window.print()">🖨️ Save as Exact PDF</button>
  </div>
  <div id="content"></div>
  <script>
    window.addEventListener("DOMContentLoaded", function() {{
      const rawMd = {md_json};
      document.getElementById("content").innerHTML = marked.parse(rawMd);
      renderMathInElement(document.getElementById("content"), {{
        delimiters: [
          {{left: "$$", right: "$$", display: true}},
          {{left: "$", right: "$", display: false}}
        ],
        throwOnError: false
      }});
    }});
  </script>
</body>
</html>"""
    return html_doc.encode("utf-8")

# ==========================================
# 🧠 UNTOUCHED SMART RADAR ENGINE
# ==========================================
def generate_ai(prompt: str, json_mode: bool = False, temperature: float = 0.25):
    errors = []
    sys_msg = (
        "You are Auronix learningAI, India's top Board, JEE Advanced, and NEET educator. "
        "Follow the user's selected exam rigor, syllabus boundary, and language strictly. "
        "Use $ for inline math and $$ for block math. NEVER use \\( or \\) or \\[ or \\]."
    )
    
    if GROQ_API_KEY and Groq:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            live_models = client.models.list().data
            valid_chat_models = [
                m.id for m in live_models
                if "guard" not in m.id.lower()
                and "whisper" not in m.id.lower()
                and "tts" not in m.id.lower()
            ]
            
            if valid_chat_models:
                for model_id in valid_chat_models:
                    try:
                        kwargs = {
                            "model": model_id,
                            "messages": [
                                {"role": "system", "content": sys_msg},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": temperature
                        }
                        if json_mode:
                            kwargs["response_format"] = {"type": "json_object"}
                        res = client.chat.completions.create(**kwargs)
                        return res.choices[0].message.content, None
                    except Exception as e:
                        errors.append(f"Groq {model_id}: {str(e)}")
                        continue
            else:
                errors.append("Groq: No valid chat models.")
        except Exception as e:
            errors.append(f"Groq API Error: {str(e)}")

    if GEMINI_API_KEY and genai:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
            for m in gemini_models:
                try:
                    model = genai.GenerativeModel(
                        m,
                        system_instruction=sys_msg,
                        generation_config={"temperature": temperature}
                    )
                    res = model.generate_content(prompt)
                    return res.text, None
                except Exception as e:
                    errors.append(f"Gemini {m}: {str(e)}")
                    continue
        except Exception as e:
            errors.append(f"Gemini API Error: {str(e)}")

    if not GROQ_API_KEY and not GEMINI_API_KEY:
        return None, "❌ API Keys missing!"
    
    return None, f"❌ AI Failure: {' | '.join(errors)}"

# ==========================================
# 🔥 HARDCORE EXAM RIGOR PROFILES
# ==========================================
EXAM_RIGOR_MAP = {
    "🏫 Class 11/12 Boards (CBSE / State)": (
        "STRICT CLASS 11/12 BOARD STANDARD: Crisp NCERT definitions, exact board-exam keywords, "
        "step-by-step standard derivations, SI units, and clear diagram descriptions."
    ),
    "🩺 NEET (Pure NCERT + 15-Yr PYQ Radar)": (
        "PURE NEET NCERT + PYQ SCANNER MODE (ZERO OUT-OF-NCERT FLUFF): Extract ONLY exact NCERT lines, "
        "NCERT tables, scientist names, dates, exceptions, and last-15-year NEET PYQ hotspots. "
        "Highlight exact NCERT trap words ('only', 'always', 'all', 'except')."
    ),
    "⚙️ JEE Main (NCERT + PYQ Tricks & Speed)": (
        "STRICT JEE MAIN STANDARD: Strong Class 11/12 conceptual depth, JEE Main PYQ patterns, "
        "graph transformations, special cases, numerical shortcuts, and silly-mistake traps."
    ),
    "🚀 JEE Advanced (Hardest Top-Batch Level)": (
        "HARDEST JEE ADVANCED TOP-BATCH STANDARD: Deep analytical derivations, multi-concept intersections, "
        "limiting cases, boundary conditions, non-obvious exceptions, and brutal conceptual traps."
    )
}

# ==========================================
# 💾 STATE INITIALIZATION
# ==========================================
DEFAULTS = {
    "study_notes": "",
    "topic_context": "",
    "quiz_data": None,
    "quiz_submitted": False,
    "qa_output": "",
    "buddy_chat": [],
    "flashcards": [],
    "selected_exam": "🏫 Class 11/12 Boards (CBSE / State)",
    "selected_basis": "📘 Strict NCERT Line-by-Line Core",
    "selected_lang": "Hinglish (Easy & Clear Concept Clarity)"
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================================
# 🎓 STEP 1: EXAM & STYLE CONTROL PANEL
# ==========================================
st.markdown("### 🎯 Step 1: Customize Your Exam & Study Style")

c1, c2 = st.columns(2)
with c1:
    target_exam = st.selectbox("1️⃣ Target Exam", list(EXAM_RIGOR_MAP.keys()))
with c2:
    content_basis = st.selectbox(
        "2️⃣ Content Basis (Source Boundary)",
        [
            "📘 Strict NCERT Line-by-Line Core",
            "🔥 PYQ Trend & Exam Traps Focused",
            "⚡ Complete NCERT + PYQ Combo"
        ]
    )

c3, c4 = st.columns(2)
with c3:
    output_type = st.selectbox(
        "3️⃣ What do you want?",
        [
            "📚 Crisp 6-Step Topper Notes",
            "⚡ Complete Formula, Reactions & Trick Sheet",
            "📖 Zero-to-Hero Deep Explanation"
        ]
    )
with c4:
    lang_choice = st.selectbox(
        "4️⃣ Explanation Language",
        [
            "Hinglish (Easy & Clear Concept Clarity)",
            "English (100% Exam Ready)"
        ]
    )

# ==========================================
# 📝 STEP 2: 3-FIELD TOPIC INPUT OR 3-LAYER YOUTUBE EXTRACTOR
# ==========================================
st.divider()
st.markdown("### 📝 Step 2: Enter Structured Topic or YouTube Lecture")
mode = st.radio("Choose input method", ["📝 Structured Topic Input", "🔗 YouTube Lecture Link"], horizontal=True)

source_text = ""
is_youtube_mode = False

if mode == "📝 Structured Topic Input":
    t1, t2 = st.columns([1, 2])
    with t1:
        student_class = st.selectbox("🎓 Class", ["Class 11", "Class 12", "Dropper (11th + 12th)"])
    with t2:
        chapter_name = st.text_input("📖 Chapter Name (Required)", placeholder="e.g., Rotational Motion / Cell: The Unit of Life")
    specific_topic = st.text_input("🎯 Specific Topic (Optional — leave blank for full chapter)", placeholder="e.g., Moment of Inertia / Mitochondria & Plastids")

    if st.button("✨ Generate 6-Step Topper Notes", use_container_width=True):
        if not chapter_name.strip():
            st.warning("⚠️ Please enter the Chapter Name first!")
        else:
            topic_part = f" | Specific Topic: {specific_topic.strip()}" if specific_topic.strip() else " | Scope: Complete Chapter"
            source_text = f"Class: {student_class} | Chapter: {chapter_name.strip()}{topic_part}"

elif mode == "🔗 YouTube Lecture Link":
    is_youtube_mode = True
    yt_url = st.text_input("🔗 Paste YouTube Lecture URL", placeholder="https://www.youtube.com/watch?v=...")
    manual_yt_paste = st.text_area(
        "📋 Optional: Paste Video Description / Rough Points (Only if video is private or captions are off)",
        height=70
    )
    if st.button("✨ Extract Sir's Lecture & Generate Crisp Notes", use_container_width=True):
        if not yt_url.strip():
            st.warning("⚠️ Please paste a YouTube lecture link first!")
        else:
            with st.spinner("🎬 Extracting lecture captions & metadata..."):
                extracted, status_msg, yt_err = extract_youtube_lecture(yt_url, manual_yt_paste)
            if yt_err:
                st.error(yt_err)
            else:
                st.info(status_msg)
                source_text = extracted

# ==========================================
# 🧠 V4.0 STRICT 6-STEP TOPPER NOTE GENERATOR
# ==========================================
if source_text:
    for state_key in list(st.session_state.keys()):
        if state_key.startswith("auronix_q_"):
            del st.session_state[state_key]
    st.session_state.quiz_data = None
    st.session_state.qa_output = ""
    st.session_state.quiz_submitted = False
    st.session_state.flashcards = []
    st.session_state.selected_exam = target_exam
    st.session_state.selected_basis = content_basis
    st.session_state.selected_lang = lang_choice

    rigor_instruction = EXAM_RIGOR_MAP[target_exam]
    yt_extra_rule = (
        "YOUTUBE LECTURE RULE: Distill the teacher's lecture into ultra-crisp, structured topper notes—cut out all filler talk, greetings, and repetition, keeping ONLY the core concepts, formulas, tricks, and exam points taught in the lecture."
        if is_youtube_mode else ""
    )

    prompt = f"""
You are Auronix learningAI V4.0, India's top ranker-producing educator.

USER SELECTION (FOLLOW 100% STRICTLY):
- Target Exam Level: {target_exam}
- Content Basis: {content_basis}
- Output Style: {output_type}
- Language: {lang_choice}
- Input Source: {source_text[:15000]}

MANDATORY EXAM RIGOR:
{rigor_instruction}
{yt_extra_rule}

STRICT 6-STEP TOPPER NOTES ARCHITECTURE (FOLLOW THIS EXACT ORDER):
# [Main Chapter / Topic Title]

## 1. 📌 Introduction & Chapter Roadmap
- Give a crisp 3-4 line intro and a bulleted roadmap of exact sub-topics covered below.

## 2. 🧠 Core Concepts (Topic-by-Topic Breakdown)
- Cover each sub-topic under clear `###` headings.
- For EVERY sub-topic provide:
  - **Exact Definition / Principle & Formula** (use `$` for inline math and `$$` for block math).
  - **💡 Logical Real-Life Analogy:** Give a 100% scientifically and logically ACCURATE real-life example (NO illogical or cringe jokes!).
  - **✍️ Solved Example:** A crisp exam-relevant example showing how to apply the concept.

## 3. 📊 Comparison Tables & Process Flowcharts
- Present key differences, classifications, or formulas in clean **Markdown Tables (Columns)**.
- Present step-by-step mechanisms, derivations, or pathways as clean **Arrow Flowcharts** (e.g., `Step 1 ➔ Step 2 ➔ Step 3`).

## 4. ⚡ Quick Summary & Revision Capsule
- 5-7 ultra-crisp bullet points for 2-minute revision before the exam.

## 5. 🚨 JEE & NEET Traps + PYQ Radar
- Highlight exact examiner traps, exceptions, and high-frequency PYQ patterns from this chapter.

## 6. 🏁 Finish
- End cleanly with a 1-line mastery checklist.

MATH RULE: Use $ for inline math and $$ for block math. NEVER use \\( or \\).
"""
    with st.spinner(f"🧠 Building 6-Step Topper Notes for {target_exam}..."):
        notes, err = generate_ai(prompt, temperature=0.25)
        if notes:
            st.session_state.study_notes = clean_math_formatting(notes)
            st.session_state.topic_context = source_text
            st.success(f"✅ {target_exam} 6-Step Topper Notes Ready!")
        else:
            st.error(err)

# ==========================================
# 📖 DISPLAY CLEAN NOTES & AS-IT-IS CALLIGRAPHY EXPORT
# ==========================================
if st.session_state.study_notes:
    st.markdown('<div class="auronix-notes-box">', unsafe_allow_html=True)
    st.markdown(st.session_state.study_notes)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption("💡 **Best Tip for Exact PDF:** Download the **As-It-Is Calligraphy Sheet**, open it in Chrome/Brave, and tap **🖨️ Save as Exact PDF** — every formula, table, and font stays 100% identical!")
    dl1, dl2 = st.columns(2)
    with dl1:
        calligraphy_html = build_as_it_is_calligraphy_html(st.session_state.study_notes, st.session_state.selected_exam)
        st.download_button(
            "✨ Download As-It-Is Calligraphy PDF Sheet",
            data=calligraphy_html,
            file_name="Auronix_Calligraphy_Notes.html",
            mime="text/html",
            use_container_width=True
        )
    with dl2:
        if REPORTLAB_OK:
            try:
                pdf_bytes = build_clean_pdf(st.session_state.study_notes, st.session_state.selected_exam)
                st.download_button(
                    "📄 Quick Direct PDF (Plain Offline)",
                    data=pdf_bytes,
                    file_name="Auronix_Quick_Notes.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"PDF build skipped: {e}")

    # ==========================================
    # 🧠 HARDCORE IN-CONTEXT PRACTICE TEST
    # ==========================================
    st.divider()
    st.markdown("### 🧠 Test Your Knowledge (Hardcore Exam Level · Strictly From Notes)")
    st.caption(f"🎯 Locked to: **{st.session_state.selected_exam}** · **{st.session_state.selected_basis}**")

    q1, q2, q3 = st.columns(3)
    with q1:
        num_q = st.selectbox("Questions", [5, 10, 15, 20], index=1)
    with q2:
        diff_level = st.selectbox("Difficulty", ["Hard / Exam Ranker", "Exam Standard", "Mixed PYQ Style"])
    with q3:
        test_format = st.selectbox("Format", ["Interactive MCQs", "Subjective Q&A (Boards/Written)"])
    
    if st.button("🚀 Generate Hardcore Test From These Notes", use_container_width=True):
        for state_key in list(st.session_state.keys()):
            if state_key.startswith("auronix_q_"):
                del st.session_state[state_key]
        st.session_state.quiz_data = None
        st.session_state.quiz_submitted = False
        st.session_state.qa_output = ""
        
        if test_format == "Interactive MCQs":
            qprompt = f"""
You MUST create {num_q} CHALLENGING, RANKER-LEVEL exam MCQs STRICTLY AND EXCLUSIVELY from the STUDY NOTES provided below.

CRITICAL DIFFICULTY & QUALITY RULES (NO EASY / DIRECT ONE-LINER QUESTIONS!):
1. Every single question MUST test deep understanding, traps, formulas, or facts present in the STUDY NOTES below.
2. Match the EXACT rigor of {st.session_state.selected_exam} ({diff_level}):
   - If NEET: Include Multi-Statement ("How many of the following statements are correct?"), NCERT Trap Assertion-Reason, and Match-the-Column MCQs.
   - If JEE Advanced: Include brutal multi-concept analytical traps, limiting cases, and non-trivial numericals from the notes.
   - If JEE Main: Include tricky conceptual & calculation-based PYQ-style MCQs from the notes.
   - If Boards: Include CBSE Class 11/12 competency, case-based, and Assertion-Reason MCQs from the notes.
3. Language: {st.session_state.selected_lang}.
4. Return ONLY a valid JSON object with key "questions", a list of objects each having:
   - "q": Question string
   - "options": List of EXACTLY 4 option strings
   - "answer": Exact string matching one of the 4 options
   - "explanation": Step-by-step explanation referencing the notes

STUDY NOTES:
{st.session_state.study_notes[:12000]}
"""
            with st.spinner(f"Preparing {num_q} hardcore {st.session_state.selected_exam} MCQs..."):
                raw, err = generate_ai(qprompt, json_mode=True, temperature=0.2)
            if raw:
                try:
                    clean_raw = re.sub(r"```(?:json)?|```", "", raw).strip()
                    start, end = clean_raw.find("{"), clean_raw.rfind("}")
                    obj = json.loads(clean_raw[start:end+1])
                    valid = [
                        item for item in obj.get("questions", [])
                        if isinstance(item.get("options"), list) and len(item["options"]) == 4 and item.get("q")
                    ]
                    st.session_state.quiz_data = valid
                except Exception:
                    st.error("Invalid quiz format returned by AI. Please tap Generate Test once more.")
            else:
                st.error(err)
        else:
            qprompt = f"""
Create {num_q} high-standard subjective exam questions (Short Answer, Derivations, Case-Study & Long Answer) with step-by-step Marking Scheme answers STRICTLY from the STUDY NOTES below.
Target Level: {st.session_state.selected_exam} ({diff_level}).
Language: {st.session_state.selected_lang}.

STUDY NOTES:
{st.session_state.study_notes[:12000]}
"""
            with st.spinner("Preparing written exam questions from your notes..."):
                answer, err = generate_ai(qprompt, temperature=0.2)
            if answer:
                st.session_state.qa_output = clean_math_formatting(answer)

    # SHOW INTERACTIVE TEST
    if st.session_state.quiz_data:
        st.markdown(f"#### 📝 Live Exam Test · {len(st.session_state.quiz_data)} Questions")
        is_competitive = ("NEET" in st.session_state.selected_exam) or ("JEE" in st.session_state.selected_exam)
        marks_per_correct = 4 if is_competitive else 1
        marks_per_wrong = 1 if is_competitive else 0
        
        with st.form("auronix_quiz_form"):
            for idx, item in enumerate(st.session_state.quiz_data):
                q_text = clean_math_formatting(str(item["q"]))
                st.markdown(f"**Q{idx + 1}. {q_text}**")
                clean_opts = [clean_math_formatting(str(opt)) for opt in item["options"]]
                st.radio(
                    f"Answer Q{idx + 1}",
                    clean_opts,
                    key=f"auronix_q_{idx}",
                    index=None,
                    label_visibility="collapsed"
                )
                st.write("")
            submitted = st.form_submit_button("📊 Submit & Check Score", use_container_width=True)
            
        if submitted:
            correct = wrong = attempted = 0
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"auronix_q_{idx}")
                clean_ans = clean_math_formatting(str(item["answer"]))
                if chosen:
                    attempted += 1
                    if chosen == clean_ans:
                        correct += 1
                    else:
                        wrong += 1
                    
            raw_score = correct * marks_per_correct - wrong * marks_per_wrong
            max_score = len(st.session_state.quiz_data) * marks_per_correct
            st.session_state.quiz_submitted = True
            st.success(f"🏆 Score: {raw_score} / {max_score} · (Correct: {correct} | Wrong: {wrong} | Unattempted: {len(st.session_state.quiz_data) - attempted})")
            
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"auronix_q_{idx}")
                clean_ans = clean_math_formatting(str(item["answer"]))
                if chosen == clean_ans:
                    st.markdown(f"✅ **Q{idx+1}: Correct** — {clean_ans}")
                else:
                    st.markdown(f"❌ **Q{idx+1}:** Your answer: `{chosen or 'Not attempted'}` · **Correct:** `{clean_ans}`")
                if item.get("explanation"):
                    st.info("💡 **Solution:** " + clean_math_formatting(str(item["explanation"])))

    # SHOW SUBJECTIVE TEST
    if st.session_state.qa_output:
        st.markdown("#### 📖 Subjective Questions & Marking Scheme")
        st.markdown(st.session_state.qa_output)

    # ==========================================
    # 🗂️ STRICT IN-CONTEXT FLASHCARDS
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ Smart Revision Flashcards (Strictly From Notes)")
    if st.button("✨ Generate 10 Flashcards From These Notes", use_container_width=True):
        f_prompt = f"""
Respond ONLY with valid JSON.
Create exactly 10 high-yield revision flashcards STRICTLY AND EXCLUSIVELY from the STUDY NOTES below.
Target Exam: {st.session_state.selected_exam}.
Language: {st.session_state.selected_lang}.
Return JSON format EXACTLY like this:
{{"cards": [{{"front": "Crisp question / term / formula prompt from notes", "back": "Crisp answer / trick from notes"}}]}}

STUDY NOTES:
{st.session_state.study_notes[:10000]}
"""
        with st.spinner("Making topic-locked flashcards from your notes..."):
            raw, err = generate_ai(f_prompt, json_mode=True, temperature=0.2)
            if raw:
                try:
                    clean_raw = re.sub(r"```(?:json)?|```", "", raw).strip()
                    start, end = clean_raw.find("{"), clean_raw.rfind("}")
                    st.session_state.flashcards = json.loads(clean_raw[start:end+1]).get("cards", [])
                except Exception:
                    st.error("JSON Parsing Error. Please tap Generate once more.")
            else:
                st.error(err)
                
    if st.session_state.flashcards:
        for i, card in enumerate(st.session_state.flashcards):
            clean_front = clean_math_formatting(str(card.get("front", "")))
            clean_back = clean_math_formatting(str(card.get("back", "")))
            with st.expander(f"🃏 Card {i+1}: {clean_front}"):
                st.markdown(clean_back)

# ==========================================
# 🤖 EMO ROBOT BUDDY (PRECISION MODE — UNTOUCHED!)
# ==========================================
with st.popover(" "):
    st.markdown("<h4 style='color:#00E5FF'>🤖 Auronix Precision Buddy</h4>", unsafe_allow_html=True)
    if not st.session_state.study_notes:
        st.info("Pehle notes generate kar, fir doubt poochh!")
    else:
        doubt = st.text_input("Ask any exact doubt from these notes:")
        if st.button("💡 Solve Doubt (Precision Mode)", use_container_width=True) and doubt.strip():
            b_prompt = f"""
You are a strict, 100% accurate doubt-solving mentor for {st.session_state.selected_exam}.
Language: {st.session_state.selected_lang}.

RULES (ZERO FLUCTUATION / ZERO GUESSING):
1. First check the STUDY NOTES below for the exact concept/formula.
2. Answer the student's doubt directly in 3 clean parts:
   - **🎯 Direct Answer:** (Exact, crisp 1-2 line answer)
   - **🧠 Step-by-Step Logic / Formula:** (Clear reasoning with proper $ math)
   - **💡 Logical Real-Life Analogy:** (1-line scientifically accurate analogy)
3. Do NOT ramble, do NOT hallucinate, and do NOT give illogical jokes.

STUDY NOTES:
{st.session_state.study_notes[:10000]}

STUDENT DOUBT:
{doubt.strip()}
"""
            with st.spinner("Solving with 100% precision..."):
                ans, err = generate_ai(b_prompt, temperature=0.05)
                if ans:
                    st.success(clean_math_formatting(ans))
                else:
                    st.error(err)
