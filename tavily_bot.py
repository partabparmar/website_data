import requests
import streamlit as st
import audio_recorder_streamlit as ars
import os

from io import BytesIO
from dotenv import load_dotenv
from web_scrape import main_scrape  # External scraping function

# Load environment variables
load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


SCRAPE_FILE = "final_analysis.txt"

# Initialize session state variables
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "website_name" not in st.session_state:
    st.session_state["website_name"] = ""
if "scraped_data" not in st.session_state:
    st.session_state["scraped_data"] = ""
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []
if "scraped" not in st.session_state:
    st.session_state["scraped"] = False

# Function to load scraped data from file
def load_scraped_data():
    if os.path.exists(SCRAPE_FILE):
        with open(SCRAPE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Function to process user query with OpenAI
def query_openai(scraped_text, user_input):
    if not scraped_text.strip():
        return "No website data found. Please enter a website URL first."
    
    prompt = f"""
    Based on the scraped website data, answer the user's query.
    Website Data:
    {scraped_text}
    User Query:
    {user_input}
    Provide a professional and concise response.
    """

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]}
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"OpenAI API Error: {e}"

# Function to convert text to speech with ElevenLabs
def text_to_speech(text):
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_monolingual_v1", "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        st.error(f"ElevenLabs API Error: {e}")
        return None

# Streamlit UI
st.title("🎙️ AI Voice Assistant")
print("ElevenLabs API Key:", os.getenv("ELEVENLABS_API_KEY"))
st.markdown("### Enter Website Q/A Voice ChatBot")

# Step 1: Scrape Website (Only Once)
url = st.text_input("Enter Website URL", "")

if url and not st.session_state["scraped"]:
    with st.spinner("Scraping website data..."):
        main_scrape(url)
        scraped_text = load_scraped_data()
        st.session_state["scraped_data"] = scraped_text
        st.session_state["scraped"] = True
        website_name = url.split("//")[-1].split("/")[0]
        st.session_state["website_name"] = website_name
        welcome_message = f"Hello! I am from {st.session_state['website_name']}. How can I help you?"
        tts_audio = text_to_speech(welcome_message)
        if tts_audio:
            st.audio(tts_audio, format="audio/mp3")

# Step 2: Continuous Voice Q&A Loop
audio_bytes = ars.audio_recorder(
    pause_threshold=5.0,
    sample_rate=16_000,
    text="",
    recording_color="#e74c3c",
    neutral_color="#2ecc71",
    icon_size="3x"
)

if audio_bytes:
    st.session_state["audio_bytes"] = audio_bytes
    st.audio(audio_bytes, format="audio/wav")
    
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    url = "https://api.deepgram.com/v1/listen?model=nova-2"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    
    try:
        with open("temp_audio.wav", "rb") as audio_file:
            response = requests.post(url, headers=headers, data=audio_file)
            response.raise_for_status()
        transcript = response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except requests.exceptions.RequestException as e:
        transcript = f"Deepgram API Error: {e}"
    
    st.session_state["transcript"] = transcript
    os.remove("temp_audio.wav")
    scraped_text = st.session_state.get("scraped_data", "")
    answer = query_openai(scraped_text, transcript)
    st.session_state["conversation"].append({"user": transcript, "ai": answer})
    tts_audio = text_to_speech(answer)
    if tts_audio:
        st.audio(tts_audio, format="audio/mp3")

# Reset functionality
if st.button("Start New Session"):
    st.session_state.clear()
    st.rerun()
