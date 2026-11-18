"""Auronix learningAI V2.8 — The Complete Masterpiece (Math Fix + Tests Restored)"""
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

st.set_page_config(page_title="Auronix learningAI", page_icon="🦁", layout="centered")

DB_PATH = "auronix.db"

def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "").strip()
    except Exception:
        return os.getenv(name, "").strip()

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# ==========================================
# 🎨 UI & STRICT ROUND ROBOT CSS
# ==========================================
st.markdown("""
<style>
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
.block-container {padding-top:1.4rem; padding-bottom:5rem; max-width:1050px;}
.auronix-hero {background:linear-gradient(135deg,rgba(255,165,0,.16),rgba(255,94,0,.055));border:1px solid rgba(255,165,0,.38);border-radius:20px;padding:23px 20px;margin-bottom:22px;text-align:center;}
.auronix-title {background:linear-gradient(90deg,#FFB300,#FF6F00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:clamp(2rem,6vw,2.65rem);font-weight:950;margin:0;}
.auronix-badge {display:inline-block;background:rgba(255,165,0,.16);color:#FFB300;font-size:12px;font-weight:750;padding:6px 14px;border-radius:20px;margin-top:10px;border:1px solid rgba(255,165,0,.32);}
div.stButton>button {background:linear-gradient(90deg,#FF9800,#F57C00)!important;color:white!important;font-weight:750!important;border:0!important;border-radius:12px!important;}

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

st.markdown(f"""
<div class="auronix-hero">
  <div class="auronix-title">🦁 Auronix learningAI</div>
  <p style="color:#B0B8C4;font-size:15px;margin:9px 0 0">AI-powered exam notes, formula sheets, practice tests & smart revision.</p>
  <div class="auronix-badge">⚡ Smart Radar Engine Active</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 SMART RADAR ENGINE
# ==========================================
def generate_ai(prompt: str, json_mode: bool = False):
    errors = []
    
    if GROQ_API_KEY and Groq:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            live_models = client.models.list().data
            valid_chat_models = [m.id for m in live_models if "guard" not in m.id.lower() and "whisper" not in m.id.lower()]
            
            if valid_chat_models:
                for model_id in valid_chat_models:
                    try:
                        kwargs = {
                            "model": model_id, 
                            "messages": [
                                {"role": "system", "content": "You are Auronix learningAI, an expert IIT-JEE mentor. Always write detailed markdown notes. Use $ for inline math and $$ for block math. Do NOT use \\( or \\)."}, 
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
                    model = genai.GenerativeModel(m, system_instruction="You are Auronix learningAI. Use $ for inline math and $$ for block math. Do not use \\( or \\).")
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
for key in ["study_notes", "quiz_data", "quiz_submitted", "qa_output", "buddy_chat", "flashcards"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ["study_notes", "qa_output"] else (False if key == "quiz_submitted" else (None if key == "quiz_data" else []))

# ==========================================
# 🎓 STUDY STUDIO UI
# ==========================================
mode = st.radio("1️⃣ Choose input method", ["📝 Topic Name", "🔗 YouTube Link"], horizontal=True)
col1, col2 = st.columns(2)
with col1:
    output_type = st.selectbox("2️⃣ Output Type", ["📚 Deep Notes", "⚡ Formula Sheet", "📖 Detailed Explanation"])
with col2:
    lang_choice = st.selectbox("3️⃣ Language", ["English", "Hinglish"])

source_text = ""
if mode == "📝 Topic Name":
    manual_input = st.text_area("📝 Enter chapter/topic", height=100)
    if st.button("✨ Generate Notes Now", use_container_width=True) and manual_input:
        source_text = manual_input
elif mode == "🔗 YouTube Link":
    yt_url = st.text_input("🔗 Paste YouTube link")
    if st.button("✨ Extract & Generate", use_container_width=True) and yt_url:
        vid = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", yt_url)
        if vid and YouTubeTranscriptApi:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(vid.group(1), languages=["hi", "en", "en-IN"])
                source_text = " ".join([t['text'] for t in transcript])
            except Exception:
                st.error("❌ Captions unavailable.")
        else:
            st.error("❌ Invalid URL.")

# PROCESS GENERATION
if source_text:
    # Reset old test data
    for state_key in list(st.session_state.keys()):
        if state_key.startswith("auronix_q_"):
            del st.session_state[state_key]
    st.session_state.quiz_data = None
    st.session_state.qa_output = ""
    st.session_state.quiz_submitted = False

    prompt = f"""
    You are Auronix learningAI. Language: {lang_choice}. Topic: {source_text[:15000]}. Task: {output_type}. 
    CRITICAL INSTRUCTION: Output a detailed, beautiful Markdown study guide. 
    MATH RULE: You MUST use $ for inline math (e.g., $x=2$) and $$ for block math. NEVER use \\( or \\).
    """
    with st.spinner("🧠 Scanning for LIVE AI servers..."):
        notes, err = generate_ai(prompt)
        if notes:
            # Final Math Backup Fix (Replaces brackets if AI still uses them)
            notes = notes.replace("\\(", "$").replace("\\)", "$").replace("\\[", "$$").replace("\\]", "$$")
            st.session_state.study_notes = notes
            st.session_state.topic_context = source_text
            st.success("✅ Guide Ready!")
        else:
            st.error(err)

# DISPLAY NOTES & PDF BUTTON
if st.session_state.study_notes:
    st.markdown(st.session_state.study_notes)
    
    if REPORTLAB_OK:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, title="Auronix Notes")
            styles = getSampleStyleSheet()
            story = [Paragraph("Auronix Study Notes", styles['Title']), Spacer(1, 12)]
            for line in st.session_state.study_notes.split('\n'):
                if line.strip():
                    clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", html.escape(line))
                    # Remove $ for PDF rendering
                    clean = clean.replace("$", "")
                    story.append(Paragraph(clean, styles['BodyText']))
            doc.build(story)
            st.download_button("📄 Download PDF Notes", data=buffer.getvalue(), file_name="Auronix_Notes.pdf", mime="application/pdf", use_container_width=True)
        except Exception:
            pass

    # ==========================================
    # 🧠 PRACTICE TEST (RESTORED!)
    # ==========================================
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
        # Reset previous test
        for state_key in list(st.session_state.keys()):
            if state_key.startswith("auronix_q_"):
                del st.session_state[state_key]
        st.session_state.quiz_data = None
        st.session_state.quiz_submitted = False
        st.session_state.qa_output = ""
        
        if test_format == "Interactive MCQs":
            qprompt = f"Create exactly {num_q} multiple-choice questions for {exam_type}, difficulty {diff_level}, language {lang_choice}. Return JSON object with key 'questions', array of objects containing 'q', 'options' (four strings), 'answer' (matches one option), 'explanation'. Return JSON ONLY."
            with st.spinner(f"Preparing {num_q} {exam_type} MCQs..."):
                raw, err = generate_ai(qprompt, json_mode=True)
            if raw:
                try:
                    clean_raw = re.sub(r"```(?:json)?|```", "", raw).strip()
                    obj = json.loads(clean_raw)
                    valid = [item for item in obj.get("questions", []) if isinstance(item.get("options"), list) and len(item["options"]) == 4]
                    st.session_state.quiz_data = valid
                except Exception:
                    st.error("Invalid quiz format. Please retry.")
            else:
                st.error(err)
        else:
            qprompt = f"Create exactly {num_q} subjective questions with step-by-step model answers for {exam_type}, difficulty {diff_level}, language {lang_choice}. Use clean Markdown."
            with st.spinner("Preparing written questions..."):
                answer, err = generate_ai(qprompt)
            if answer:
                st.session_state.qa_output = answer

    # SHOW INTERACTIVE TEST
    if st.session_state.quiz_data:
        st.markdown(f"#### 📝 Live Test · {len(st.session_state.quiz_data)} questions")
        marks_per_correct = 4 if exam_type in ("NEET", "JEE Main", "JEE Advanced") else 1
        marks_per_wrong = 1 if exam_type in ("NEET", "JEE Main", "JEE Advanced") else 0
        
        with st.form("auronix_quiz_form"):
            for idx, item in enumerate(st.session_state.quiz_data):
                # Fix math brackets for questions too
                q_text = item['q'].replace("\\(", "$").replace("\\)", "$")
                st.markdown(f"**Q{idx + 1}. {q_text}**")
                
                # Fix options
                clean_opts = [opt.replace("\\(", "$").replace("\\)", "$") for opt in item["options"]]
                st.radio(f"Answer Q{idx + 1}", clean_opts, key=f"auronix_q_{idx}", index=None, label_visibility="collapsed")
            
            submitted = st.form_submit_button("📊 Submit & Check Score", use_container_width=True)
            
        if submitted:
            correct = wrong = attempted = 0
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"auronix_q_{idx}")
                clean_ans = item["answer"].replace("\\(", "$").replace("\\)", "$")
                if chosen:
                    attempted += 1
                    if chosen == clean_ans: correct += 1
                    else: wrong += 1
                    
            raw_score = correct * marks_per_correct - wrong * marks_per_wrong
            max_score = len(st.session_state.quiz_data) * marks_per_correct
            st.session_state.quiz_submitted = True
            st.success(f"🏆 Score: {raw_score} / {max_score} (Correct: {correct}, Wrong: {wrong})")
            
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"auronix_q_{idx}")
                clean_ans = item["answer"].replace("\\(", "$").replace("\\)", "$")
                if chosen == clean_ans:
                    st.markdown(f"✅ **Q{idx+1}: Correct** — {clean_ans}")
                else:
                    st.markdown(f"❌ **Q{idx+1}:** Your answer: `{chosen or 'Not attempted'}` · Correct: `{clean_ans}`")
                
                if item.get("explanation"):
                    st.caption(item["explanation"].replace("\\(", "$").replace("\\)", "$"))

    # SHOW SUBJECTIVE TEST
    if st.session_state.qa_output:
        st.markdown("#### 📖 Subjective practice questions")
        clean_qa = st.session_state.qa_output.replace("\\(", "$").replace("\\)", "$")
        st.markdown(clean_qa)

    # ==========================================
    # 🗂️ FLASHCARDS
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ Smart Flashcards")
    if st.button("✨ Generate 10 Flashcards", use_container_width=True):
        f_prompt = f"Respond ONLY with valid JSON. Create 10 short flashcards. Return JSON format EXACTLY like this: {{\"cards\": [{{\"front\": \"question\", \"back\": \"answer\"}}]}}."
        with st.spinner("Making flashcards..."):
            raw, err = generate_ai(f_prompt, json_mode=True)
            if raw:
                try:
                    clean_raw = re.sub(r"```(?:json)?|```", "", raw).strip()
                    st.session_state.flashcards = json.loads(clean_raw).get("cards", [])
                except:
                    st.error("JSON Parsing Error.")
            else:
                st.error(err)
                
    if st.session_state.flashcards:
        for i, card in enumerate(st.session_state.flashcards):
            clean_front = card.get('front', '').replace("\\(", "$").replace("\\)", "$")
            clean_back = card.get('back', '').replace("\\(", "$").replace("\\)", "$")
            with st.expander(f"Card {i+1}: {clean_front}"):
                st.write(clean_back)

# ==========================================
# 🤖 EMO ROBOT BUDDY
# ==========================================
with st.popover(" "):
    st.markdown("<h4 style='color:#00E5FF'>🤖 Auronix AI Buddy</h4>", unsafe_allow_html=True)
    if not st.session_state.study_notes:
        st.info("Pehle notes generate kar, fir doubt poochh!")
    else:
        doubt = st.text_input("Ask a doubt from the notes:")
        if st.button("💡 Solve Doubt", use_container_width=True) and doubt:
            b_prompt = f"Answer this doubt based on the notes briefly. Doubt: {doubt}"
            with st.spinner("Thinking..."):
                ans, err = generate_ai(b_prompt)
                if ans:
                    st.success(ans.replace("\\(", "$").replace("\\)", "$"))
                else:
                    st.error(err)
