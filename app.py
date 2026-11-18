"""Auronix learningAI V3.0 — Exam/Board Selector, NCERT/PYQ Lock, Desi Humour & In-Context Engine"""
import json
import os
import re
import sqlite3
import html
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
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

st.set_page_config(page_title="Auronix learningAI V3.0", page_icon="🦁", layout="centered")

DB_PATH = "auronix.db"

def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "").strip()
    except Exception:
        return os.getenv(name, "").strip()

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# ==========================================
# 🎨 UI, BIG HEADINGS & STRICT ROUND ROBOT CSS
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
    font-size: 2.1rem !important;
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
  <p style="color:#B0B8C4;font-size:15px;margin:9px 0 0">NCERT & PYQ Locked Notes · Desi Examples · Exam-Level Tests & Smart Flashcards</p>
  <div class="auronix-badge">⚡ V3.0 Smart Radar Engine · Boards · JEE · NEET</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 UNTOUCHED SMART RADAR ENGINE
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

def generate_ai(prompt: str, json_mode: bool = False):
    errors = []
    sys_msg = (
        "You are Auronix learningAI, India's top Board, JEE, and NEET educator. "
        "Follow the user's selected exam level, syllabus boundary, and language strictly. "
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
                            "temperature": 0.3
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
                    model = genai.GenerativeModel(m, system_instruction=sys_msg)
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
    "selected_lang": "Hinglish (Desi & Easy Concept Clarity)"
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================================
# 🎓 V3.0 CUSTOMIZATION CONTROL PANEL
# ==========================================
st.markdown("### 🎯 Step 1: Customize Your Exam & Study Style")

c1, c2 = st.columns(2)
with c1:
    target_exam = st.selectbox(
        "1️⃣ Target Exam",
        [
            "🏫 Class 11/12 Boards (CBSE / State)",
            "🩺 NEET (Strictly NCERT Bio/Chem/Phys)",
            "⚙️ JEE Main (NCERT + Concept Tricks & PYQs)",
            "🚀 JEE Advanced (Deep Derivations & Multi-Concept)"
        ]
    )
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
            "📚 Crisp Topper Revision Notes",
            "⚡ Complete Formula, Reactions & Trick Sheet",
            "📖 Zero-to-Hero Deep Explanation"
        ]
    )
with c4:
    lang_choice = st.selectbox(
        "4️⃣ Explanation Language",
        [
            "Hinglish (Desi & Easy Concept Clarity)",
            "English (100% Exam Ready)"
        ]
    )

st.divider()
st.markdown("### 📝 Step 2: Enter Your Topic or Lecture")
mode = st.radio("Choose input method", ["📝 Topic / Chapter Name", "🔗 YouTube Lecture Link"], horizontal=True)

source_text = ""
if mode == "📝 Topic / Chapter Name":
    manual_input = st.text_area(
        "📝 Just write the topic & class (e.g., 'Cell the Unit of Life Class 11' or 'Rotational Motion Class 11')",
        height=90
    )
    if st.button("✨ Generate Crisp Exam Notes", use_container_width=True) and manual_input.strip():
        source_text = manual_input.strip()
elif mode == "🔗 YouTube Lecture Link":
    yt_url = st.text_input("🔗 Paste YouTube lecture link")
    if st.button("✨ Extract Lecture & Generate Notes", use_container_width=True) and yt_url.strip():
        vid = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", yt_url.strip())
        if vid and YouTubeTranscriptApi:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(vid.group(1), languages=["hi", "en", "en-IN"])
                source_text = " ".join([t["text"] for t in transcript])
            except Exception:
                st.error("❌ Captions unavailable for this video. Try Topic Name mode!")
        else:
            st.error("❌ Invalid YouTube URL.")

