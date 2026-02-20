import streamlit as st
import requests
import base64
import io
import wave
from streamlit_audiorecorder import audiorecorder

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

# TTS only supports these 11 languages
TTS_SUPPORTED = ["hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN",
                 "od-IN", "pa-IN", "ta-IN", "te-IN", "en-IN", "gu-IN"]

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


def audio_segment_to_wav_bytes(audio_segment):
    """Convert pydub AudioSegment to WAV bytes for Sarvam STT API."""
    buf = io.BytesIO()
    audio_segment.export(buf, format="wav")
    buf.seek(0)
    return buf.read()


def stt(audio_bytes):
    """Speech to Text using Sarvam Saarika v2.
    audio_bytes must be a valid WAV file bytes.
    """
    if not SARVAM_API_KEY:
        return ""
    try:
        # audio_bytes from streamlit_audiorecorder is already a valid WAV
        buf = io.BytesIO(audio_bytes)
        files = {
            "file": ("recording.wav", buf, "audio/wav")
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
            st.error(f"STT Error {r.status_code}: {r.text[:200]}")
            return ""
        return r.json().get("transcript", "")
    except Exception as e:
        st.error(f"STT exception: {e}")
        return ""


def tts(text, lang_code):
    """Text to Speech using Sarvam Bulbul v2."""
    if not SARVAM_API_KEY:
        return None
    try:
        # Use English fallback for unsupported TTS languages
        tts_lang = lang_code if lang_code in TTS_SUPPORTED else "en-IN"
        # Trim to bulbul:v2 limit
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
            st.warning(f"TTS Error {r.status_code}: {r.text[:200]}")
            return None
        audios = r.json().get("audios", [])
        if audios:
            return base64.b64decode(audios[0])
        return None
    except Exception as e:
        st.warning(f"TTS exception: {e}")
        return None


def chat(user_msg, history):
    """Chat with Sarvam-M model."""
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
        return f"Chat error: {str(e)}"


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
    st.caption("Press Start, speak your question, then press Stop")

    audio = audiorecorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹️ Stop Recording",
        pause_prompt="",
        key="audiorecorder"
    )

    st.divider()
    st.markdown("🚨 **Emergency**")
    st.markdown("[WhatsApp Dr. Ajay](https://wa.me/916358822642)")
    st.divider()

    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.session_state["last_audio_hash"] = None
        st.rerun()


# ---- Main ----
st.title("🦷 Aligner Coach")
st.caption("Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry | Powered by Sarvam.ai")

if "history" not in st.session_state:
    st.session_state.history = []
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# ---- Process Voice Input ----
if len(audio) > 0:
    # Export to WAV bytes
    wav_bytes = audio_segment_to_wav_bytes(audio)
    audio_hash = hash(wav_bytes)

    # Only process new recordings (avoid re-processing on rerun)
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("🎧 Transcribing your voice..."):
            transcript = stt(wav_bytes)
        if transcript and transcript.strip():
            st.session_state.v_input = transcript.strip()
            st.toast(f"🎤 Heard: {transcript[:80]}")
        else:
            st.warning("🔇 Could not transcribe audio. Please try again clearly.")

# ---- Display Chat History ----
for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")

# ---- Get Input (typed or voice) ----
inp = st.chat_input(f"Ask in {lang}...")
if st.session_state.get("v_input"):
    inp = st.session_state.pop("v_input")

if inp:
    with st.chat_message("user"):
        st.write(inp)

    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(inp, st.session_state.history)

    with st.spinner("🔊 Generating audio response..."):
        audio_bytes_out = tts(rep, lang_code)

    with st.chat_message("assistant", avatar="🦷"):
        st.write(rep)
        if audio_bytes_out:
            st.audio(audio_bytes_out, format="audio/wav")

    st.session_state.history.append({
        "user": inp,
        "bot": rep,
        "audio": audio_bytes_out
    })
    st.rerun()
