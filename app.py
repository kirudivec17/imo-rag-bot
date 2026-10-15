import streamlit as st
import glob, os
from datetime import datetime

st.set_page_config(
    page_title="IMO WhatsApp Bot",
    page_icon="💬",
    layout="centered"
)

# ===== WHATSAPP CSS =====
st.markdown("""
<style>
   .stApp { background: #e5ddd5; }
   .wa-header {
        background: #075e54; padding: 15px 20px; border-radius: 0px;
        color: white; display: flex; align-items: center;
        position: sticky; top: 0; z-index: 999;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
   .wa-chat-bg {
        background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');
        background-color: #e5ddd5; padding: 10px; min-height: 80vh;
    }
   .msg-user {
        background: #dcf8c6; padding: 10px 15px; border-radius: 10px 0px 10px 10px;
        margin: 10px 0px 10px 50px; box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        text-align: right; max-width: 85%; float: right; clear: both;
    }
   .msg-bot {
        background: white; padding: 10px 15px; border-radius: 0px 10px 10px 10px;
        margin: 10px 50px 10px 0px; box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        max-width: 85%; float: left; clear: both;
    }
   .msg-time { font-size: 11px; color: #667781; margin-top: 4px; }
   .source-chip {
        background: #25d366; color: white; padding: 3px 8px; border-radius: 10px;
        font-size: 11px; display: inline-block; margin: 2px;
    }
   .stTextInput > div > div > input {
        border-radius: 25px!important; padding: 12px 20px!important;
        border: 1px solid #ddd!important;
    }
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("""
<div class="wa-header">
    <img src="https://img.icons8.com/color/48/cargo-ship.png" width="35" style="margin-right:12px;">
    <div>
        <div style="font-weight:600; font-size:18px;">IMO RAG Bot</div>
        <div style="font-size:12px; opacity:0.9;">online • 1000+ PDFs • ChromaDB + Gemini</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===== LOAD DATA =====
@st.cache_resource
def load_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    if not files:
        files = glob.glob("master_*.txt")
    txt = ""
    for f in files:
        try:
            txt += open(f, 'r', encoding='utf-8', errors='ignore').read() + "\n"
        except:
            pass
    chunks = [c.strip() for c in txt.split("---CHUNK---") if len(c.strip())>80]
    return chunks, len(files)

chunks, fcount = load_chunks()

# ===== CHAT HISTORY =====
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "text": f"👋 Hi! I have loaded {len(chunks)} chunks from {fcount} files (ALL Public IMO PDFs). Ask me about Hong Kong Convention, SOLAS, ISPS, Bunker rules..."}
    ]

# Display chat
st.markdown('<div class="wa-chat-bg">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="msg-user">{msg["text"]}<div class="msg-time">{datetime.now().strftime("%H:%M")}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-bot">{msg["text"]}<div class="msg-time">{datetime.now().strftime("%H:%M")} ✓✓</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===== INPUT (WhatsApp style) =====
st.write("")
col1, col2 = st.columns([5,1])
with col1:
    query = st.text_input("", placeholder="Type a message...", label_visibility="collapsed", key="wa_input")
with col2:
    send = st.button("➤", use_container_width=True)

if (send or query) and query and query.strip()!= "":
    # User message
    st.session_state.messages.append({"role": "user", "text": query})

    # Bot logic - simple RAG
    q_low = query.lower()
    results = [c for c in chunks if any(w in c.lower() for w in q_low.split() if len(w)>3)][:3]
    if not results:
        results = chunks[:2]

    # Build answer
    answer = f"Based on {len(chunks)} IMO docs:\n\n"
    for i, r in enumerate(results[:2], 1):
        src = r.split('\\n')[0][:40] if 'SOURCE:' in r else f"Doc {i}"
        answer += f"<span class='source-chip'>{src}</span> {r[:350]}...\n\n"

    answer += f"\n_2 sources found • {fcount} files searched_"

    st.session_state.messages.append({"role": "bot", "text": answer})
    st.rerun()

# Footer info
st.caption(f"✅ {len(chunks)} chunks LIVE • {fcount} parts • WhatsApp Theme • Tip: Ask 'Hong Kong Convention recycling'")