# ==========================================
# 🧠 V3.0 STRICT SYLLABUS-BOUND NOTE GENERATOR
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

    prompt = f"""
You are Auronix learningAI V3.0, India's best educator for {target_exam}.

USER SELECTION (FOLLOW 100% STRICTLY):
- Target Exam Level: {target_exam}
- Content Basis: {content_basis}
- Output Style: {output_type}
- Language: {lang_choice}
- Student Topic / Transcript: {source_text[:15000]}

STRICT SYLLABUS & QUALITY RULES (DO NOT VIOLATE):
1. NO RANDOM ENCYCLOPEDIA GYAN: Stay 100% inside the Indian Class 11/12 NCERT & {target_exam} syllabus boundary. If the topic is Biology (like Cell), do NOT dump irrelevant PhD or general internet history—teach ONLY exact NCERT lines, scientists, dates, diagrams/structures, and exam points.
2. RESPECT THE SELECTED EXAM: Do NOT force JEE content if the user selected NEET or Boards. Tailor every single point, formula, and example strictly to {target_exam} and {content_basis}.
3. BIG, CLEAN HEADINGS: Use large Markdown headings (`#` for Main Title, `##` for Major Topics, `###` for Sub-topics) with emojis so the student loves reading it.
4. DESI HUMOUR & REAL-LIFE EXAMPLE FOR EVERY TOPIC: After explaining EVERY major heading/concept, you MUST include a bullet called:
   - **😂 Desi Relatable Example:** (Explain that exact concept with a fun, memorable Indian daily-life or student-life example with light humour + a concrete solved example so the student never forgets it!)
5. EXAM TRAPS & PYQ RADAR: Include a dedicated section `## 🚨 Exam Traps & PYQ Radar` highlighting exact mistakes students make in {target_exam} and what questions are repeatedly asked in PYQs.
6. ZERO MERGING / CLEAN LAYOUT: Never merge questions into theory paragraphs. Keep definitions, formulas, examples, and traps cleanly separated with bullet points.
7. MATH RULE: Use $ for inline math and $$ for block math. NEVER use \\( or \\).
"""
    with st.spinner(f"🧠 Preparing {target_exam} ({content_basis}) Notes..."):
        notes, err = generate_ai(prompt)
        if notes:
            st.session_state.study_notes = clean_math_formatting(notes)
            st.session_state.topic_context = source_text
            st.success(f"✅ {target_exam} Guide Ready!")
        else:
            st.error(err)

