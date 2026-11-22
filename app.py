"""Auronix learningAI V4.2 (Verified Final Build) — Zero-Truncation, Math-Safe Calligraphy Export & Precision Doubt Solver"""
import json
import os
import re
import html
import urllib.request
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

st.set_page_config(page_title="Auronix learningAI V4.2", page_icon="🦁", layout="centered")

def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "").strip()
    except Exception:
        return os.getenv(name, "").strip()

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# ==========================================
# 🎨 CLEAN, SERIOUS EXAM-GRADE UI & HEADINGS CSS
# ==========================================
st.markdown("""
<style>
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
.block-container {padding-top:1.4rem; padding-bottom:4rem; max-width:1050px;}
.auronix-hero {background:linear-gradient(135deg,rgba(255,165,0,.14),rgba(255,94,0,.045));border:1px solid rgba(255,165,0,.35);border-radius:18px;padding:22px 20px;margin-bottom:22px;text-align:center;}
.auronix-title {background:linear-gradient(90deg,#FFB300,#FF6F00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:clamp(1.9rem,5.5vw,2.55rem);font-weight:950;margin:0;}
.auronix-badge {display:inline-block;background:rgba(255,165,0,.15);color:#FFB300;font-size:12px;font-weight:750;padding:5px 14px;border-radius:20px;margin-top:10px;border:1px solid rgba(255,165,0,.30);}
div.stButton>button, div.stDownloadButton>button, div.stFormSubmitButton>button {background:linear-gradient(90deg,#FF9800,#F57C00)!important;color:white!important;font-weight:750!important;border:0!important;border-radius:12px!important;}

/* 🔥 BIG, AUTHORITATIVE TOPPER NOTES HEADINGS */
.auronix-notes-box h1 {
    font-size: 2.05rem !important;
    font-weight: 900 !important;
    color: #FFB300 !important;
    border-bottom: 2px solid rgba(255, 179, 0, 0.35) !important;
    padding-bottom: 8px !important;
    margin-top: 1.5rem !important;
}
.auronix-notes-box h2 {
    font-size: 1.55rem !important;
    font-weight: 850 !important;
    color: #FF8F00 !important;
    margin-top: 1.4rem !important;
}
.auronix-notes-box h3 {
    font-size: 1.25rem !important;
    font-weight: 750 !important;
    color: #38BDF8 !important;
    margin-top: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="auronix-hero">
  <div class="auronix-title">🦁 Auronix learningAI</div>
  <p style="color:#B0B8C4;font-size:15px;margin:8px 0 0">Serious Topper Notes · Real 15-Yr PYQs · YouTube Lecture Distiller · As-It-Is Calligraphy Export</p>
  <div class="auronix-badge">⚡ V4.2 Verified Engine · Boards · JEE Main & Adv · NEET</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🎬 3-LAYER YOUTUBE LECTURE EXTRACTOR
# ==========================================
def extract_youtube_lecture(yt_url: str, manual_notes_paste: str = ""):
    vid_match = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([A-Za-z0-9_-]{11})", yt_url.strip())
    if not vid_match:
        return None, None, "❌ Invalid YouTube URL. Please paste a valid lecture link."

    vid_id = vid_match.group(1)
    video_title = ""
    channel_name = ""

    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
            video_title = meta.get("title", "").strip()
            channel_name = meta.get("author_name", "").strip()
    except Exception:
        pass

    transcript_text = ""
    if YouTubeTranscriptApi:
        try:
            if hasattr(YouTubeTranscriptApi, "fetch"):
                api = YouTubeTranscriptApi()
                fetched = api.fetch(vid_id, languages=["hi", "en", "en-IN"])
                transcript_text = " ".join([snippet.text for snippet in fetched])
            else:
                fetched = YouTubeTranscriptApi.get_transcript(vid_id, languages=["hi", "en", "en-IN"])
                transcript_text = " ".join([t["text"] for t in fetched])
        except Exception:
            transcript_text = ""

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
# 🧹 MATH & MATH-SAFE CALLIGRAPHY EXPORT ENGINE
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
            if txt:
                story.append(Paragraph(html.escape(txt), h2_style))
        elif stripped.startswith("## "):
            txt = clean_latex_for_pdf(stripped[3:])
            if txt:
                story.append(Paragraph(html.escape(txt), h1_style))
        elif stripped.startswith("# "):
            txt = clean_latex_for_pdf(stripped[2:])
            if txt:
                story.append(Paragraph(html.escape(txt), h1_style))
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
    """Math-safe As-It-Is Calligraphy HTML/PDF sheet (protects LaTeX from marked.js)."""
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
      const mathStore = [];
      let protectedMd = rawMd.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, function(m) {{
        mathStore.push(m);
        return "AURONIXMATHBLOCK" + (mathStore.length - 1) + "END";
      }});
      protectedMd = protectedMd.replace(/\\$([^\\$\\n]+?)\\$/g, function(m) {{
        mathStore.push(m);
        return "AURONIXMATHINLINE" + (mathStore.length - 1) + "END";
      }});
      let htmlOut = marked.parse(protectedMd);
      htmlOut = htmlOut.replace(/AURONIXMATH(?:BLOCK|INLINE)(\\d+)END/g, function(_, i) {{
        return mathStore[Number(i)];
      }});
      const container = document.getElementById("content");
      container.innerHTML = htmlOut;
      renderMathInElement(container, {{
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
# 🧠 SMART RADAR ENGINE (HIGH-CONTEXT + UPDATED BACKUP)
# ==========================================
def generate_ai(prompt: str, json_mode: bool = False, temperature: float = 0.2, max_tokens: int = 8192):
    errors = []
    sys_msg = (
        "You are Auronix learningAI, India's premier Board, JEE Advanced, and NEET ranker-producing educator. "
        "Maintain an authoritative, serious, topper-handbook tone. Never truncate or leave sections incomplete. "
        "Use $ for inline math and $$ for block math. NEVER use \\( or \\) or \\[ or \\]."
    )

    if GROQ_API_KEY and Groq:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            live_models = client.models.list().data
            skip_words = ("guard", "whisper", "tts", "audio", "embed", "vision")
            valid_chat_models = [
                m.id for m in live_models
                if not any(w in m.id.lower() for w in skip_words)
            ]
            preferred = [m for m in valid_chat_models if any(k in m.lower() for k in ("llama-3.3", "70b", "qwen"))]
            others = [m for m in valid_chat_models if m not in preferred]
            ordered_models = preferred + others

            if ordered_models:
                for model_id in ordered_models:
                    try:
                        kwargs = {
                            "model": model_id,
                            "messages": [
                                {"role": "system", "content": sys_msg},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": temperature,
                            "max_tokens": max_tokens
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
            gemini_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
            for m in gemini_models:
                try:
                    model = genai.GenerativeModel(
                        m,
                        system_instruction=sys_msg,
                        generation_config={"temperature": temperature, "max_output_tokens": max_tokens}
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
# 🔥 SERIOUS EXAM RIGOR PROFILES
# ==========================================
EXAM_RIGOR_MAP = {
    "🏫 Class 11/12 Boards (CBSE / State)": (
        "STRICT CLASS 11/12 BOARD TOPPER STANDARD: Formal NCERT definitions, exact board-exam keywords, "
        "complete step-by-step derivations, SI units, and clear diagram descriptions."
    ),
    "🩺 NEET (Pure NCERT + 15-Yr PYQ Radar)": (
        "PURE NEET NCERT + 15-YEAR PYQ SCANNER MODE (ZERO OUT-OF-NCERT FLUFF): Extract ONLY exact NCERT lines, "
        "NCERT tables, scientist names, dates, exceptions, and real last-15-year NEET/AIPMT PYQ hotspots. "
        "Highlight exact NCERT trap words ('only', 'always', 'all', 'except')."
    ),
    "⚙️ JEE Main (NCERT + PYQ Tricks & Speed)": (
        "STRICT JEE MAIN TOPPER STANDARD: Strong Class 11/12 conceptual depth, JEE Main PYQ patterns, "
        "graph transformations, special cases, numerical shortcuts, and silly-mistake traps."
    ),
    "🚀 JEE Advanced (Hardest Top-Batch Level)": (
        "HARDEST JEE ADVANCED TOP-BATCH STANDARD (KOTA RANKER HANDBOOK): Deep analytical derivations, "
        "multi-concept intersections, limiting cases, boundary conditions, non-obvious exceptions, and brutal conceptual traps."
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
    "flashcards": [],
    "doubt_answer": "",
    "selected_exam": "🏫 Class 11/12 Boards (CBSE / State)",
    "selected_basis": "📘 Strict NCERT Line-by-Line Core",
    "selected_lang": "Hinglish (Clear & Serious Concept Clarity)"
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

board_stream = ""
if target_exam == "🏫 Class 11/12 Boards (CBSE / State)":
    board_stream = st.radio(
        "🎯 School Board Alignment (Select Your Track):",
        [
            "📘 Pure School Boards (CBSE / State Only)",
            "🩺 Boards + NEET Alignment (NCERT Bio/Chem/Phys Focus)",
            "⚙️ Boards + JEE Alignment (Derivations & Numericals Focus)"
        ],
        horizontal=True
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
            "Hinglish (Clear & Serious Concept Clarity)",
            "English (100% Exam Ready)"
        ]
    )

effective_exam_label = f"{target_exam} [{board_stream}]" if board_stream else target_exam

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

    if st.button("✨ Generate Complete 6-Step Topper Notes", use_container_width=True):
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
    if st.button("✨ Extract Lecture & Generate Complete Notes", use_container_width=True):
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
# 🧠 ZERO-TRUNCATION 6-STEP TOPPER NOTE GENERATOR
# ==========================================
if source_text:
    for state_key in list(st.session_state.keys()):
        if state_key.startswith("auronix_q_"):
            del st.session_state[state_key]
    st.session_state.quiz_data = None
    st.session_state.qa_output = ""
    st.session_state.quiz_submitted = False
    st.session_state.flashcards = []
    st.session_state.doubt_answer = ""
    st.session_state.selected_exam = effective_exam_label
    st.session_state.selected_basis = content_basis
    st.session_state.selected_lang = lang_choice

    rigor_instruction = EXAM_RIGOR_MAP[target_exam]
    if board_stream:
        rigor_instruction += f" | BOARD TRACK ALIGNMENT: Strictly align examples, traps, and PYQs with {board_stream}."

    if "NEET" in effective_exam_label:
        pyq_mandatory_rule = (
            "MANDATORY 15-YEAR NEET PYQ BANK: In Section 5, include **5 to 7 actual, most-repeated Last 15 Years NEET / AIPMT PYQ Questions** "
            "from this exact chapter/topic with Year tags (`[NEET 2023]`, `[NEET 2020]`, `[AIPMT 2015]`), "
            "followed by the exact NCERT-based Answer & 1-line Trap/Trick."
        )
    elif "JEE" in effective_exam_label:
        pyq_mandatory_rule = (
            "MANDATORY JEE PYQ BANK: In Section 5, include **5 high-yield JEE Main / Advanced PYQ Questions** "
            "from this exact chapter/topic with Year tags (`[JEE Main 2023]`, `[JEE Adv 2019]`), "
            "followed by the crisp Formula/Approach & Final Answer."
        )
    else:
        pyq_mandatory_rule = (
            "MANDATORY CBSE BOARD PYQ BANK: In Section 5, include **5 most-repeated CBSE Class 11/12 Board Previous Year Questions** "
            "(1-Mark, 2-Mark, 3-Mark/5-Mark) with Marking Scheme key points."
        )

    yt_extra_rule = (
        "YOUTUBE LECTURE RULE: Distill the teacher's lecture into ultra-crisp, structured topper notes—cut out filler talk and repetition, keeping ONLY core concepts, formulas, tricks, and exam points."
        if is_youtube_mode else ""
    )

    prompt = f"""
You are Auronix learningAI V4.2, India's premier ranker-producing educator.
Write SERIOUS, EXAM-GRADE, TOPPER-HANDBOOK NOTES (no childish jokes or casual filler).
CRITICAL COMPLETION RULE: You MUST complete ALL 6 SECTIONS cleanly from Section 1 through Section 6 without cutting off mid-sentence! Keep explanations dense, crisp, and high-yield so every single section finishes completely.

USER SELECTION (FOLLOW 100% STRICTLY):
- Target Exam Level: {effective_exam_label}
- Content Basis: {content_basis}
- Output Style: {output_type}
- Language: {lang_choice}
- Input Source: {source_text[:15000]}

MANDATORY EXAM RIGOR:
{rigor_instruction}
{yt_extra_rule}

STRICT 6-STEP TOPPER NOTES ARCHITECTURE (COMPLETE ALL 6 SECTIONS):
# [Main Chapter / Topic Title]

## 1. 📌 Introduction & Chapter Roadmap
- Crisp 3-line exam weightage & scope overview + bulleted roadmap of exact sub-topics covered below.

## 2. 🧠 Core Concepts (Topic-by-Topic Breakdown)
- Cover every core sub-topic under clear `###` headings.
- For EVERY sub-topic provide:
  - **Definition / Principle & Formula:** Exact exam-ready statement and equations (`$` inline, `$$` block).
  - **💡 Logical Real-World Application:** A 100% scientifically accurate real-world physical/biological example (strictly serious & logical).
  - **✍️ Solved Example:** A crisp exam-relevant numerical or conceptual example with step-by-step solution.

## 3. 📊 Comparison Tables & Process Flowcharts
- Present key differences, classifications, or formula summaries in clean **Markdown Tables (Columns)**.
- Present step-by-step mechanisms, derivations, or pathways as clean **Arrow Flowcharts** (`Step 1 ➔ Step 2 ➔ Step 3`).

## 4. ⚡ Quick Summary & Revision Capsule
- 6-8 ultra-crisp bullet points for rapid 2-minute revision before the exam.

## 5. 🚨 Exam Traps & Real Previous Year Questions (PYQ Bank)
- Top examiner traps, limiting cases, & NCERT exceptions for {effective_exam_label}.
- {pyq_mandatory_rule}

## 6. 🏁 Finish
- End with a crisp 2-line mastery verification checklist.

MATH RULE: Use $ for inline math and $$ for block math. NEVER use \\( or \\).
"""
    with st.spinner(f"🧠 Building Complete 6-Step Topper Notes for {effective_exam_label}..."):
        notes, err = generate_ai(prompt, temperature=0.2, max_tokens=8192)
        if notes:
            if not re.search(r"##\s*6\.|🏁", notes):
                cont_prompt = f"""
The following topper notes were cut off before finishing all 6 sections.
Continue seamlessly from the exact last line below and COMPLETE the remaining sections (up to `## 6. 🏁 Finish`, including Section 4 Summary and Section 5 Real PYQ Bank if missing). Do NOT repeat what is already written.

ALREADY WRITTEN NOTES (END PART):
{notes[-3500:]}
"""
                more_notes, _ = generate_ai(cont_prompt, temperature=0.2, max_tokens=4096)
                if more_notes:
                    notes = notes.rstrip() + "\n\n" + more_notes.lstrip()

            st.session_state.study_notes = clean_math_formatting(notes)
            st.session_state.topic_context = source_text
            st.success(f"✅ Complete {effective_exam_label} Topper Notes Ready!")
        else:
            st.error(err)

# ==========================================
# 📖 DISPLAY CLEAN NOTES, EXPORT & 100% RELIABLE DOUBT SOLVER
# ==========================================
if st.session_state.study_notes:
    st.markdown('<div class="auronix-notes-box">', unsafe_allow_html=True)
    st.markdown(st.session_state.study_notes)
    st.markdown('</div>', unsafe_allow_html=True)

    st.caption("💡 **For Exact PDF:** Download the **As-It-Is Calligraphy Sheet**, open it in Chrome/Brave, and tap **🖨️ Save as Exact PDF** — every formula, table, and font stays 100% identical!")
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
    # 🤖 100% RELIABLE AI DOUBT SOLVER (MOBILE-FIRST FORM)
    # ==========================================
    st.divider()
    with st.expander("🤖 Auronix Precision Doubt Solver (Tap Here to Ask Any Doubt)", expanded=True):
        st.caption(f"🎯 Precision Mode Locked (`temp=0.05`) · Context: **{st.session_state.selected_exam}**")
        with st.form("auronix_doubt_form"):
            doubt = st.text_input("Type your exact concept, formula, or PYQ doubt from these notes:", key="auronix_doubt_input")
            ask_clicked = st.form_submit_button("💡 Solve Doubt With Precision", use_container_width=True)
        if ask_clicked:
            if not doubt.strip():
                st.warning("⚠️ Please type your doubt first!")
            else:
                b_prompt = f"""
You are a strict, 100% accurate academic doubt-solving mentor for {st.session_state.selected_exam}.
Language: {st.session_state.selected_lang}.

RULES (ZERO FLUCTUATION / ZERO GUESSING):
1. Check the STUDY NOTES below for the exact concept/formula.
2. Answer the student's doubt directly in 3 structured parts:
   - **🎯 Direct Answer:** (Exact, crisp 1-2 line answer)
   - **🧠 Step-by-Step Logic / Derivation:** (Clear reasoning with proper `$` math)
   - **💡 Real-World / Exam Application:** (1-line scientifically accurate application)
3. Maintain a serious, encouraging mentor tone.

STUDY NOTES:
{st.session_state.study_notes[:12000]}

STUDENT DOUBT:
{doubt.strip()}
"""
                with st.spinner("Solving with 100% precision..."):
                    ans, err = generate_ai(b_prompt, temperature=0.05, max_tokens=2048)
                    if ans:
                        st.session_state.doubt_answer = clean_math_formatting(ans)
                    else:
                        st.error(err)
        if st.session_state.doubt_answer:
            st.success(st.session_state.doubt_answer)

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

CRITICAL DIFFICULTY & QUALITY RULES:
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
                raw, err = generate_ai(qprompt, json_mode=True, temperature=0.2, max_tokens=6000)
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
                answer, err = generate_ai(qprompt, temperature=0.2, max_tokens=6000)
            if answer:
                st.session_state.qa_output = clean_math_formatting(answer)

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
            raw, err = generate_ai(f_prompt, json_mode=True, temperature=0.2, max_tokens=4096)
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
