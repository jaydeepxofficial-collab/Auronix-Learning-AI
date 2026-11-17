import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

st.set_page_config(page_title="Auronix learningAI", page_icon="🦁", layout="centered")

# Royal Auronix Header
st.markdown(
    "<h1 style='color: #FFA500; margin-bottom: 0;'>🦁 Auronix learningAI</h1>"
    "<p style='color: #A0A0A0; font-size: 15px; margin-top: 4px;'>"
    "AI-Powered Exam Notes, Formula Sheets & Practice MCQs in Seconds!</p>",
    unsafe_allow_html=True
)

api_key = st.secrets.get("GEMINI_API_KEY", "")

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

# Input Method Selection
mode = st.radio(
    "1️⃣ Choose Input Method:",
    ["🔗 YouTube Lecture Link", "📝 Topic Name / Lecture Text"],
    horizontal=True
)

# Study Output Customization
col1, col2 = st.columns(2)
with col1:
    output_type = st.selectbox(
        "2️⃣ What do you want?",
        [
            "📚 Crisp Exam Notes & Formulas",
            "⚡ 60-Sec Rapid Formula Sheet",
            "🧠 5 Practice MCQs + Solutions"
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
    if st.button("✨ Generate Now", use_container_width=True):
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
    if st.button("✨ Generate Now", use_container_width=True):
        if not manual_input.strip():
            st.warning("⚠️ Please enter a topic or paste some text first!")
            st.stop()
        if not api_key:
            st.error("❌ API Key missing in server settings.")
            st.stop()
        source_text = manual_input.strip()
        trigger = True

if trigger and source_text:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-3.8-flash")

        if output_type == "📚 Crisp Exam Notes & Formulas":
            task_instruction = """Generate high-scoring exam notes with these 4 clean sections:
1. 🎯 Core Concept Summary
2. 📌 Key Definitions & Laws
3. 📐 Important Formulas & Units
4. ⚡ Exam Topper Takeaway"""
        elif output_type == "⚡ 60-Sec Rapid Formula Sheet":
            task_instruction = """Generate a super-crisp, last-minute revision Formula & Rule Sheet:
- List every important formula clearly with symbol meanings and SI units.
- Add 3 common exam traps/mistakes to avoid."""
        else:
            task_instruction = """Generate 5 conceptual & numerical exam-level MCQs (with 4 options A, B, C, D) based on this topic/lecture.
At the very bottom, provide a clean '✅ Answer Key & Step-by-Step Solutions' section."""

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
        response = model.generate_content(prompt, stream=True)

        full_output = []
        def stream_chunks():
            for chunk in response:
                if chunk.text:
                    full_output.append(chunk.text)
                    yield chunk.text

        st.write_stream(stream_chunks())
        final_text = "".join(full_output)

        if final_text and not final_text.startswith("🚫 STRICT FILTER"):
            st.download_button(
                label="⬇️ Download Notes (.txt)",
                data=final_text,
                file_name="Auronix_Study_Notes.txt",
                mime="text/plain"
            )
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")

st.markdown("---")
st.caption("🦁 **Auronix learningAI** • Built for Smart Revision • Bookmark this page for instant access!")
