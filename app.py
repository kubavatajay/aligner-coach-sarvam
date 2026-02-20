import streamlit as st
import requests
import base64
import io

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

# TTS only supports these 11 language codes
TTS_SUPPORTED = [
    "hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN",
    "od-IN", "pa-IN", "ta-IN", "te-IN", "en-IN", "gu-IN"
]

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


def stt(audio_file):
    """Speech-to-Text using Sarvam Saarika v2.
    audio_file: file-like object (from st.audio_input) with .read() method.
    Returns transcript string.
    """
    if not SARVAM_API_KEY:
        st.error("Sarvam API key not set.")
        return ""
    try:
        audio_bytes = audio_file.read()
        files = {
            "file": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")
        }
        data = {
            "model": "saarika:v2",
            "language_code": "unknown"
        }
        r = requests.post(
            "https://api.sarvam.ai/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files=files,
            data=data,
            timeout=30
        )
        if r.status_code != 200:
            st.error(f"STT Error {r.status_code}: {r.text[:300]}")
            return ""
        result = r.json()
        return result.get("transcript", "")
    except Exception as e:
        st.error(f"STT Error: {e}")
        return ""


def tts(text, lang_code):
    """Text-to-Speech using Sarvam Bulbul v2.
    Returns WAV bytes or None.
    """
    if not SARVAM_API_KEY:
        return None
    try:
        # Fallback to English for languages not supported by TTS
        tts_lang = lang_code if lang_code in TTS_SUPPORTED else "en-IN"
        # bulbul:v2 max 1500 chars
        text_trimmed = text[:1500]
        payload = {
            "text": text_trimmed,
            "target_language_code": tts_lang,
            "speaker": "anushka",
            "model": "bulbul:v2",
            "enable_preprocessing": True
        }
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        if r.status_code != 200:
            st.warning(f"TTS Error {r.status_code}: {r.text[:300]}")
            return None
        audios = r.json().get("audios", [])
        if audios:
            return base64.b64decode(audios[0])
        return None
    except Exception as e:
        st.warning(f"TTS Error: {e}")
        return None


def chat(user_msg, history):
    """Chat completion using Sarvam-M."""
    if not SARVAM_API_KEY:
        return "API key not configured. Please set SARVAM_API_KEY in Streamlit secrets."
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        msgs.append({"role": "user", "content": h["user"]})
        msgs.append({"role": "assistant", "content": h["bot"]})
    msgs.append({"role": "user", "content": user_msg})
    try:
        r = requests.post(
            "https://api.sarvam.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sarvam-m",
                "messages": msgs,
                "temperature": 0.7,
                "max_tokens": 512
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Chat Error: {str(e)}"


# ======== SIDEBAR ========
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
    st.caption("Record your question below, then it will auto-transcribe")

    # Built-in Streamlit audio input (no extra package needed)
    audio_input = st.audio_input(
        label="Speak your question",
        key="voice_input"
    )

    st.divider()
    st.markdown("🚨 **Emergency**")
    st.markdown("[WhatsApp Dr. Ajay](https://wa.me/916358822642)")
    st.divider()

    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.session_state["last_audio_id"] = None
        st.rerun()


# ======== MAIN ========
st.title("🦷 Aligner Coach")
st.caption("Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry | Powered by Sarvam.ai")

if "history" not in st.session_state:
    st.session_state.history = []
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ---- Process voice input ----
if audio_input is not None:
    # Use file ID to avoid re-processing same recording on re-runs
    audio_id = id(audio_input)
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        with st.spinner("🎧 Transcribing your voice..."):
            transcript = stt(audio_input)
        if transcript and transcript.strip():
            st.session_state.v_input = transcript.strip()
            st.toast(f"🎤 Heard: {transcript[:80]}")
        else:
            st.warning("🔇 Could not transcribe. Please speak clearly and try again.")

# ---- Display chat history ----
for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")

# ---- Text or voice input ----
inp = st.chat_input(f"Ask in {lang}...")
if st.session_state.get("v_input"):
    inp = st.session_state.pop("v_input")

if inp:
    with st.chat_message("user"):
        st.write(inp)

    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(inp, st.session_state.history)

    with st.spinner("🔊 Generating audio response..."):
        audio_out = tts(rep, lang_code)

    with st.chat_message("assistant", avatar="🦷"):
        st.write(rep)
        if audio_out:
            st.audio(audio_out, format="audio/wav")

    st.session_state.history.append({
        "user": inp,
        "bot": rep,
        "audio": audio_out
    })
    st.rerun()
