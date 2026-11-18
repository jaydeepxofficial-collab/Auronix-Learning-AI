"""Auronix learningAI V2.6 — Strict Hardcoded Cascade & Round Robot"""
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
# 🎨 UI & ROUND ROBOT CSS
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
  <div class="auronix-badge">⚡ Stable Engine Active</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 STRICT HARDCODED ENGINE (NO GUESSING)
# ==========================================
def generate_ai(prompt: str, json_mode: bool = False):
    errors = []
    
    # 1. GROQ STRICT MODELS
    if GROQ_API_KEY and Groq:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            # Only exact chat models, no guard models
            groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
            
            for m in groq_models:
                try:
                    kwargs = {"model": m, "messages": [{"role": "system", "content": "You are Auronix learningAI, an expert IIT-JEE mentor. Always write detailed markdown notes. Do not output just math."}, {"role": "user", "content": prompt}], "temperature": 0.3}
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}
                    res = client.chat.completions.create(**kwargs)
                    return res.choices[0].message.content, None
                except Exception as e:
                    errors.append(f"Groq {m} fail: {str(e)}")
                    continue
        except Exception as e:
            errors.append(f"Groq API Error: {str(e)}")

    # 2. GEMINI STRICT MODELS
    if GEMINI_API_KEY and genai:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # Including 3.8 just in case the API demands it again
            gemini_models = ["gemini-1.5-flash", "gemini-3.8-flash", "gemini-1.5-pro"]
            
            for m in gemini_models:
                try:
                    model = genai.GenerativeModel(m)
                    res = model.generate_content(prompt)
                    return res.text, None
                except Exception as e:
                    errors.append(f"Gemini {m} fail: {str(e)}")
                    continue
        except Exception as e:
            errors.append(f"Gemini API Error: {str(e)}")

    if not GROQ_API_KEY and not GEMINI_API_KEY:
        return None, "❌ API Keys are missing in Streamlit Secrets!"
    
    return None, f"❌ Engine Failure. Logs: {' | '.join(errors)}"

# ==========================================
# 💾 DATABASE & STATE
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY, type TEXT, topic TEXT, score REAL)")
    conn.commit()
    return conn

init_db()

for key in ["study_notes", "quiz_data", "qa_output", "buddy_chat", "flashcards"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ["study_notes", "qa_output"] else []

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
                st.error("❌ Captions unavailable for this video.")
        else:
            st.error("❌ Invalid URL or missing package.")

# PROCESS GENERATION
if source_text:
    prompt = f"""
    You are Auronix learningAI, an expert AI mentor. 
    Language: {lang_choice}. 
    Topic: {source_text[:15000]}. 
    Task: {output_type}. 
    
    CRITICAL INSTRUCTION: You MUST output a complete, highly detailed, beautifully formatted Markdown study guide. 
    Do NOT output just a calculation or a single line. Use headings (##), bullet points, and LaTeX for formulas.
    """
    with st.spinner("🧠 Connecting to AI..."):
        notes, err = generate_ai(prompt)
        if notes:
            st.session_state.study_notes = notes
            st.success("✅ Guide Ready!")
        else:
            st.error(err)

# DISPLAY NOTES ON SCREEN & PDF BUTTON
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
                    story.append(Paragraph(clean, styles['BodyText']))
            doc.build(story)
            st.download_button("📄 Download PDF Notes", data=buffer.getvalue(), file_name="Auronix_Notes.pdf", mime="application/pdf", use_container_width=True)
        except Exception:
            pass

    st.divider()
    
    # FLASHCARDS
    st.markdown("### 🗂️ Smart Flashcards")
    if st.button("✨ Generate 10 Flashcards", use_container_width=True):
        f_prompt = f"Respond ONLY with valid JSON. Create 10 short flashcards based on these notes. Language {lang_choice}. Return JSON format EXACTLY like this: {{\"cards\": [{{\"front\": \"question\", \"back\": \"answer\"}}]}}. Notes: {st.session_state.study_notes[:5000]}"
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
            with st.expander(f"Card {i+1}: {card.get('front', '')}"):
                st.write(card.get('back', ''))

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
            b_prompt = f"Answer this doubt based on the notes briefly in {lang_choice}. Doubt: {doubt}. Notes: {st.session_state.study_notes[:5000]}"
            with st.spinner("Thinking..."):
                ans, err = generate_ai(b_prompt)
                if ans:
                    st.success(ans)
                else:
                    st.error(err)
