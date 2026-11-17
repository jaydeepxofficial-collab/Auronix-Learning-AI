import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

st.set_page_config(page_title="Auronix learningAI", page_icon="🦁", layout="centered")

st.title("🦁 Auronix learningAI")
st.caption("Convert Educational YouTube Lectures into Crisp Exam Notes & Formulas in Seconds!")

# API Key Secret Locker se aayegi
api_key = st.secrets.get("GEMINI_API_KEY", "")

def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

youtube_url = st.text_input("🔗 Paste Educational YouTube Lecture Link Here:")

if st.button("✨ Generate Study Notes"):
    if not youtube_url:
        st.warning("Please paste a valid YouTube link first!")
    elif not api_key:
        st.error("API Key missing in server settings.")
    else:
        video_id = get_video_id(youtube_url)
        if not video_id:
            st.error("Invalid YouTube link! Please check and try again.")
        else:
            with st.spinner("🧠 Reading lecture & extracting key exam concepts..."):
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
                    full_text = " ".join([item['text'] for item in transcript_list])
                    
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    prompt = f"""
                    You are an elite academic assistant. First check if the following YouTube video transcript is educational, academic, informative, or skill-based.
                    If it is pure entertainment, music, prank, gaming, or non-educational, reply ONLY with: '🚫 STRICT FILTER: This tool only summarizes educational and study-related videos.'
                    Otherwise, create structured, crystal-clear Exam Revision Notes with:
                    1. Core Summary (3-4 bullet points)
                    2. Key Definitions & Concepts
                    3. Important Formulas / Rules (if any)
                    4. Quick Revision Takeaway
                    
                    Transcript: {full_text[:25000]}
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown("---")
                    st.markdown(response.text)
                except Exception as e:
                    st.error("Could not fetch captions for this video. Make sure the video has English or Hindi subtitles enabled!")

st.markdown("---")
st.info("💡 **Pro Tip:** Bookmark this page for instant exam revision notes!")
