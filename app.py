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
    """Voice to Text using Sarvam Saaras v2"""
    try:
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        r = requests.post(
            "https://api.sarvam.ai/v1/speech-to-text-translate",
            headers={"Authorization": f"Bearer {SARVAM_API_KEY}"},
            files=files,
            data={"model": "saaras_v2"},
            timeout=30
        )
        r.raise_for_status()
        return r.json().get("transcript", "")
    except Exception as e:
        st.error(f"STT Error: {e}")
        return ""

def tts(text, lang_code):
    """Text to Speech using Sarvam Bulbul v1"""
    try:
        r = requests.post(
            "https://api.sarvam.ai/v1/text-to-speech",
            headers={"Authorization": f"Bearer {SARVAM_API_KEY}", "Content-Type": "application/json"},
            json={
                "inputs": [text],
                "target_language_code": lang_code,
                "speaker": "meera",
                "model": "bulbul:v1"
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json().get("audios", [None])[0]
    except Exception as e:
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
    recorded_audio = audio_recorder(text="Click to Speak", neutral_color="#00a2ff")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.rerun()

# ---- Main ----
st.title("🦷 Aligner Coach")
st.caption(f"Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry")

if "history" not in st.session_state:
    st.session_state.history = []

# Process Voice Input
if recorded_audio:
    with st.spinner("🎧 Processing voice..."):
        v_text = stt(recorded_audio)
        if v_text:
            st.session_state.v_input = v_text

# Display History
for i, m in enumerate(st.session_state.history):
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")

# Chat Logic
inp = st.chat_input(f"Ask in {lang}...")
if st.session_state.get("v_input"):
    inp = st.session_state.v_input
    del st.session_state.v_input

if inp:
    with st.chat_message("user"):
        st.write(inp)
    
    with st.spinner("🦷 Thinking..."):
        rep = chat(inp, st.session_state.history)
    
    with st.spinner("🔊 Generating audio..."):
        audio_base64 = tts(rep, lang_code)
    
    with st.chat_message("assistant", avatar="🦷"):
        st.write(rep)
        if audio_base64:
            st.audio(audio_base64, format="audio/wav")
            
    st.session_state.history.append({"user": inp, "bot": rep, "audio": audio_base64})
    st.rerun()
