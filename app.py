import streamlit as st
import requests

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

def chat(user_msg, history):
    if not SARVAM_API_KEY:
        return "API key not configured. Add SARVAM_API_KEY to Streamlit secrets."
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-6:]:
        msgs.append({"role": "user", "content": h["user"]})
        msgs.append({"role": "assistant", "content": h["bot"]})
    msgs.append({"role": "user", "content": user_msg})
    try:
        r = requests.post(
            "https://api.sarvam.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {SARVAM_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": "sarvam-m", "messages": msgs,
                  "temperature": 0.7, "max_tokens": 512},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError:
        return f"API Error {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return f"Error: {str(e)}"

# ---- Sidebar ----
with st.sidebar:
    st.image("https://img.icons8.com/color/96/tooth.png", width=80)
    st.markdown("## 🦷 Aligner Coach")
    st.markdown("**Dr. Ajay Kubavat**")
    st.markdown("🎓 MDS Orthodontics")
    st.markdown("🏥 Sure Align Orthodontix n Dentistry")
    st.markdown("📍 Ahmedabad, Gujarat")
    st.divider()
    lang = st.selectbox("🌐 Language / भाषा", list(LANGUAGES.keys()))
    st.divider()
    st.markdown("### 🚨 Emergency")
    st.markdown("**WhatsApp:** [+916358822642](https://wa.me/916358822642)")
    st.markdown("**Clinic:** Sure Align Orthodontix n Dentistry")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.history = []
        st.rerun()

# ---- Main ----
st.title("🦷 Aligner Coach")
st.caption("Your 24/7 AI guide for clear aligner treatment | Powered by Sarvam.ai")
st.caption("Dr. Ajay Kubavat | Sure Align Orthodontix n Dentistry, Ahmedabad")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message("user"):
        st.write(m["user"])
    with st.chat_message("assistant", avatar="🦷"):
        st.write(m["bot"])

if not st.session_state.history:
    st.markdown("### 💬 Quick Questions:")
    c1, c2 = st.columns(2)
    quick_qs = [
        "How long to wear aligners daily?",
        "My aligner is hurting me",
        "How to clean my aligners?",
        "I lost my aligner tray",
        "My attachment fell off",
        "Can I drink tea with aligners?"
    ]
    for i, q in enumerate(quick_qs):
        col = c1 if i % 2 == 0 else c2
        if col.button(q, key=f"q{i}", use_container_width=True):
            with st.spinner("🦷 Thinking..."):
                rep = chat(q, st.session_state.history)
            st.session_state.history.append({"user": q, "bot": rep})
            st.rerun()

if inp := st.chat_input(f"Ask your question in {lang}..."):
    with st.chat_message("user"):
        st.write(inp)
    with st.spinner("🦷 Dr. Ajay's AI is thinking..."):
        rep = chat(inp, st.session_state.history)
    with st.chat_message("assistant", avatar="🦷"):
        st.write(rep)
    st.session_state.history.append({"user": inp, "bot": rep})
    st.rerun()
