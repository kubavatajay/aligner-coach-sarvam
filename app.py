import streamlit as st
import requests
import base64
from audio_recorder_streamlit import audio_recorder

st.set_page_config(
    page_title="Aligner Coach | Dr. Ajay Kubavat",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="expanded"
)

SARVAM_API_KEY = st.secrets.get("SARVAM_API_KEY", "")

LANGUAGES = {
    "English": "en-IN", "Hindi": "hi-IN", "Gujarati": "gu-IN",
    "Bengali": "bn-IN", "Tamil": "ta-IN", "Telugu": "te-IN",
    "Kannada": "kn-IN", "Malayalam": "ml-IN", "Marathi": "mr-IN",
    "Punjabi": "pa-IN", "Odia": "od-IN", "Assamese": "as-IN",
    "Maithili": "mai-IN", "Konkani": "kok-IN", "Dogri": "doi-IN",
    "Kashmiri": "ks-IN", "Manipuri": "mni-IN", "Nepali": "ne-IN",
    "Sanskrit": "sa-IN", "Santali": "sat-IN", "Sindhi": "sd-IN", "Urdu": "ur-IN"
}

SYSTEM_PROMPT = """You are the Aligner Coach AI, created by Dr. Ajay Kubavat (MDS Orthodontics),
Founder of Sure Align Orthodontix n Dentistry, Ahmedabad, Gujarat.
You are a friendly, empathetic expert aligner-treatment assistant for patients.
DETECT the patient language automatically and REPLY in the SAME language.
You support all 22 official Indian languages.

=== CLINICAL PROTOCOLS ===
WEAR TIME: 20-22 hours/day. Remove ONLY for eating/drinking (except water).
CLEANING: Rinse with lukewarm water; brush gently with soft toothbrush. NO hot water.
STORAGE: Always in the provided case. Never wrap in tissue.
EACH SET: 7-14 days as prescribed by Dr. Ajay Kubavat.

=== COMMON ISSUES ===
PAIN: Mild soreness 2-3 days after new tray is NORMAL. Paracetamol 500mg if needed.
SHARP EDGE: Use ortho wax. Call clinic if it persists beyond 3 days.
STAINING: Avoid turmeric, tea, coffee while wearing aligners.
LOST ALIGNER: Move to next or previous tray temporarily. Call clinic immediately.
MULTIPLE ATTACHMENTS FALLEN: Stop wearing and call clinic immediately.

=== EMERGENCY - CALL IMMEDIATELY ===
Severe pain not relieved by paracetamol.
Allergic reaction (swelling, rash).
Multiple attachments fallen off.
Contact: Dr. Ajay Kubavat | WhatsApp: +916358822642
Clinic: Sure Align Orthodontix n Dentistry, Ahmedabad

ALWAYS end every response with:
'For any concerns, WhatsApp Dr. Ajay Kubavat: +916358822642'
"""

# ---- Sarvam AI Functions ----
def stt(audio_bytes):
    """Voice to Text using Sarvam Saarika v2"""
    try:
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        r = requests.post(
            "https://api.sarvam.ai/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files=files,
            data={"model": "saarika:v2", "language_code": "unknown"},
            timeout=30
        )
        r.raise_for_status()
        return r.json().get("transcript", "")
    except Exception as e:
        st.error(f"Voice transcription error: {e}")
        return ""

def tts(text, lang_code):
    """Text to Speech using Sarvam Bulbul v2"""
    try:
        # Trim text to 1500 chars max (bulbul:v2 limit)
        text = text[:1500]
        # Only supported language codes for bulbul:v2 TTS
        supported_tts = ["hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN",
                         "od-IN", "pa-IN", "ta-IN", "te-IN", "en-IN", "gu-IN"]
        if lang_code not in supported_tts:
            lang_code = "en-IN"
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "target_language_code": lang_code,
                "speaker": "anushka",
                "model": "bulbul:v2",
                "enable_preprocessing": True
            },
            timeout=30
        )
        r.raise_for_status()
        audios = r.json().get("audios", [])
        if audios:
            return base64.b64decode(audios[0])
        return None
    except Exception as e:
        st.warning(f"Audio generation note: {e}")
        return None

def chat(user_msg, history):
    if not SARVAM_API_KEY:
        return "API key not configured."
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        msgs.append({"role": "user", "content": h["user"]})
        msgs.append({"role": "assistant", "content": h["bot"]})
    msgs.append({"role": "user", "content": user_msg})
    try:
        r = requests.post(
            "https://api.sarvam.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {SARVAM_API_KEY}", "Content-Type": "application/json"},
            json={"model": "sarvam-m", "messages": msgs, "temperature": 0.7, "max_tokens": 512},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# ---- Sidebar ----
with st.sidebar:
    st.image("https://img.icons8.com/color/96/tooth.png", width=80)
    st.markdown("## 🦷 Aligner Coach")
    st.markdown("**Dr. Ajay Kubavat**")
    st.markdown("🎓 MDS Orthodontics | Ahmedabad")
    st.divider()
    lang = st.selectbox("🌐 Language / भाषा", list(LANGUAGES.keys()))
    lang_code = LANGUAGES[lang]
    st.divider()
    st.markdown("### 🎤 Voice Input")
    st.caption("Click mic, speak your question, click again to stop")
    recorded_audio = audio_recorder(
        text="Click to Speak",
        recording_color="#e8534f",
        neutral_color="#00a2ff",
        icon_size="2x"
    )
    st.divider()
    st.markdown("🚨 **Emergency**")
    st.markdown("[WhatsApp Dr. Ajay](https://wa.me/916358822642)")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.rerun()

# ---- Main ----
st.title("🦷 Aligner Coach")
st.caption("Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry | Powered by Sarvam.ai")

if "history" not in st.session_state:
    st.session_state.history = []

# Process voice input from microphone
if recorded_audio and len(recorded_audio) > 1000:
    with st.spinner("🎧 Transcribing your voice..."):
        v_text = stt(recorded_audio)
    if v_text and v_text.strip():
        st.session_state.v_input = v_text.strip()
        st.toast(f"🎤 Heard: {v_text[:60]}")

# Display chat history
for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")

# Get input - either typed or from voice
inp = st.chat_input(f"Ask in {lang}...")
if st.session_state.get("v_input"):
    inp = st.session_state.pop("v_input")

if inp:
    with st.chat_message("user"):
        st.write(inp)

    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(inp, st.session_state.history)

    with st.spinner("🔊 Generating audio response..."):
        audio_bytes = tts(rep, lang_code)

    with st.chat_message("assistant", avatar="🦷"):
        st.write(rep)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

    st.session_state.history.append({"user": inp, "bot": rep, "audio": audio_bytes})
    st.rerun()
