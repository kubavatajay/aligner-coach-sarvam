import streamlit as st
import requests
import base64
import io
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Aligner Coach | Dr. Ajay Kubavat", page_icon="🦷", layout="centered", initial_sidebar_state="expanded")

st.markdown("""<style>.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); } [data-testid='stSidebar'] { background-color: #ffffff !important; border-right: 1px solid #dee2e6; } .stChatMessage { background-color: white !important; border-radius: 15px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; padding: 15px !important; margin-bottom: 15px !important; } .stButton>button { width: 100%; border-radius: 25px; background-color: #3498db; color: white; border: none; font-weight: bold; } .stButton>button:hover { background-color: #2980b9; }</style>""", unsafe_allow_html=True)

SARVAM_API_KEY = st.secrets.get("SARVAM_API_KEY", "")
LANGUAGES = {"Auto Detect": "unknown", "English": "en-IN", "Hindi": "hi-IN", "Gujarati": "gu-IN", "Bengali": "bn-IN", "Tamil": "ta-IN", "Telugu": "te-IN", "Kannada": "kn-IN", "Malayalam": "ml-IN", "Marathi": "mr-IN", "Punjabi": "pa-IN", "Odia": "od-IN", "Assamese": "as-IN", "Maithili": "mai-IN", "Konkani": "kok-IN", "Dogri": "doi-IN", "Kashmiri": "ks-IN", "Manipuri": "mni-IN", "Nepali": "ne-IN", "Sanskrit": "sa-IN", "Santali": "sat-IN", "Sindhi": "sd-IN", "Urdu": "ur-IN"}
TTS_SUPPORTED = ["hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN", "en-IN", "gu-IN"]
SYSTEM_PROMPT = "You are the Aligner Coach AI by Dr. Ajay Kubavat (MDS Orthodontics). Support all Indian languages. Wear 20-22h. Clean with lukewarm water. Store in case. Contact: +916358822642"

def stt(audio_bytes):
    if not SARVAM_API_KEY: return ""
    try:
        files = {"file": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")}
        data = {"model": "saarika:v2.5", "language_code": "unknown"}
        r = requests.post("https://api.sarvam.ai/speech-to-text", headers={"api-subscription-key": SARVAM_API_KEY}, files=files, data=data, timeout=30)
        return r.json().get("transcript", "")
    except: return ""

def tts(text, lang_code):
    if not SARVAM_API_KEY: return None
    try:
        tts_lang = lang_code if lang_code in TTS_SUPPORTED else "en-IN"
        r = requests.post("https://api.sarvam.ai/text-to-speech", headers={"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}, json={"text": text[:1500], "target_language_code": tts_lang, "speaker": "anushka", "model": "bulbul:v2", "enable_preprocessing": True}, timeout=30)
        audios = r.json().get("audios", [])
        return base64.b64decode(audios[0]) if audios else None
    except: return None

def chat(user_msg, history):
    if not SARVAM_API_KEY: return "API key not configured."
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        msgs.append({"role": "user", "content": h["user"]})
        msgs.append({"role": "assistant", "content": h["bot"]})
    msgs.append({"role": "user", "content": user_msg})
    try:
        r = requests.post("https://api.sarvam.ai/v1/chat/completions", headers={"Authorization": f"Bearer {SARVAM_API_KEY}", "Content-Type": "application/json"}, json={"model": "sarvam-m", "messages": msgs, "temperature": 0.7, "max_tokens": 512}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return f"Chat Error: {str(e)}"

with st.sidebar:
    st.image("https://img.icons8.com/color/96/tooth.png", width=100)
    st.markdown("## 🦷 Aligner Coach")
    st.markdown("### Dr. Ajay Kubavat")
    st.markdown("*(MDS Orthodontics)*")
    st.markdown("**Sure Align Orthodontix n Dentistry**")
    st.caption("📍 Ahmedabad, Gujarat")
    st.divider()
    lang = st.selectbox("🌐 Language / भाषा", list(LANGUAGES.keys()))
    lang_code = LANGUAGES[lang]
    st.divider()
    st.markdown("### 🎤 Voice Input")
    audio = mic_recorder(start_prompt="🎤 Start Speaking", stop_prompt="⏹️ Stop Recording", just_once=False, use_container_width=True, key="mic")
    st.divider()
    st.markdown("🚨 **Emergency**")
    st.markdown("[WhatsApp Dr. Ajay](https://wa.me/916358822642)")
    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.session_state["last_audio_id"] = None
        st.rerun()

st.title("🦷 Aligner Coach")
st.caption("Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry | Ahmedabad | Powered by Sarvam.ai")

if "history" not in st.session_state:
    st.session_state.history = []
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio is not None:
    audio_id = audio.get("id")
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        wav_bytes = audio["bytes"]
        if len(wav_bytes) > 1000:
            with st.spinner("🎧 Transcribing..."):
                transcript = stt(wav_bytes)
                if transcript:
                    st.session_state.v_input = transcript

for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")
        st.write(m["bot"])

inp = st.chat_input(f"Ask in {lang}...")
if st.session_state.get("v_input"):
    inp = st.session_state.pop("v_input")

if inp:
    with st.chat_message("user"):
        st.write(inp)
    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(inp, st.session_state.history)
        audio_out = tts(rep, lang_code)
        with st.chat_message("assistant", avatar="🦷"):
            st.write(rep)
            if audio_out:
                st.audio(audio_out, format="audio/wav")
        st.session_state.history.append({"user": inp, "bot": rep, "audio": audio_out})
        st.rerun()
