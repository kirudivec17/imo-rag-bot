import streamlit as st
import glob, os
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

st.set_page_config(page_title="Assistant IMO Bot", page_icon="🚢", layout="centered")

st.markdown("""
<style>
   header, footer {visibility: hidden;}
.stApp { background: #e5ddd5; }
   iframe[title="streamlitAppDeploymentButton"]{position:fixed!important;top:10px!important;right:55px!important;bottom:auto!important;z-index:9999!important;opacity:0.8!important;}
   div[data-testid="stAppDeployButton"],div[class*="viewerBadge"]{position:fixed!important;top:10px!important;right:55px!important;bottom:auto!important;z-index:9999!important;opacity:0.8!important;}
.imo-header{background:#0b2a5b;padding:12px 16px;color:white;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:1000;height:60px;}
.imo-logo-left,.imo-logo-right{background:white;color:#0b2a5b;font-weight:900;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;}
.imo-logo-right{margin-right:8px;width:36px;height:36px;font-size:12px;}
.chat-wrap{margin-top:70px;margin-bottom:95px;padding-bottom:10px;}
.msg-user{background:#dcf8c6;color:#000!important;padding:10px 14px;border-radius:12px 0px 12px 12px;margin:8px 0 8px auto;max-width:82%;float:right;clear:both;box-shadow:0 1px 1px rgba(0,0,0,0.15);font-size:15px;}
.msg-bot{background:#ffffff;color:#000!important;padding:10px 14px;border-radius:0px 12px 12px 12px;margin:8px auto 8px 0;max-width:85%;float:left;clear:both;box-shadow:0 1px 1px rgba(0,0,0,0.15);font-size:14px;border:1px solid #e0e0e0;white-space:pre-wrap;}
.msg-bot *{color:#000!important;}
.msg-time{font-size:10px;color:#667781!important;margin-top:5px;text-align:right;}
div[data-testid="stChatInput"]{position:fixed!important;bottom:5px!important;left:8px!important;right:8px!important;background:#f0f0f0!important;padding:8px!important;z-index:1001!important;border-radius:25px!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div style="display:flex; align-items:center;">
        <div class="imo-logo-left">IMO</div>
        <div><div style="font-weight:700; font-size:16px;">Assistant IMO Bot</div><div style="font-size:11px; opacity:0.9;">imo online....</div></div>
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
    vectorizer = TfidfVectorizer(stop_words='english', max_features=8000)
    tfidf_matrix = vectorizer.fit_transform(_chunks)
    return vectorizer, tfidf_matrix
vectorizer, tfidf_matrix = build_tfidf(chunks)

def get_best_chunks(question, chunks, vectorizer, tfidf_matrix, top_k=3):
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

# SAARE FLASH MODELS - JO CHALEGA AUTO PAKDEGA
ALL_FLASH_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-latest",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
]

def generate_with_fallback(client, prompt):
    last_error = ""
    for model_name in ALL_FLASH_MODELS:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response.text:
                return response.text, model_name, None
        except Exception as e:
            last_error = str(e)
            continue
    return None, None, last_error

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    q_lower = prompt.lower()

    if "gemini key" in q_lower or "key working" in q_lower:
        if gemini_ok and gemini_client:
            test_prompt = "Say 'KEY WORKING' in 2 words"
            ans, used_model, err = generate_with_fallback(gemini_client, test_prompt)
            if ans:
                final = f"✅ **GEMINI KEY WORKING!**\n\nWorking Model: `{used_model}`\nYour Key: AQ... (IMO RAG BOT)\nResponse: {ans}\n\nAb koi bhi IMO sawal pucho - pura answer aayega!"
            else:
                final = f"❌ Key error: {err}\n\nEnable API: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com"
        else:
            final = f"❌ {gemini_msg}"
        st.session_state.messages.append({"role": "assistant", "content": final})
        st.rerun()

    results = get_best_chunks(prompt, chunks, vectorizer, tfidf_matrix, top_k=3)
    context = "\n\n---\n\n".join(results)[:10000]

    if gemini_ok and gemini_client:
        final_prompt = f"You are Assistant IMO Bot expert. Question: {prompt}\nIMO Context: {context}\nGive FULL detailed answer with Articles, no half answer. Add SOURCE."
        ans, used_model, err = generate_with_fallback(gemini_client, final_prompt)
        if ans:
            answer = f"{ans}\n\n---\n✅ Model Used: `{used_model}`"
        else:
            answer = f"**Gemini Error - Tried all models:** {err[:800]}\n\n**IMO Data from your files:**\n{context[:2500]}\n\nFix: Enable Generative Language API"
    else:
        answer = f"Key error: {gemini_msg}\n\n{context[:2500]}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
