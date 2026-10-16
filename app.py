import streamlit as st
import glob, os, base64
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

st.set_page_config(page_title="Assistant IMO Bot", page_icon="🚢", layout="wide")

with st.sidebar:
    st.markdown("### ☰ IMO RAG Files")
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    if not files: files = glob.glob("master_*.txt")
    st.write(f"Total: {len(files)} files")
    for f in files[:20]:
        st.markdown(f"📄 `{f}`")
    st.markdown("---")
    st.markdown("Assistant IMO Bot - IMO Online")

def get_logo_base64():
    for name in ["bot_logo.png", "bot.png", "/mnt/data/image_20261016_021908.webp", "image_20261016_021908.webp"]:
        if os.path.exists(name):
            with open(name, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:38px;height:38px;border-radius:50%;background:white;padding:2px;">' if logo_b64 else '<div style="background:white;color:#0b2a5b;font-weight:900;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;">BOT</div>'

st.markdown(f"""
<style>
   header, footer {{visibility: hidden;}}
  .stApp {{ background: #e5ddd5; }}
   /* RIGHT CORNER FIX - Manage app + IMO logo */
   iframe[title="streamlitAppDeploymentButton"]{{position:fixed!important;top:10px!important;right:120px!important;bottom:auto!important;z-index:99999!important;opacity:0.9!important;}}
   div[data-testid="stAppDeployButton"],div[class*="viewerBadge"]{{position:fixed!important;top:10px!important;right:120px!important;bottom:auto!important;z-index:99999!important;}}
   div[data-testid="stToolbar"]{{right:140px!important;}}
   /* Header */
.imo-header{{background:#0b2a5b;padding:12px 16px;color:white;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:1000;height:60px;}}
.imo-logo-right{{background:white;color:#0b2a5b;font-weight:900;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;position:fixed!important;right:10px!important;top:11px!important;z-index:10001!important;}}
.chat-wrap{{margin-top:75px;margin-bottom:95px;max-width:800px;margin-left:auto;margin-right:auto;}}
.msg-user{{background:#dcf8c6;color:#000!important;padding:10px 14px;border-radius:12px 0px 12px 12px;margin:8px 0 8px auto;max-width:82%;float:right;clear:both;box-shadow:0 1px 1px rgba(0,0,0,0.15);font-size:15px;}}
.msg-bot{{background:#ffffff;color:#000!important;padding:10px 14px;border-radius:0px 12px 12px 12px;margin:8px auto 8px 0;max-width:85%;float:left;clear:both;box-shadow:0 1px 1px rgba(0,0,0,0.15);font-size:14px;border:1px solid #e0e0e0;white-space:pre-wrap;}}
.msg-bot *{{color:#000!important;}}
.msg-time{{font-size:10px;color:#667781!important;margin-top:5px;text-align:right;}}
div[data-testid="stChatInput"]{{position:fixed!important;bottom:5px!important;left:8px!important;right:8px!important;background:#f0f0f0!important;padding:8px!important;z-index:1001!important;border-radius:25px!important;max-width:800px;margin:0 auto;}}
</style>
<div class="imo-header">
    <div style="display:flex; align-items:center; gap:12px;">
        {logo_html}
    </div>
    <div style="flex:1; text-align:center;">
        <div style="font-weight:700; font-size:17px; letter-spacing:0.5px;">Assistant IMO Bot</div>
        <div style="font-size:11px; opacity:0.9;">IMO RAG - Online</div>
    </div>
    <div class="imo-logo-right">IMO</div>
</div>
""", unsafe_allow_html=True)

@st.cache_resource
def get_gemini_client():
    try:
        from google import genai
        api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key: return None, False, "No API Key"
        client = genai.Client(api_key=api_key)
        return client, True, "OK"
    except Exception as e:
        return None, False, str(e)

gemini_client, gemini_ok, gemini_msg = get_gemini_client()

@st.cache_resource
def load_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    if not files: files = glob.glob("master_*.txt")
    txt = ""
    for f in files:
        try: txt += open(f, 'r', encoding='utf-8', errors='ignore').read() + "\n"
        except: pass
    chunks = [c.strip() for c in txt.split("---CHUNK---") if len(c.strip())>80]
    return chunks

chunks = load_chunks()
@st.cache_resource
def build_tfidf(_chunks):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000, ngram_range=(1,2))
    tfidf_matrix = vectorizer.fit_transform(_chunks)
    return vectorizer, tfidf_matrix
vectorizer, tfidf_matrix = build_tfidf(chunks)

def get_best_chunks_smart(question, chunks, vectorizer, tfidf_matrix, top_k=2):
    q_lower = question.lower()
    good_idx = []
    for i, c in enumerate(chunks):
        # KACHRA FILTER - Index wale chunks hatao
        if c.lower().count("annex") > 10 and len(c) < 3000:
            continue
        if c.lower().count("what is") > 5: # TOC
            continue
        good_idx.append(i)
    if not good_idx:
        good_idx = list(range(len(chunks)))
    sub_chunks = [chunks[i] for i in good_idx]
    sub_matrix = vectorizer.transform(sub_chunks)
    q_vec = vectorizer.transform([question])
    scores = (sub_matrix * q_vec.T).toarray().ravel()
    top = np.argsort(scores)[-top_k:][::-1]
    return [sub_chunks[i] for i in top]

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Good Day i am assistant imo bot.. how can i help you"}]

st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in st.session_state.messages:
    role_class = "msg-user" if m["role"]=="user" else "msg-bot"
    st.markdown(f'<div class="{role_class}">{m["content"]}<div class="msg-time">{datetime.now().strftime("%H:%M")} ✓✓</div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

ALL_FLASH_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-1.5-flash-001", "gemini-flash-latest"]

def generate_with_fallback(client, prompt):
    for model_name in ALL_FLASH_MODELS:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response.text:
                return response.text, model_name
        except:
            continue
    return None, None

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    results = get_best_chunks_smart(prompt, chunks, vectorizer, tfidf_matrix, top_k=2)
    context = "\n\n---\n\n".join(results)[:5000]

    if gemini_ok and gemini_client:
        final_prompt = f"""User asked: {prompt}
Context (2 best chunks only): {context}

INSTRUCTION - BE SHORT AND SPECIFIC:
- Do NOT list all Annexes if only one Annex asked
- Give 3-4 lines obligations only, not full index
- If context is list of annexes, extract only relevant one and explain

Answer:"""
        ans, used_model = generate_with_fallback(gemini_client, final_prompt)
        answer = ans if ans else f"Info: {context[:2000]}"
    else:
        answer = context[:2000]

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
