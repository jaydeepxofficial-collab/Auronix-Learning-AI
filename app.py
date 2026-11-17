import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re
import json

st.set_page_config(page_title="Auronix learningAI", page_icon="🦁", layout="centered")

# Google Search Console Verification Tag
st.markdown('<meta name="google-site-verification" content="AjHF7eNYXQYzd50KtS5DVJR3olMBc2UjYkBiw95e_Xs" />', unsafe_allow_html=True)

# Royal Auronix Header
st.markdown(
    "<h1 style='color: #FFA500; margin-bottom: 0;'>🦁 Auronix learningAI</h1>"
    "<p style='color: #A0A0A0; font-size: 15px; margin-top: 4px;'>"
    "AI-Powered Exam Notes, Formula Sheets & Smart Practice Tests in Seconds!</p>",
    unsafe_allow_html=True
)

api_key = st.secrets.get("GEMINI_API_KEY", "")

# Session State Initialization (taaki Test select karte waqt Notes gayab na hon)
for key, default in [
    ("study_notes", ""),
    ("topic_context", ""),
    ("lang_saved", "English (Exam Ready)"),
    ("quiz_data", None),
    ("qa_output", ""),
    ("quiz_submitted", False)
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

def generate_with_cascade(prompt_text, stream_mode=True):
    genai.configure(api_key=api_key)
    models_to_try = get_cascade_models()
    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            if stream_mode:
                response = model.generate_content(prompt_text, stream=True)
                full_output = []
                def stream_chunks():
                    for chunk in response:
                        if chunk.text:
                            full_output.append(chunk.text)
                            yield chunk.text
                st.write_stream(stream_chunks())
                final_text = "".join(full_output)
                if final_text:
                    return final_text, None
            else:
                response = model.generate_content(prompt_text)
                if response.text:
                    return response.text, None
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
            "📚 Crisp Exam Notes & Formulas",
            "⚡ 60-Sec Rapid Formula Sheet",
            "📖 Detailed Step-by-Step Explanation"
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
        placeholder="Example: Class 11 Work, Energy and Power all formulas & theorems...",
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

    if output_type == "📚 Crisp Exam Notes & Formulas":
        task_instruction = """Generate high-scoring topper-style exam notes with these 4 clean sections:
1. 🎯 Core Concept Summary
2. 📌 Key Definitions & Laws
3. 📐 Important Formulas & Units
4. ⚡ Exam Topper Takeaway"""
    elif output_type == "⚡ 60-Sec Rapid Formula Sheet":
        task_instruction = """Generate a super-crisp, last-minute revision Formula & Rule Sheet:
- List every important formula clearly with symbol meanings and SI units.
- Add 3 common exam traps/mistakes to avoid."""
    else:
        task_instruction = """Explain this topic from zero level to exam mastery in clear, structured points with real-life examples, laws, formulas, and solved numericals."""

    prompt = f"""
You are Auronix learningAI, an elite academic & skill-learning assistant.
Language Style: {lang_choice}

First, verify if the following input is educational, academic, scientific, or skill-based:
Input: {source_text[:12000]}

STRICT FILTER RULE:
If this input is pure entertainment (songs, movies, gaming, pranks, comedy, vlogs, gossip), output ONLY:
"🚫 STRICT FILTER: Auronix learningAI only supports educational, academic, and skill-learning content!"

If it IS educational/academic, follow this instruction strictly:
{task_instruction}
Keep formatting super clean, structured, and easy to revise on mobile.
"""
    st.markdown("---")
    notes_res, err = generate_with_cascade(prompt, stream_mode=True)
    if notes_res:
        st.session_state.study_notes = notes_res
        st.session_state.topic_context = source_text[:10000]
        st.session_state.lang_saved = lang_choice
    elif err == "BUSY":
        st.warning("⏳ All free AI engines are busy right now. Please wait 30 seconds and click Generate again!")
    elif err:
        st.error(f"❌ AI Error: {err}")

elif st.session_state.study_notes:
    st.markdown("---")
    st.markdown(st.session_state.study_notes)

# Download & Test Your Knowledge Section (Sirf valid educational notes ke baad dikhega!)
if st.session_state.study_notes and not st.session_state.study_notes.startswith("🚫 STRICT FILTER"):
    st.download_button(
        label="⬇️ Download Notes (.txt)",
        data=st.session_state.study_notes,
        file_name="Auronix_Study_Notes.txt",
        mime="text/plain"
    )

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

Return ONLY a valid JSON array (no markdown backticks, no extra text before or after) with exactly {num_q} objects in this format:
[
  {{
    "q": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A",
    "explanation": "Short clear explanation why this is correct."
  }}
]
Make sure "answer" matches one of the 4 strings in "options" EXACTLY.
"""
            with st.spinner(f"🧠 Preparing {num_q} {diff_level} MCQs for you..."):
                raw_json, q_err = generate_with_cascade(quiz_prompt, stream_mode=False)
                if raw_json:
                    try:
                        cleaned = re.sub(r'```(?:json)?|```', '', raw_json).strip()
                        start_idx = cleaned.find('[')
                        end_idx = cleaned.rfind(']') + 1
                        parsed = json.loads(cleaned[start_idx:end_idx])
                        st.session_state.quiz_data = parsed
                    except Exception:
                        st.session_state.qa_output = raw_json
                elif q_err == "BUSY":
                    st.warning("⏳ Free AI engines are busy. Wait 30 seconds and try again!")
                elif q_err:
                    st.error(f"❌ Test Error: {q_err}")
        else:
            qa_prompt = f"""
Create a {num_q}-question practice test (Important Subjective Questions with Step-by-Step Model Answers) strictly based on this topic/content:
Topic/Content: {st.session_state.topic_context}

Difficulty Level: {diff_level}
Language: {st.session_state.lang_saved}

Format cleanly with Q1, Q2... followed by clear, exam-scoring '✅ Answer:' for each question.
"""
            with st.spinner(f"📝 Preparing {num_q} {diff_level} Q&A for you..."):
                qa_res, qa_err = generate_with_cascade(qa_prompt, stream_mode=False)
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
            user_answers = {}
            for idx, item in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{idx+1}. {item['q']}**")
                user_answers[idx] = st.radio(
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
        st.download_button(
            label="⬇️ Download Practice Test (.txt)",
            data=st.session_state.qa_output,
            file_name="Auronix_Practice_Test.txt",
            mime="text/plain"
        )

st.markdown("---")
st.caption("🦁 **Auronix learningAI** • Built for Smart Revision • Bookmark this page for instant access!")
