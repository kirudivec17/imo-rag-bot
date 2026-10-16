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

 /* < BUTTON TOP RIGHT */
 iframe[title="streamlitAppDeploymentButton"] {
        position: fixed!important; top: 65px!important; right: 8px!important;
        bottom: auto!important; width: 28px!important; height: 28px!important;
        z-index: 2000!important; opacity: 0.8!important;
        background: black!important; border-radius: 6px!important;
 }
 div[class*="viewerBadge"], div[class*="stAppDeployButton"] {
        position: fixed!important; top: 65px!important; right: 8px!important; bottom: auto!important;
        width: 28px!important; height: 28px!important; overflow: hidden!important;
        background: #000!important; border-radius: 5px!important; opacity: 0.7!important; z-index: 2000!important;
 }
 div[class*="viewerBadge"] span, div[class*="stAppDeployButton"] span { display: none!important; }
 div[class*="viewerBadge"]::after, div[class*="stAppDeployButton"]::after {
        content: "<"!important; display: block!important; color: white!important;
        text-align: center!important; font-weight: bold!important; line-height: 28px!important;
 }

.imo-header {
        background: #0b2a5b; padding: 12px 16px; color: white;
        display: flex; align-items: center; justify-content: space-between;
        position: fixed; top: 0; left: 0; right: 0; z-index: 1000; height: 60px;
   }
.imo-logo-left {
        background: white; color: #0b2a5b; font-weight: 900; width: 38px; height: 38px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 13px; margin-right: 10px;
   }
.imo-logo-right {
        background: white; color: #0b2a5b; font-weight: 900; width: 36px; height: 36px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 12px; margin-right: 35px;
   }
.chat-wrap { margin-top: 70px; margin-bottom: 85px; padding-bottom: 15px; }
.msg-user {
        background: #dcf8c6; color: #000!important; padding: 10px 14px;
        border-radius: 12px 0px 12px 12px; margin: 8px 0 8px auto;
        max-width: 82%; float: right; clear: both;
        box-shadow: 0 1px 1px rgba(0,0,0,0.15); font-size: 15px;
   }
.msg-bot {
        background: #ffffff; color: #000!important; padding: 10px 14px;
        border-radius: 0px 12px 12px 12px; margin: 8px auto 8px 0;
        max-width: 85%; float: left; clear: both;
        box-shadow: 0 1px 1px rgba(0,0,0,0.15); font-size: 14px;
        border: 1px solid #e0e0e0; white-space: pre-wrap;
   }
.msg-bot * { color: #000!important; }
.msg-time { font-size: 10px; color: #667781!important; margin-top: 5px; text-align: right;}
div[data-testid="stChatInput"] {
        position: fixed!important; bottom: 0!important; left: 0!important; right: 0!important;
        background: #f0f0f0!important; padding: 8px 12px!important; z-index: 1001!important;
   }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div style="display:flex; align-items:center;">
        <div class="imo-logo-left">IMO</div>
        <div>
            <div style="font-weight:700; font-size:16px;">Assistant IMO Bot</div>
            <div style="font-size:11px; opacity:0.9; margin-top:1px;">imo online....</div>
        </div>
    </div>
    <div class="imo-logo-right">IMO</div>
</div>
""", unsafe_allow_html=True)

@st.cache_resource
def get_gemini_model():
    try:
        import google.generativeai as genai
        api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            return model, True
        else:
            return None, False
    except:
        return None, False

gemini_model, gemini_ok = get_gemini_model()

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
    return chunks

chunks = load_chunks()

@st.cache_resource
def build_tfidf(_chunks):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=8000)
    tfidf_matrix = vectorizer.fit_transform(_chunks)
    return vectorizer, tfidf_matrix

vectorizer, tfidf_matrix = build_tfidf(chunks)

def get_best_chunks(question, chunks, vectorizer, tfidf_matrix, top_k=4):
    q_vec = vectorizer.transform([question])
    scores = (tfidf_matrix * q_vec.T).toarray().ravel()
    top_idx = np.argsort(scores)[-top_k:][::-1]
    return [chunks[i] for i in top_idx if scores[i] > 0.001]

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Good Day i am assistant imo bot.. how can i help you"}
    ]

st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in st.session_state.messages:
    role_class = "msg-user" if m["role"]=="user" else "msg-bot"
    st.markdown(f'<div class="{role_class}">{m["content"]}<div class="msg-time">{datetime.now().strftime("%H:%M")} ✓✓</div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    results = get_best_chunks(prompt, chunks, vectorizer, tfidf_matrix, top_k=4)
    if not results:
        results = chunks[:3]
    context = "\n\n---\n\n".join(results)[:12000]

    if gemini_ok and gemini_model:
        try:
            final_prompt = f"""You are Assistant IMO Bot - Expert in IMO Conventions.
User Question: {prompt}

Use ONLY this authentic IMO context:
{context}

Give FULL DETAILED ANSWER:
1. Direct Answer - Who is liable?
2. Bunker Convention 2001 Article 3 & 4 applicability
3. Hong Kong Convention Regulation 9 & Article 9 liability
4. Wreck Removal Convention - Is it applicable?
5. P&I Club cover - when it ends?
6. Practical Conclusion

Add SOURCE references. Give complete answer, not short."""
            response = gemini_model.generate_content(final_prompt, generation_config={"max_output_tokens": 3000, "temperature": 0.2})
            answer = response.text
        except Exception as e:
            answer = results[0][:2000]
    else:
        answer = results[0][:2000] + "\n\n(Add GEMINI_API_KEY in Secrets for AI analysis)"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
