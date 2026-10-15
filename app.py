import streamlit as st
import glob, os
from datetime import datetime

st.set_page_config(page_title="Assistant IMO Bot", page_icon="🚢", layout="centered")

# ===== FIX CSS - BLACK TEXT VISIBLE =====
st.markdown("""
<style>
   header, footer {visibility: hidden;}
  .stApp { background: #e5ddd5; }
  .imo-header {
        background: #0b2a5b; padding: 12px 16px; color: white;
        display: flex; align-items: center;
        position: fixed; top: 0; left: 0; right: 0;
        z-index: 1000; height: 60px;
   }
  .imo-logo {
        background: white; color: #0b2a5b; font-weight: 900;
        width: 38px; height: 38px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; margin-right: 10px;
   }
  .chat-wrap { margin-top: 70px; margin-bottom: 95px; padding-bottom: 20px; }

   /* MESSAGE BUBBLES - BLACK TEXT FIX */
  .msg-user {
        background: #dcf8c6; color: #000!important; padding: 10px 14px;
        border-radius: 12px 0px 12px 12px; margin: 8px 0 8px auto;
        max-width: 82%; float: right; clear: both;
        box-shadow: 0 1px 1px rgba(0,0,0,0.15);
        font-size: 15px; line-height: 20px;
   }
  .msg-bot {
        background: #ffffff; color: #000000!important; padding: 10px 14px;
        border-radius: 0px 12px 12px 12px; margin: 8px auto 8px 0;
        max-width: 82%; float: left; clear: both;
        box-shadow: 0 1px 1px rgba(0,0,0,0.15);
        font-size: 14px; line-height: 20px; border: 1px solid #e0e0e0;
   }
  .msg-bot * { color: #000!important; }
  .msg-time { font-size: 10px; color: #667781!important; margin-top: 5px; text-align: right;}

   /* BOTTOM FIXED INPUT */
   div[data-testid="stChatInput"] {
        position: fixed!important; bottom: 0!important;
        left: 0!important; right: 0!important;
        background: #f0f0f0!important; padding: 8px 12px!important;
        z-index: 1001!important;
   }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div class="imo-logo">IMO</div>
    <div>
        <div style="font-weight:700; font-size:16px;">Assistant IMO Bot</div>
        <div style="font-size:11px; opacity:0.9;">IMO CODE • online • ChromaDB + Gemini</div>
    </div>
    <div style="margin-left:auto;">📞</div>
</div>
""", unsafe_allow_html=True)

# ===== AUTO GEMINI CONNECT FROM SECRETS =====
@st.cache_resource
def get_gemini_model():
    try:
        import google.generativeai as genai
        # Secret me se auto key nikalo - 3 naam check karo
        api_key = None
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        elif "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        elif "GEMINI_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_KEY"]
        else:
            api_key = os.environ.get("GEMINI_API_KEY")

        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            return model, True, "✅ Gemini Auto-Connected"
        else:
            return None, False, "⚠️ No Key in Secrets"
    except Exception as e:
        return None, False, f"Error: {e}"

gemini_model, gemini_ok, gemini_status = get_gemini_model()

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

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Assalamualaikum! I am Assistant IMO Bot. I have {len(chunks)} IMO CODE documents. {gemini_status}. Ask anything."}
    ]

st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in st.session_state.messages:
    role_class = "msg-user" if m["role"]=="user" else "msg-bot"
    st.markdown(f'<div class="{role_class}">{m["content"]}<div class="msg-time">{datetime.now().strftime("%H:%M")} ✓✓</div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat Input Fixed Bottom
if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    q_low = prompt.lower()
    results = [c for c in chunks if any(w in c.lower() for w in q_low.split() if len(w)>3)][:3]
    if not results:
        results = chunks[:2]

    context = "\n".join(results)[:4000]

    # Gemini Auto Answer
    if gemini_ok and gemini_model:
        try:
            final_prompt = f"You are Assistant IMO Bot. Use this IMO CODE context:\n{context}\n\nUser Question: {prompt}\nAnswer clearly in simple English with source."
            response = gemini_model.generate_content(final_prompt)
            answer = response.text
        except Exception as e:
            answer = f"IMO CODE Context:\n{results[0][:800]}\n\n(Gemini error: {e})"
    else:
        answer = f"IMO CODE Found:\n{results[0][:800]}\n\n({gemini_status} - Add GEMINI_API_KEY in Streamlit Secrets to enable AI)"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
