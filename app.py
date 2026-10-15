import streamlit as st
import glob, os
from datetime import datetime

st.set_page_config(
    page_title="Assistant IMO Bot",
    page_icon="🚢",
    layout="centered"
)

# ===== IMO BLUE WHATSAPP FIXED CSS =====
st.markdown("""
<style>
   header {visibility: hidden;}
   .stApp { background: #e5ddd5; }
   
   /* TOP HEADER - FIXED BLUE IMO */
   .imo-header {
        background: #0b2a5b; /* IMO BLUE */
        padding: 14px 18px;
        color: white;
        display: flex;
        align-items: center;
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
   .imo-logo {
        background: white; color: #0b2a5b; font-weight: 900;
        width: 38px; height: 38px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; margin-right: 12px; border: 2px solid #1e5db1;
    }
   
   /* CHAT AREA */
   .chat-wrapper {
        margin-top: 75px;
        margin-bottom: 90px;
        padding: 10px;
        min-height: 75vh;
   }
   .msg-user {
        background: #dcf8c6; padding: 10px 14px; border-radius: 10px 0px 10px 10px;
        margin: 8px 0 8px auto; max-width: 80%; float: right; clear: both;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1); font-size: 14px;
    }
   .msg-bot {
        background: white; padding: 10px 14px; border-radius: 0px 10px 10px 10px;
        margin: 8px auto 8px 0; max-width: 80%; float: left; clear: both;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1); font-size: 14px;
    }
   .msg-time { font-size: 10px; color: #667781; margin-top: 4px; text-align: right; }
   
   /* BOTTOM INPUT - FIXED LIKE WHATSAPP */
   div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important; left: 0 !important; right: 0 !important;
        background: #f0f0f0 !important;
        padding: 10px 15px !important;
        z-index: 1000 !important;
        border-top: 1px solid #ddd !important;
   }
   div[data-testid="stChatInput"] textarea {
        border-radius: 25px !important;
   }
</style>
""", unsafe_allow_html=True)

# ===== BLUE HEADER - Assistant IMO Bot =====
st.markdown("""
<div class="imo-header">
    <div class="imo-logo">IMO</div>
    <div>
        <div style="font-weight:700; font-size:17px; line-height:18px;">Assistant IMO Bot</div>
        <div style="font-size:12px; opacity:0.85; margin-top:2px;">IMO CODE • online • ChromaDB + Gemini</div>
    </div>
    <div style="margin-left:auto; font-size:20px;">📞</div>
</div>
""", unsafe_allow_html=True)

# ===== LOAD =====
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

# ===== SESSION =====
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"👋 Assalamualaikum! Main **Assistant IMO Bot** hu.\n\nMere paas **{len(chunks)} IMO CODE** chunks hai ({fcount} files). Aap Hong Kong Convention, SOLAS, ISPS, Bunker ke baare me pucho."}
    ]

# Chat display
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
for m in st.session_state.messages:
    if m["role"] == "user":
        st.markdown(f'<div class="msg-user">{m["content"]}<div class="msg-time">{datetime.now().strftime("%H:%M")} ✓✓</div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
    else:
        # convert markdown simple
        text = m["content"].replace("\n", "<br>")
        st.markdown(f'<div class="msg-bot">{text}<div class="msg-time">{datetime.now().strftime("%H:%M")}</div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===== FIXED BOTTOM INPUT (WhatsApp style) =====
if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # RAG search
    q_low = prompt.lower()
    results = [c for c in chunks if any(w in c.lower() for w in q_low.split() if len(w)>3)][:3]
    if not results:
        results = chunks[:2]

    ans = f"**IMO CODE Answer:**\n\n"
    for r in results[:2]:
        src = r[:40].replace("SOURCE:", "").strip()
        ans += f"📄 `{src}`\n{r[:400]}...\n\n---\n\n"

    st.session_state.messages.append({"role": "assistant", "content": ans})
    st.rerun()
