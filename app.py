import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import io
import json

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

# Sarvam TTS (bulbul:v2) supports only these 11 language codes
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
ALWAYS end every response with: 'For any concerns, WhatsApp Dr. Ajay Kubavat: +916358822642'
"""

# ===== JavaScript Audio Recorder Component =====
AUDIO_RECORDER_HTML = """
<div style="font-family: sans-serif; text-align: center; padding: 8px;">
  <button id="recBtn" onclick="toggleRecording()"
    style="background:#FF4B4B; color:white; border:none; border-radius:8px;
           padding:10px 20px; font-size:16px; cursor:pointer; width:100%;">
    🎤 Start Speaking
  </button>
  <p id="status" style="color:#666; font-size:13px; margin:6px 0;">Click button to start recording</p>
</div>

<script>
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

function toggleRecording() {
  if (!isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        window.parent.postMessage({ type: 'audio_data', data: base64 }, '*');
        document.getElementById('status').textContent = 'Recording sent for transcription!';
      };
      reader.readAsDataURL(blob);
      stream.getTracks().forEach(t => t.stop());
    };
    mediaRecorder.start();
    isRecording = true;
    document.getElementById('recBtn').textContent = '⏹️ Stop Recording';
    document.getElementById('recBtn').style.background = '#00AA00';
    document.getElementById('status').textContent = 'Recording... Click to stop';
  } catch(err) {
    document.getElementById('status').textContent = 'Mic error: ' + err.message;
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    document.getElementById('recBtn').textContent = '🎤 Start Speaking';
    document.getElementById('recBtn').style.background = '#FF4B4B';
    document.getElementById('status').textContent = 'Processing...';
  }
}
</script>
"""


def stt(audio_bytes):
    """Speech-to-Text using Sarvam Saarika v2."""
    if not SARVAM_API_KEY:
        st.error("Sarvam API key not configured.")
        return ""
    try:
        files = {"file": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")}
        data = {"model": "saarika:v2", "language_code": "unknown"}
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
        return r.json().get("transcript", "")
    except Exception as e:
        st.error(f"STT Exception: {e}")
        return ""


def tts(text, lang_code):
    """Text-to-Speech using Sarvam Bulbul v2. Returns WAV bytes or None."""
    if not SARVAM_API_KEY:
        return None
    try:
        tts_lang = lang_code if lang_code in TTS_SUPPORTED else "en-IN"
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": text[:1500],
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
        return base64.b64decode(audios[0]) if audios else None
    except Exception as e:
        st.warning(f"TTS Exception: {e}")
        return None


def chat(user_msg, history):
    """Chat using Sarvam-M."""
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
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"model": "sarvam-m", "messages": msgs, "temperature": 0.7, "max_tokens": 512},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Chat Error: {str(e)}"


# ======== SESSION STATE INIT ========
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None


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
    st.caption("▶️ Click to start | ⏹️ Click again to stop")

    # Render the JS audio recorder
    audio_b64 = components.html(AUDIO_RECORDER_HTML, height=100)

    st.divider()
    st.markdown("🚨 **Emergency**")
    st.markdown("[WhatsApp Dr. Ajay](https://wa.me/916358822642)")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.session_state.pending_input = None
        st.rerun()


# ======== MAIN ========
st.title("🦷 Aligner Coach")
st.caption("Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry | Powered by Sarvam.ai")

# ---- Display chat history ----
for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])
        if m.get("audio"):
            st.audio(m["audio"], format="audio/wav")

# ---- Text input ----
final_inp = st.chat_input(f"Ask in {lang}...")

if final_inp:
    with st.chat_message("user"):
        st.write(final_inp)
    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(final_inp, st.session_state.history)
    audio_out = None
    with st.spinner("🔊 Generating audio response..."):
        audio_out = tts(rep, lang_code)
    with st.chat_message("assistant", avatar="🦷"):
        st.write(rep)
        if audio_out:
            st.audio(audio_out, format="audio/wav")
    st.session_state.history.append({
        "user": final_inp,
        "bot": rep,
        "audio": audio_out
    })
    st.rerun()
