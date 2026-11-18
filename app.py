import streamlit as st
import streamlit.components.v1 as components
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
import json

st.set_page_config(page_title="Auronix learningAI", page_icon="🦁", layout="centered")

# Google Search Console Verification Tag
st.markdown('<meta name="google-site-verification" content="AjHF7eNYXQYzd50KtS5DVJR3olMBc2UjYkBiw95e_Xs" />', unsafe_allow_html=True)

# Custom Royal SaaS UI & Cute Floating Robot CSS
st.markdown("""
<style>
    /* Hide default Streamlit branding for pure SaaS look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Hero Banner Styling */
    .auronix-hero {
        background: linear-gradient(135deg, rgba(255, 165, 0, 0.14) 0%, rgba(255, 94, 0, 0.06) 100%);
        border: 1px solid rgba(255, 165, 0, 0.35);
        border-radius: 18px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 25px rgba(255, 140, 0, 0.08);
    }
    .auronix-title {
        background: linear-gradient(90deg, #FFB300, #FF6F00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }
    .auronix-badge {
        display: inline-block;
        background: rgba(255, 165, 0, 0.18);
        color: #FFB300;
        font-size: 11.5px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin-top: 8px;
        border: 1px solid rgba(255, 165, 0, 0.3);
    }

    /* Glowing Primary Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #FF9800 0%, #F57C00 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.55rem 1.2rem !important;
        box-shadow: 0 4px 14px rgba(255, 152, 0, 0.3) !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(255, 152, 0, 0.45) !important;
    }

    /* Floating Cute Robot Popover Button in Bottom-Right Corner */
    div[data-testid="stPopover"] {
        position: fixed !important;
        bottom: 22px !important;
        right: 22px !important;
        z-index: 99999 !important;
    }
    div[data-testid="stPopover"] > button {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #FFA500 !important;
        border-radius: 50px !important;
        padding: 10px 16px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 25px rgba(255, 165, 0, 0.38) !important;
        animation: buddyFloat 2.8s ease-in-out infinite !important;
    }
    div[data-testid="stPopover"] > button:hover {
        transform: scale(1.05) !important;
        border-color: #FFD54F !important;
    }
    @keyframes buddyFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
</style>
""", unsafe_allow_html=True)

# Royal Auronix Header + Optional Lion Roar Player
col_hero, col_roar = st.columns([4, 1])
with col_hero:
    st.markdown("""
    <div class="auronix-hero">
        <div class="auronix-title">🦁 Auronix learningAI</div>
        <p style="color: #B0B8C4; font-size: 14.5px; margin: 6px 0 0 0;">
            AI-Powered Deep Exam Notes, Formula Sheets & Smart Practice Tests in Seconds!
        </p>
        <div class="auronix-badge">⚡ JEE • NEET • Class 11 & 12 • Smart AI Tutor</div>
    </div>
    """, unsafe_allow_html=True)

with col_roar:
    # Optional interactive Lion Roar sound button (Synthesized Web Audio Roar - zero external broken links!)
    components.html("""
    <div style="display:flex; justify-content:center; align-items:center; height:105px;">
        <button onclick="playLionRoar()" title="Tap for Auronix Lion Roar!" style="
            background: linear-gradient(135deg, #FFA500, #E65100);
            color: white;
            border: none;
            border-radius: 16px;
            padding: 10px 12px;
            font-weight: 700;
            font-size: 12px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(255,165,0,0.35);
            transition: 0.2s;
            text-align: center;
        ">🦁<br>🔊 Roar</button>
    </div>
    <script>
    function playLionRoar() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc1 = ctx.createOscillator();
            const osc2 = ctx.createOscillator();
            const gain = ctx.createGain();
            const filter = ctx.createBiquadFilter();

            osc1.type = 'sawtooth';
            osc2.type = 'triangle';
            osc1.frequency.setValueAtTime(115, ctx.currentTime);
            osc1.frequency.exponentialRampToValueAtTime(52, ctx.currentTime + 1.3);
            osc2.frequency.setValueAtTime(85, ctx.currentTime);
            osc2.frequency.exponentialRampToValueAtTime(40, ctx.currentTime + 1.3);

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(340, ctx.currentTime);
            filter.frequency.exponentialRampToValueAtTime(140, ctx.currentTime + 1.3);

            gain.gain.setValueAtTime(0.01, ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0.45, ctx.currentTime + 0.18);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.35);

            osc1.connect(filter);
            osc2.connect(filter);
            filter.connect(gain);
            gain.connect(ctx.destination);

            osc1.start();
            osc2.start();
            osc1.stop(ctx.currentTime + 1.4);
            osc2.stop(ctx.currentTime + 1.4);
        } catch(e) {}
    }
    </script>
    """, height=115)