# ==========================================
# 📖 DISPLAY CLEAN NOTES & OPTIONAL PDF
# ==========================================
if st.session_state.study_notes:
    st.markdown('<div class="auronix-notes-box">', unsafe_allow_html=True)
    st.markdown(st.session_state.study_notes)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if REPORTLAB_OK:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, title="Auronix Notes")
            styles = getSampleStyleSheet()
            story = [Paragraph(f"Auronix Study Notes ({st.session_state.selected_exam})", styles["Title"]), Spacer(1, 12)]
            for line in st.session_state.study_notes.split("\n"):
                if line.strip():
                    clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html.escape(line))
                    clean = clean.replace("$", "")
                    story.append(Paragraph(clean, styles["BodyText"]))
            doc.build(story)
            st.download_button(
                "📄 Download PDF Notes (Optional)",
                data=buffer.getvalue(),
                file_name="Auronix_Notes.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception:
            pass

    # ==========================================
    # 🧠 STRICT IN-CONTEXT PRACTICE TEST
    # ==========================================
    st.divider()
    st.markdown("### 🧠 Test Your Knowledge (Strictly From Above Notes)")
    st.caption(f"🎯 Locked to: **{st.session_state.selected_exam}** · **{st.session_state.selected_basis}**")

    q1, q2, q3 = st.columns(3)
    with q1:
        num_q = st.selectbox("Questions", [5, 10, 15, 20], index=1)
    with q2:
        diff_level = st.selectbox("Difficulty", ["Exam Standard", "Easy Foundation", "Hard / Tricky", "Mixed PYQ Style"])
    with q3:
        test_format = st.selectbox("Format", ["Interactive MCQs", "Subjective Q&A (Boards/Written)"])
    
    if st.button("🚀 Generate Test From These Notes", use_container_width=True):
        for state_key in list(st.session_state.keys()):
            if state_key.startswith("auronix_q_"):
                del st.session_state[state_key]
        st.session_state.quiz_data = None
        st.session_state.quiz_submitted = False
        st.session_state.qa_output = ""
        
        if test_format == "Interactive MCQs":
            qprompt = f"""
You MUST create {num_q} high-quality exam MCQs STRICTLY AND EXCLUSIVELY from the STUDY NOTES provided below.

CRITICAL RULES:
1. DO NOT invent random math questions or out-of-context questions. Every single question MUST test a concept, fact, formula, or trap present in the STUDY NOTES below.
2. Match the exact level of: {st.session_state.selected_exam} ({diff_level}).
   - If NEET is selected: Ask NCERT statement-based, assertion-reason, match-the-following, or direct NEET-level numericals.
   - If JEE Main/Advanced is selected: Ask conceptual & analytical application questions from the notes.
   - If Boards is selected: Ask CBSE competency-based MCQs from the notes.
3. Language: {st.session_state.selected_lang}.
4. Do NOT merge question text and options. Keep them completely clean.
5. Return ONLY a valid JSON object with key "questions", which is a list of objects each having:
   - "q": Question string
   - "options": List of EXACTLY 4 option strings
   - "answer": Exact string matching one of the 4 options
   - "explanation": Step-by-step explanation referencing the notes

STUDY NOTES TO GENERATE QUESTIONS FROM:
{st.session_state.study_notes[:12000]}
"""
            with st.spinner(f"Preparing {num_q} strict in-context MCQs for {st.session_state.selected_exam}..."):
                raw, err = generate_ai(qprompt, json_mode=True)
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
Create {num_q} subjective exam questions (Short Answer, Long Answer & Case/Application Based) with clean step-by-step Marking Scheme answers STRICTLY from the STUDY NOTES below.
Target Level: {st.session_state.selected_exam} ({diff_level}).
Language: {st.session_state.selected_lang}.
Keep questions and answers cleanly separated.

STUDY NOTES:
{st.session_state.study_notes[:12000]}
"""
            with st.spinner("Preparing written exam questions from your notes..."):
                answer, err = generate_ai(qprompt)
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
CRITICAL RULE: Do NOT generate random math cards or outside topics! If the notes are about Biology, Chemistry, or Physics, every single card MUST come directly from the definitions, formulas, NCERT lines, or traps written in the STUDY NOTES below.
Target Exam: {st.session_state.selected_exam}.
Language: {st.session_state.selected_lang}.
Return JSON format EXACTLY like this:
{{"cards": [{{"front": "Crisp question / term / formula prompt from notes", "back": "Crisp answer / trick from notes"}}]}}

STUDY NOTES:
{st.session_state.study_notes[:10000]}
"""
        with st.spinner("Making topic-locked flashcards from your notes..."):
            raw, err = generate_ai(f_prompt, json_mode=True)
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
# 🤖 EMO ROBOT BUDDY (UNTOUCHED & CONTEXT LOCKED)
# ==========================================
with st.popover(" "):
    st.markdown("<h4 style='color:#00E5FF'>🤖 Auronix AI Buddy</h4>", unsafe_allow_html=True)
    if not st.session_state.study_notes:
        st.info("Pehle notes generate kar, fir doubt poochh!")
    else:
        doubt = st.text_input("Ask any doubt from these notes:")
        if st.button("💡 Solve Doubt", use_container_width=True) and doubt:
            b_prompt = f"""
Answer the student's doubt clearly using a fun desi example in {st.session_state.selected_lang} for {st.session_state.selected_exam}.
Base your answer on these notes:
{st.session_state.study_notes[:8000]}

Student Doubt: {doubt}
"""
            with st.spinner("Thinking..."):
                ans, err = generate_ai(b_prompt)
                if ans:
                    st.success(clean_math_formatting(ans))
                else:
                    st.error(err)
