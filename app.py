import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

st.set_page_config(page_title="Auronix learningAI", page_icon="🦁", layout="centered")
st.title("🦁 Auronix learningAI")
st.caption("Convert Educational YouTube Lectures or Study Topics into Crisp Exam Notes & Formulas in Seconds!")

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

def get_working_model():
    try:
        available = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name.lower()
        ]
        for preferred in ['models/gemini-2.5-flash', 'models/gemini-2.0-flash', 'models/gemini-flash-latest']:
            if preferred in available:
                return genai.GenerativeModel(preferred)
        if available:
            return genai.GenerativeModel(available[0])
    except Exception:
        pass
    return genai.GenerativeModel("gemini-2.5-flash")

mode = st.radio(
    "Choose Input Method:",
    ["🔗 YouTube Lecture Link", "📝 Paste Topic / Rough Lecture Text (Backup)"],
    horizontal=True
)

source_text = ""

if mode == "🔗 YouTube Lecture Link":
    youtube_url = st.text_input("Paste Educational YouTube Lecture Link Here:")
    if st.button("✨ Generate Study Notes"):
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
        with st.spinner("🔍 Fetching lecture transcript & generating notes..."):
            source_text = fetch_any_transcript(video_id)
            if not source_text:
                st.warning("⚠️ YouTube blocked captions for this video (or subtitles are disabled). Switch to **'📝 Paste Topic / Rough Lecture Text'** above to generate instant notes anyway!")
                st.stop()
else:
    manual_input = st.text_area(
        "Enter Chapter/Topic Name OR Paste Lecture Transcript/Text:",
        placeholder="Example: Class 11 Work, Energy and Power all formulas...",
        height=150
    )
    if st.button("✨ Generate Study Notes"):
        if not manual_input.strip():
            st.warning("⚠️ Please enter a topic or paste some text first!")
            st.stop()
        if not api_key:
            st.error("❌ API Key missing in server settings.")
            st.stop()
        source_text = manual_input.strip()

if source_text:
    with st.spinner("🧠 Auronix AI is crafting your exam notes..."):
        try:
            genai.configure(api_key=api_key)
            model = get_working_model()
            prompt = f"""
You are Auronix learningAI, a strict academic & skill-building study assistant.
First, check if the following content is educational, academic, scientific, or skill-based:
Content: {source_text[:15000]}

STRICT FILTER RULE:
If this content is pure entertainment (songs, movies, gaming, pranks, comedy, vlogs, gossip), reply ONLY with:
"🚫 STRICT FILTER: Auronix learningAI only generates notes for educational, academic, and skill-learning content!"

If it IS educational/academic, generate crisp, high-scoring exam notes in clear English with these 4 sections:
1. 🎯 Core Concept Summary
2. 📌 Key Definitions & Principles
3. 📐 Important Formulas / Rules (if applicable)
4. ⚡ Quick Revision Takeaway
"""
            response = model.generate_content(prompt)
            st.markdown("---")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"❌ AI Error: {str(e)}")

st.info("💡 **Pro Tip:** Bookmark this page for instant exam revision notes!")