api_key = st.secrets.get("GEMINI_API_KEY", "")

# Session State Initialization
for key, default in [
    ("study_notes", ""),
    ("topic_context", ""),
    ("lang_saved", "English (Exam Ready)"),
    ("quiz_data", None),
    ("qa_output", ""),
    ("quiz_submitted", False),
    ("buddy_chat", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default

def get_video_id(url):
    pattern = r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_any_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            data = transcript.fetch()
            return " ".join([item['text'] for item in data])
    except Exception:
        pass
    try:
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'en-IN'])
        return " ".join([item['text'] for item in data])
    except Exception:
        return None

def get_cascade_models():
    priority = [
        "models/gemini-3.8-flash",
        "models/gemini-3.8-flash-lite",
        "models/gemma-3-27b-it",
        "models/gemma-3-12b-it",
        "models/gemma-3-4b-it"
    ]
    blocked_words = ("tts", "audio", "image", "vision", "embedding", "aqa", "robotics")
    try:
        available = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
            and not any(bad in m.name.lower() for bad in blocked_words)
        ]
        ordered = [m for m in priority if m in available]
        others = [m for m in available if m not in ordered and ('gemini' in m.lower() or 'gemma' in m.lower())]
        return ordered + others if (ordered or others) else priority
    except Exception:
        return priority

def extract_non_thought_text(response_obj):
    text_pieces = []
    try:
        if getattr(response_obj, "candidates", None):
            for cand in response_obj.candidates:
                if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                    for p in cand.content.parts:
                        if getattr(p, "thought", False):
                            continue
                        if getattr(p, "text", None):
                            text_pieces.append(p.text)
            return "".join(text_pieces)
    except Exception:
        pass
    try:
        return response_obj.text or ""
    except Exception:
        return ""

def strip_leaked_thinking(raw_text, mode="notes"):
    """ABSOLUTE GUILLOTINE METHOD: Cuts everything before the exact marker!"""
    if not raw_text:
        return ""
    text = raw_text.strip()
    
    if "🚫 STRICT FILTER" in text:
        return text[text.find("🚫 STRICT FILTER"):].strip()

    if mode == "buddy":
        marker = "===START_BUDDY==="
    elif mode == "notes":
        marker = "===START_NOTES==="
    else:
        marker = "===START_TEST==="

    if marker in text:
        text = text.split(marker)[-1].strip()
    else:
        text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL | re.IGNORECASE).strip()
        
    return text

