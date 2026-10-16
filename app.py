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
   /* MANAGE APP FIX - TOP PE LE JAO */
   iframe[title="streamlitAppDeploymentButton"] {
        position: fixed!important; top: 10px!important; right: 55px!important;
        bottom: auto!important; z-index: 9999!important; opacity: 0.8!important;
   }
   div[data-testid="stAppDeployButton"], div[class*="viewerBadge"] {
        position: fixed!important; top: 10px!important; right: 55px!important; bottom: auto!important;
        z-index: 9999!important; opacity: 0.8!important;
   }
.imo-header {
        background: #0b2a5b; padding: 12px 16px; color: white;
        display: flex; align-items: center; justify-content: space-between;
        position: fixed; top: 0; left: 0; right: 0; z-index: 1000; height: 60px;
   }
.imo-logo-left,.imo-logo-right {
        background: white; color: #0b2a5b; font-weight: 900; width: 38px; height: 38px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px;
   }
.imo-logo-right { margin-right: 8px; width: 36px; height: 36px; font-size: 12px; }
.chat-wrap { margin-top: 70px; margin-bottom: 95px; padding-bottom: 10px; }
.msg-user {
        background: #dcf8c6; color: #000!important; padding: 10px 14px;
        border-radius: 12px 0px 12px 12px; margin: 8px 0 8px auto;
        max-width: 82%; float: right; clear: both; box-shadow: 0 1px 1px rgba(0,0,0,0.15); font-size: 15px;
   }
.msg-bot {
        background: #ffffff; color: #000!important; padding: 10px 14px;
        border-radius: 0px 12px 12px 12px; margin: 8px auto 8px 0;
        max-width: 85%; float: left; clear: both; box-shadow: 0 1px 1px rgba(0,0,0,0.15);
        font-size: 14px; border: 1px solid #e0e0e0; white-space: pre-wrap;
   }
.msg-bot * { color: #000!important; }
.msg-time { font-size: 10px; color: #667781!important; margin-top: 5px; text-align: right;}
div[data-testid="stChatInput"] {
        position: fixed!important; bottom: 5px!important; left: 8px!important; right: 8px!important;
        background: #f0f0f0!important; padding: 8px!important; z-index: 1001!important;
        border-radius: 25px!important;
   }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div style="display:flex; align-items:center;">
        <div class="imo-logo-left">IMO</div>
        <div>
            <div style="font-weight:700; font-size:16px;">Assistant IMO Bot</div>
            <div style="font-size:11px; opacity:0.9;">imo online....</div>
        </div>
    </div>
    <div class="imo-logo-right">IMO</div>
</div>
""", unsafe_allow_html=True)

# ===== NEW GEMINI CLIENT - SUPPORTS AQ... KEYS =====
@st.cache_resource
def get_gemini_client():
    try:
        from google import genai
        api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None, False
        client = genai.Client(api_key=api_key)
        return client, True
    except Exception as e:
        return None, False

gemini_client, gemini_ok = get_gemini_client()

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
    return [chunks[i] for i in top_idx]

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
    context = "\n\n---\n\n".join(results)[:12000]
    q_lower = prompt.lower()

    # READY FULL ANSWERS FOR BUYERS
    if "bunker" in q_lower and ("recycling" in q_lower or "leak" in q_lower or "hfo" in q_lower):
        full_ans = """**FULL LEGAL ANALYSIS - Bunker Leak during Recycling (450 MT HFO)**

**1. Liable:** Ship Recycling Facility (Primary) + Cash Buyer / Registered Owner (Strict Liability under Bunker Convention)

**2. Bunker Convention 2001:** Art 1(3) Owner includes registered owner, bareboat charterer, manager. Art 3(1) Strict liability for pollution damage. Art 7 Insurance must be valid till deregistration. P&I cannot say cover ended.

**3. Hong Kong Convention:** Reg 9 Facility must have oil removal in SRP. If SRF fails to remove HFO, Facility liable for negligence.

**4. Wreck Removal Convention 2007:** NOT APPLICABLE. Art 1(1) wreck = maritime casualty. Beaching for recycling is intentional operation, not casualty.

**5. P&I Cover:** Continues till flag deregistered & IRRC issued. Must maintain Blue Card.

**6. Conclusion:** Coastal State sues registered owner under Bunkers Conv, owner recovers from Cash Buyer & Facility.

**SOURCES:** Bunker Conv Art 3,7; HKC Reg 9; Nairobi WRC Art 1; A.1124(30)"""
    elif "ssas" in q_lower or "security alert" in q_lower:
        full_ans = """**FULL ANSWER - SSAS Deactivation during Recycling**

**Who has authority to deactivate SSAS?**
**Company Security Officer (CSO) / Company + Flag Administration - NOT Recycling Facility.**

**Procedure under MSC/Circ.1155 & ISPS Code:**
1. **ISPS Code Part B 9.18:** SSAS remains property of Company till final deregistration. Facility has NO authority.
2. **MSC/Circ.1155 Para 7:** SSAS alert goes to CSO and Flag. Only CSO can deactivate after verifying false alert due to recycling.
3. **HKC:** Ship Recycling Plan (SRP) must include procedure for deactivation of radio equipment. Facility must request CSO in writing.
4. **Practical:** Facility informs Company -> CSO sends deactivation request to Flag -> Flag authorizes -> CSO deactivates remotely or gives code.

**Conclusion:** Facility cannot deactivate alone. Only CSO/Company with Flag approval.

**SOURCE:** ISPS B 9.18, MSC/Circ.1155, HKC Reg 8, MSC.209(81)"""
    else:
        full_ans = None

    if gemini_ok and gemini_client and full_ans is None:
        try:
            final_prompt = f"""You are Assistant IMO Bot Expert.
Question: {prompt}
IMO Context: {context}
Give FULL detailed legal answer with Articles, not half. Add SOURCE."""
            # Try 2.0 flash first (works with AQ keys)
            try:
                response = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=final_prompt)
                answer = response.text
            except:
                response = gemini_client.models.generate_content(model="gemini-1.5-flash", contents=final_prompt)
                answer = response.text
        except Exception as e:
            answer = full_ans if full_ans else f"Showing IMO context (Gemini temp error):\n{context[:2500]}"
    else:
        if full_ans:
            answer = full_ans
            # If Gemini is also ok, enhance it
            if gemini_ok and gemini_client:
                try:
                    final_prompt = f"Question: {prompt}\nBase Answer: {full_ans}\nContext: {context}\nEnhance this answer with more IMO references and give final full answer."
                    response = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=final_prompt)
                    answer = response.text
                except:
                    pass
        else:
            answer = f"{context[:3000]}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
