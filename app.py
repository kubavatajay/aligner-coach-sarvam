import streamlit as st
import requests
import base64
import io
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="Aligner Coach | Dr. Ajay Kubavat",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="expanded"
)

SARVAM_API_KEY = st.secrets.get("SARVAM_API_KEY", "")

# Full list of 22 official languages + Auto Detect
LANGUAGES = {
    "Auto Detect": "unknown",
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Gujarati": "gu-IN",
    "Bengali": "bn-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Punjabi": "pa-IN",
    "Odia": "od-IN",
    "Assamese": "as-IN",
    "Maithili": "mai-IN",
    "Konkani": "kok-IN",
    "Dogri": "doi-IN",
    "Kashmiri": "ks-IN",
    "Manipuri": "mni-IN",
    "Nepali": "ne-IN",
    "Sanskrit": "sa-IN",
    "Santali": "sat-IN",
    "Sindhi": "sd-IN",
    "Urdu": "ur-IN"
}

# Sarvam TTS (bulbul:v2) supports only these 11 language codes
TTS_SUPPORTED = [
    "hi-IN", "bn-IN", "kn-IN", "ml-IN", "mr-IN",
    "od-IN", "pa-IN", "ta-IN", "te-IN", "en-IN", "gu-IN"
]

SYSTEM_PROMPT = """You are the Aligner Coach AI, created by Dr. Ajay Kubavat (MDS Orthodontics), Founder of Sure Align Orthodontix n Dentistry, Ahmedabad, Gujarat. You are a friendly, empathetic expert aligner-treatment assistant for patients.

CRITICAL INSTRUCTION:
1. If the user selects a specific language from the menu, ALWAYS reply in that language.
2. If "Auto Detect" is selected, detect the language from the user's input and reply in the SAME language.
3. You support all 22 official Indian languages.

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
Severe pain not relieved by paracetamol. Allergic reaction (swelling, rash). Multiple attachments fallen off.
Contact: Dr. Ajay Kubavat | WhatsApp: +916358822642
Clinic: Sure Align Orthodontix n Dentistry, Ahmedabad

ALWAYS end every response with: 'For any concerns, WhatsApp Dr. Ajay Kubavat: +916358822642'
"""

def stt(audio_bytes):
    """Speech-to-Text using Sarvam Saarika v2."""
    if not SARVAM_API_KEY:
        st.error("Sarvam API key not configured.")
        return "", "unknown"
    try:
        files = {
            "file": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")
        }
        data = {
            "model": "saarika:v2.5",
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
            return "", "unknown"
        
        res = r.json()
        return res.get("transcript", ""), res.get("language_code", "unknown")
    except Exception as e:
        st.error(f"STT Error: {e}")
        return "", "unknown"

def tts(text, lang_code):
    """Text-to-Speech using Sarvam Bulbul v2."""
    if not SARVAM_API_KEY:
        return None
    try:
        tts_lang = lang_code if lang_code in TTS_SUPPORTED else "en-IN"
        text_trimmed = text[:1500]
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": text_trimmed,
                "target_language_code": tts_lang,
                "speaker": "anushka",
                "model": "bulbul:v2",
                "enable_preprocessing": True
            },
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

def chat(user_msg, history, selected_lang):
    """Chat using Sarvam-M with language awareness."""
    if not SARVAM_API_KEY:
        return "API key not configured."
    
    lang_instr = ""
    if selected_lang != "Auto Detect":
        lang_instr = f"\
\
IMPORTANT: The user has selected {selected_lang}. Please reply exclusively in {selected_lang}."
        
    msgs = [{"role": "system", "content": SYSTEM_PROMPT + lang_instr}]
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
    st.caption("▶️ Click to start | ⏹️ Click to stop | Auto-transcribes")
    
    audio = mic_recorder(
        start_prompt="🎤 Start Speaking",
        stop_prompt="⏹️ Stop Recording",
        just_once=False,
        use_container_width=True,
        key="mic"
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

# ---- Process new voice recording ----
if audio is not None:
    audio_id = audio.get("id")
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        wav_bytes = audio["bytes"]
        if len(wav_bytes) > 1000:
            with st.spinner("🎧 Transcribing your voice..."):
                transcript, detected_lang = stt(wav_bytes)
                if transcript and transcript.strip():
                    st.session_state.v_input = transcript.strip()
                    if lang == "Auto Detect":
                        st.session_state.detected_lang_code = detected_lang
                    st.toast(f"🎤 Heard: {transcript[:80]}")
                else:
                    st.warning("🔇 Could not transcribe. Please speak clearly and try again.")
        else:
            st.warning("🔇 Recording too short. Please hold and speak for at least 1 second.")

# ---- Display chat history ----
for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")

# ---- Text or voice input ----
placeholder = "Ask in any language..." if lang == "Auto Detect" else f"Ask in {lang}..."
inp = st.chat_input(placeholder)

if st.session_state.get("v_input"):
    inp = st.session_state.pop("v_input")

if inp:
    with st.chat_message("user"):
        st.write(inp)
    
    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(inp, st.session_state.history, lang)
    
    target_tts_code = lang_code
    if lang == "Auto Detect":
        target_tts_code = st.session_state.get("detected_lang_code", "en-IN")
        
    with st.spinner("🔊 Generating audio response..."):
        audio_out = tts(rep, target_tts_code)
        
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
