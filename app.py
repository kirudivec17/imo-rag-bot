import streamlit as st
import glob, os, base64
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

st.set_page_config(page_title="Assistant IMO Bot", page_icon="🚢", layout="wide")

# --- SIDEBAR 3-LINE MENU - IMO FILES ---
with st.sidebar:
    st.markdown("### ☰ IMO RAG Files")
    st.markdown("---")
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    if not files: files = glob.glob("master_*.txt")
    st.write(f"**Total Files Loaded:** {len(files)}")
    for f in files[:20]: # 20 tak dikhayega
        size_kb = os.path.getsize(f)//1024
        st.markdown(f"📄 `{f}` - {size_kb} KB")
    st.markdown("---")
    st.markdown("**Assistant IMO Bot**\nBuilt for IMO Conventions")

# Load bot logo if exists
def get_logo_base64():
    for name in ["bot_logo.png", "bot.png", "image_20261016_021908.webp", "/mnt/data/image_20261016_021908.webp"]:
        if os.path.exists(name):
            with open(name, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:38px;height:38px;border-radius:50%;background:white;padding:2px;">' if logo_b64 else '<div style="background:white;color:#0b2a5b;font-weight:900;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;">IMO</div>'

st.markdown(f"""
<style>
   header, footer {{visibility: hidden;}}
.stApp {{ background: #e5ddd5; }}
   iframe[title="streamlitAppDeploymentButton"]{{position:fixed!important;top:10px!important;right:55px!important;bottom:auto!important;z-index:9999!important;opacity:0.8!important;}}
   div[data-testid="stAppDeployButton"],div[class*="viewerBadge"]{{position:fixed!important;top:10px!important;right:55px!important;bottom:auto!important;z-index:9999!important;opacity:0.8!important;}}
.imo-header{{background:#0b2a5b;padding:12px 16px;color:white;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:1000;height:60px;}}
.imo-logo-right{{background:white;color:#0b2a5b;font-weight:900;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;margin-right:50px;}}
.chat-wrap{{margin-top:75px;margin-bottom:95px;padding-bottom:10px;max-width:800px;margin-left:auto;margin-right:auto;}}
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
    <div style="flex:1; text-align:center; margin-right:40px;">
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
    # SMART FILTER - agar Annex 1 pucha to sirf Annex 1 wale chunks do
    q_lower = question.lower()
    filtered_idx = []
    if "annex 1" in q_lower:
        for i,c in enumerate(chunks):
            if "annex 1" in c.lower() or "annex i" in c.lower() or "obligations of contracting" in c.lower():
                filtered_idx.append(i)
    if filtered_idx:
        sub_chunks = [chunks[i] for i in filtered_idx[:50]]
        sub_matrix = vectorizer.transform(sub_chunks)
        q_vec = vectorizer.transform([question])
        scores = (sub_matrix * q_vec.T).toarray().ravel()
        top = np.argsort(scores)[-top_k:][::-1]
        return [sub_chunks[i] for i in top]
    else:
        q_vec = vectorizer.transform([question])
        scores = (tfidf_matrix * q_vec.T).toarray().ravel()
        top_idx = np.argsort(scores)[-top_k:][::-1]
        return [chunks[i] for i in top_idx]

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
                return response.text, model_name, None
        except Exception as e:
            continue
    return None, None, "All models failed"

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    results = get_best_chunks_smart(prompt, chunks, vectorizer, tfidf_matrix, top_k=2)
    context = "\n\n---\n\n".join(results)[:6000]

    if gemini_ok and gemini_client:
        final_prompt = f"""You are Assistant IMO Bot. User asked: {prompt}
IMO Context (only 2 best chunks): {context}

STRICT RULES:
1. Answer ONLY about what user asked. If user asked Annex 1, talk ONLY Annex 1. Don't list Annex 2,3,4, MARPOL, BC Code etc unless asked.
2. Give short, specific legal answer with obligations.
3. Don't dump whole code list.
4. End with SOURCE.

Example for 'Annex 1 code': Tell what Annex 1 obligations are, not list all Annexes.

Now give clean answer:"""
        ans, used_model, err = generate_with_fallback(gemini_client, final_prompt)
        answer = ans if ans else f"IMO Info: {context[:2000]}"
    else:
        answer = context[:2000]

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