def get_smart_html_download(markdown_text, title="Auronix Study Notes"):
    """Wraps output in a professional HTML document with MathJax for beautiful formulas."""
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>__TITLE__</title>
    <style>
        body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.7; max-width: 850px; margin: 0 auto; padding: 40px 20px; color: #2c3e50; background-color: #f8f9fa; }
        .document-container { background: #ffffff; padding: 40px 50px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }
        h1, h2, h3 { color: #1a252f; margin-top: 30px; padding-bottom: 10px; border-bottom: 2px solid #f1f2f6; }
        h1 { font-size: 2.2em; color: #d35400; text-align: center; border-bottom: none; }
        code { background: #fdf2e9; padding: 3px 6px; border-radius: 4px; font-family: 'Courier New', monospace; color: #e67e22; font-weight: bold; }
        pre { background: #2c3e50; padding: 20px; border-radius: 8px; overflow-x: auto; color: #ecf0f1; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }
        blockquote { border-left: 5px solid #f39c12; background: #fffaf0; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; color: #555; font-style: italic; }
        ul, ol { padding-left: 25px; margin-bottom: 20px; }
        li { margin-bottom: 8px; }
        .watermark { text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px dashed #bdc3c7; color: #7f8c8d; font-size: 0.9em; }
        .print-btn { display: block; width: 200px; margin: 0 auto 30px auto; padding: 12px; background: #e67e22; color: white; text-align: center; text-decoration: none; border-radius: 25px; font-weight: bold; cursor: pointer; border: none; box-shadow: 0 4px 6px rgba(230,126,34,0.3); transition: 0.3s; }
        .print-btn:hover { background: #d35400; transform: translateY(-2px); }
        @media print { .print-btn { display: none; } body { background: #fff; } .document-container { box-shadow: none; padding: 0; } }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
      MathJax = { tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']] } };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ Save as PDF / Print</button>
    <div class="document-container">
        <div id="content">Formatting your beautiful notes...</div>
        <div class="watermark">🚀 Generated by <b>Auronix learningAI</b> • The Ultimate Study Companion</div>
    </div>
    <textarea id="source" style="display:none;">__MARKDOWN_CONTENT__</textarea>
    <script>
        document.getElementById('content').innerHTML = marked.parse(document.getElementById('source').value);
    </script>
</body>
</html>"""
    html = html_template.replace("__TITLE__", title)
    html = html.replace("__MARKDOWN_CONTENT__", markdown_text)
    return html

def generate_with_cascade(prompt_text, clean_mode="notes"):
    genai.configure(api_key=api_key)
    models_to_try = get_cascade_models()
    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            raw_out = extract_non_thought_text(response)
            cleaned_out = strip_leaked_thinking(raw_out, mode=clean_mode)
            if cleaned_out:
                return cleaned_out, None
        except Exception as e:
            last_error = str(e)
            if any(code in last_error.lower() for code in ("429", "quota", "404", "400", "not supported")):
                continue
            return None, last_error
    return None, "BUSY"

# Input Method Selection
mode = st.radio(
    "1️⃣ Choose Input Method:",
    ["🔗 YouTube Lecture Link", "📝 Topic Name / Lecture Text"],
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    output_type = st.selectbox(
        "2️⃣ What do you want?",
        [
            "📚 Deep Topper Exam Notes & Formulas",
            "⚡ Complete Formula & Trick Sheet",
            "📖 Zero-to-Pro Detailed Explanation"
        ]
    )
with col2:
    lang_choice = st.selectbox(
        "3️⃣ Explanation Language:",
        ["English (Exam Ready)", "Hinglish (Easy Concept Clarity)"]
    )

source_text = ""
trigger = False

if mode == "🔗 YouTube Lecture Link":
    youtube_url = st.text_input("🔗 Paste Educational YouTube Lecture Link:")
    if st.button("✨ Generate Notes Now", use_container_width=True):
        if not youtube_url:
            st.warning("⚠️ Please paste a valid YouTube link first!")
            st.stop()
        if not api_key:
            st.error("❌ API Key missing in server settings.")
            st.stop()
        video_id = get_video_id(youtube_url)
        if not video_id:
            st.error("❌ Invalid YouTube URL. Please check the link.")
            st.stop()
        with st.spinner("🔍 Extracting lecture subtitles..."):
            source_text = fetch_any_transcript(video_id)
            if not source_text:
                st.warning("⚠️ Subtitles are disabled/restricted on this video. Switch to **'📝 Topic Name / Lecture Text'** above to generate instant notes anyway!")
                st.stop()
        trigger = True
else:
    manual_input = st.text_area(
        "📝 Enter Chapter/Topic Name OR Paste Lecture Notes:",
        placeholder="Example: Rotational Motion for JEE / Class 11 Work Energy Power...",
        height=120
    )
    if st.button("✨ Generate Notes Now", use_container_width=True):
        if not manual_input.strip():
            st.warning("⚠️ Please enter a topic or paste some text first!")
            st.stop()
        if not api_key:
            st.error("❌ API Key missing in server settings.")
            st.stop()
        source_text = manual_input.strip()
        trigger = True

if trigger and source_text:
    st.session_state.quiz_data = None
    st.session_state.qa_output = ""
    st.session_state.quiz_submitted = False
    st.session_state.buddy_chat = []

    if output_type == "📚 Deep Topper Exam Notes & Formulas":
        task_instruction = """Write comprehensive, deeply detailed, exam-mastery notes (minimum 800 words) with these 5 thorough sections:
1. 🎯 Core Concept Summary & Intuition 
2. 📌 Complete Definitions, Laws & Theorems 
3. 📐 Exhaustive Formula Bank & SI Units
4. 🧮 2 Solved Exam-Level Numericals
5. ⚡ Exam Topper Strategy & Common Traps"""
    elif output_type == "⚡ Complete Formula & Trick Sheet":
        task_instruction = """Write an exhaustive Formula & Trick Sheet:
- Cover EVERY single formula, standard value, and SI unit in detail.
- Include 5 high-speed exam shortcuts and 5 deadly exam traps to avoid."""
    else:
        task_instruction = """Write a complete, deep Zero-to-Pro Chapter Guide:
- Build every concept step-by-step from basic laws to advanced applications with derivations, formulas, and 3 solved examples."""

    prompt = f"""
You are Auronix learningAI. Language Style: {lang_choice}.
Topic/Input: {source_text[:12000]}

CRITICAL INSTRUCTIONS (OBEY STRICTLY):
1. DO NOT write any thinking process, persona, analysis, or filter steps.
2. You MUST start your response EXACTLY with this marker: ===START_NOTES===
3. DO NOT output a single character before the marker.
4. If the input is pure entertainment (songs, movies, gaming, vlogs), output ONLY: 🚫 STRICT FILTER: Auronix learningAI only supports educational content!

===START_NOTES===
{task_instruction}
"""
    with st.spinner("⚡ Generating Deep Topper-Level Study Notes..."):
        notes_res, err = generate_with_cascade(prompt, clean_mode="notes")
    if notes_res:
        st.session_state.study_notes = notes_res
        st.session_state.topic_context = source_text[:10000]
        st.session_state.lang_saved = lang_choice
    elif err == "BUSY":
        st.warning("⏳ All free AI engines are busy right now. Please wait 30 seconds and click Generate again!")
    elif err:
        st.error(f"❌ AI Error: {err}")

if st.session_state.study_notes:
    st.markdown("---")
    st.markdown(st.session_state.study_notes)

# Smart PDF / HTML Download Section
if st.session_state.study_notes and not st.session_state.study_notes.startswith("🚫 STRICT FILTER"):
    html_content = get_smart_html_download(st.session_state.study_notes, title="Auronix Study Notes")
    
    st.download_button(
        label="⬇️ Download Smart PDF/Doc (.html)",
        data=html_content,
        file_name="Auronix_Study_Notes.html",
        mime="text/html",
        help="Opens beautifully on any device. Just click 'Print' inside to save as a clean PDF!"
    )
    st.caption("✨ *Tip: Open the downloaded file and click 'Save as PDF' for a professional printout!*")

    st.markdown("---")
    st.markdown("### 🎯 Test Your Knowledge")
    st.caption("Apne is topic ki tayyari check karo — apna custom test banao! 🚀")

    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        num_q = st.selectbox("📊 Questions:", [10, 20, 30])
    with t_col2:
        diff_level = st.selectbox("🔥 Difficulty:", ["Easy (Basics)", "Medium (Exam Level)", "Hard (JEE / Pro)"])
    with t_col3:
        test_format = st.selectbox("📝 Format:", ["Interactive MCQs", "Questions & Answers"])

    if st.button("🚀 Generate Test Now", use_container_width=True):
        st.session_state.quiz_data = None
        st.session_state.qa_output = ""
        st.session_state.quiz_submitted = False

        if test_format == "Interactive MCQs":
            quiz_prompt = f"""
Create a {num_q}-question multiple choice quiz strictly based on this topic/content:
Topic/Content: {st.session_state.topic_context}

Difficulty Level: {diff_level}
Language: {st.session_state.lang_saved}

CRITICAL: Output ONLY a valid JSON array. No thinking process, no intro text, no markdown fences.
Format:
[
  {{
    "q": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A",
    "explanation": "Short explanation."
  }}
]
"""
            with st.spinner(f"🧠 Preparing {num_q} {diff_level} MCQs for you..."):
                raw_json, q_err = generate_with_cascade(quiz_prompt, clean_mode="json")
                if raw_json:
                    try:
                        cleaned = re.sub(r'```(?:json)?|```', '', raw_json).strip()
                        start_idx = cleaned.find('[')
                        end_idx = cleaned.rfind(']') + 1
                        parsed = json.loads(cleaned[start_idx:end_idx])
                        st.session_state.quiz_data = parsed
                    except Exception:
                        st.session_state.qa_output = strip_leaked_thinking(raw_json, mode="qa")
                elif q_err == "BUSY":
                    st.warning("⏳ Free AI engines are busy. Wait 30 seconds and try again!")
                elif q_err:
                    st.error(f"❌ Test Error: {q_err}")
        else:
            qa_prompt = f"""
Create a {num_q}-question practice test (Subjective Questions with Model Answers) based on this topic:
Topic: {st.session_state.topic_context}
Difficulty: {diff_level}
Language: {st.session_state.lang_saved}

CRITICAL: You MUST start exactly with ===START_TEST===
No thinking process before it! Format cleanly with Q1., Q2... followed by '✅ Answer:'.

===START_TEST===
"""
            with st.spinner(f"📝 Preparing {num_q} {diff_level} Q&A for you..."):
                qa_res, qa_err = generate_with_cascade(qa_prompt, clean_mode="qa")
                if qa_res:
                    st.session_state.qa_output = qa_res
                elif qa_err == "BUSY":
                    st.warning("⏳ Free AI engines are busy. Wait 30 seconds and try again!")
                elif qa_err:
                    st.error(f"❌ Test Error: {qa_err}")

    # Render Interactive MCQs
    if st.session_state.quiz_data:
        st.markdown(f"#### 📝 Live Practice Test ({len(st.session_state.quiz_data)} Questions)")
        with st.form("auronix_quiz_form"):
            for idx, item in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{idx+1}. {item['q']}**")
                st.radio(
                    f"Select answer for Q{idx+1}:",
                    item["options"],
                    key=f"q_radio_{idx}",
                    index=None,
                    label_visibility="collapsed"
                )
            submitted = st.form_submit_button("📊 Submit Test & Check Score", use_container_width=True)
            if submitted:
                st.session_state.quiz_submitted = True

        if st.session_state.quiz_submitted:
            score = 0
            total = len(st.session_state.quiz_data)
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"q_radio_{idx}")
                if chosen == item["answer"]:
                    score += 1

            st.success(f"🏆 **Your Score: {score} / {total}** ({round((score/total)*100)}%)")
            for idx, item in enumerate(st.session_state.quiz_data):
                chosen = st.session_state.get(f"q_radio_{idx}")
                if chosen == item["answer"]:
                    st.markdown(f"✅ **Q{idx+1}: Correct!** ({item['answer']}) — *{item.get('explanation', '')}*")
                else:
                    st.markdown(f"❌ **Q{idx+1}: Your answer:** `{chosen or 'Not Attempted'}` | **Correct:** `{item['answer']}` — *{item.get('explanation', '')}*")

    # Render Subjective Q&A
    if st.session_state.qa_output:
        st.markdown("#### 📖 Practice Questions & Step-by-Step Answers")
        st.markdown(st.session_state.qa_output)
        
        qa_html = get_smart_html_download(st.session_state.qa_output, title="Auronix Practice Test")
        st.download_button(
            label="⬇️ Download Smart PDF/Doc (.html)",
            data=qa_html,
            file_name="Auronix_Practice_Test.html",
            mime="text/html",
            help="Opens beautifully on any device. Just click 'Print' inside to save as PDF!"
        )

# 🤖 CUTE FLOATING CORNER AI DOUBT ROBOT
with st.popover("🤖✨ Ask Doubt"):
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(255,165,0,0.18), rgba(30,41,59,0.9));
                padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(255,165,0,0.4); margin-bottom: 10px;">
        <div style="font-size: 16px; font-weight: 800; color: #FFB300;">🤖 Auronix Cute Buddy</div>
        <div style="font-size: 13.5px; color: #F1F5F9; margin-top: 3px;">
            "How can I help you in the notes? ✨"
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.study_notes or st.session_state.study_notes.startswith("🚫 STRICT FILTER"):
        st.info("👋 Pehle upar kisi bhi chapter ya YouTube link se **Notes generate** karo — phir main unhi notes se tera har doubt solve karunga! 🚀")
    else:
        # Display chat history inside popover
        for msg in st.session_state.buddy_chat[-4:]:
            if msg["role"] == "user":
                st.markdown(f"🧑‍🎓 **You:** {msg['text']}")
            else:
                st.success(f"🤖 **Buddy:** {msg['text']}")

        doubt_q = st.text_input(
            "Type your doubt from these notes:",
            placeholder="e.g., Formula #2 samjha do / Ismein se JEE trap kya hai?",
            key="buddy_doubt_input"
        )
        if st.button("💡 Solve My Doubt", use_container_width=True, key="buddy_ask_btn"):
            if not doubt_q.strip():
                st.warning("Pehle apna doubt likho!")
            elif not api_key:
                st.error("API Key missing.")
            else:
                buddy_prompt = f"""
You are Auronix Cute Buddy, a super-friendly, smart AI study assistant.
Language: {st.session_state.lang_saved}.
The student generated these Study Notes:
---
{st.session_state.study_notes[:9000]}
---
Student's Doubt: "{doubt_q.strip()}"

CRITICAL RULES:
1. Start your answer EXACTLY with ===START_BUDDY=== (nothing before it!).
2. Answer clearly, concisely, and step-by-step based directly on the generated notes above.
3. Keep the tone encouraging and easy to understand.

===START_BUDDY===
"""
                with st.spinner("🤖 Thinking..."):
                    ans, b_err = generate_with_cascade(buddy_prompt, clean_mode="buddy")
                    if ans:
                        st.session_state.buddy_chat.append({"role": "user", "text": doubt_q.strip()})
                        st.session_state.buddy_chat.append({"role": "bot", "text": ans})
                        st.rerun()
                    elif b_err == "BUSY":
                        st.warning("⏳ AI busy hai, 15 second baad try karo!")
                    elif b_err:
                        st.error(f"Error: {b_err}")

st.markdown("---")
st.caption("🦁 **Auronix learningAI** • Built for Smart Revision • Bookmark this page for instant access!")
