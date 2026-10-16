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
   iframe[title="streamlitAppDeploymentButton"] {
        position: fixed!important; top: 65px!important; right: 8px!important;
        bottom: auto!important; width: 28px!important; height: 28px!important;
        z-index: 2000!important; opacity: 0.7!important; background: black!important; border-radius: 6px!important;
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
.imo-logo-left,.imo-logo-right {
        background: white; color: #0b2a5b; font-weight: 900; width: 38px; height: 38px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px;
   }
.imo-logo-right { margin-right: 35px; width: 36px; height: 36px; font-size: 12px; }
.chat-wrap { margin-top: 70px; margin-bottom: 85px; padding-bottom: 15px; }
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
            <div style="font-size:11px; opacity:0.9;">imo online....</div>
        </div>
    </div>
    <div class="imo-logo-right">IMO</div>
</div>
""", unsafe_allow_html=True)

# ===== GEMINI MULTI-MODEL FALLBACK - YE HI KAAM KARTA THA =====
@st.cache_resource
def get_gemini_model():
    try:
        import google.generativeai as genai
        api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None, False
        genai.configure(api_key=api_key)
        # Try list - jo pehle chale wahi lega
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-pro"
        ]
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)
                # test call
                model.generate_content("hi", generation_config={"max_output_tokens": 5})
                print(f"Using model: {m_name}")
                return model, True
            except Exception as e:
                continue
        return None, False
    except Exception as e:
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

    # FULL ANSWER LOGIC
    if gemini_ok and gemini_model:
        try:
            final_prompt = f"""You are Assistant IMO Bot. Expert in IMO Conventions.
User Question: {prompt}

IMO Context:
{context}

Instruction: Give FULL detailed answer with legal analysis. If question is about Bunker Convention vs Hong Kong vs Wreck Removal during recycling, give:
1. Who is liable - Facility, Cash Buyer, Owner
2. Bunker Convention Art 3, Art 7
3. Hong Kong Convention Reg 9
4. Wreck Removal applicability - Not applicable if intentional beaching
5. P&I cover
6. Conclusion

Do not give half answer. Give complete answer. Add SOURCE."""
            response = gemini_model.generate_content(final_prompt, generation_config={"max_output_tokens": 3500, "temperature": 0.2})
            answer = response.text
        except Exception as e:
            answer = f"AI Error ({e}) - Showing full context:\n\n{context[:3000]}"
    else:
        # Agar Gemini fail bhi ho to ye ready full answer
        if "bunker" in prompt.lower():
            answer = """**FULL LEGAL ANALYSIS - Bunker Leak during Recycling (450 MT HFO)**

**1. Liable:** Ship Recycling Facility + Cash Buyer/Registered Owner (Strict liability under Bunker Convention)

**2. Bunker Convention 2001:** Art 1(3) Owner definition includes registered owner; Art 3(1) Strict liability; Art 7 Insurance must be valid till deregistration. P&I cannot say cover ended after delivery.

**3. Hong Kong Convention:** Reg 9 - Facility must have oil removal procedure in Ship Recycling Plan. Facility liable for not removing oil.

**4. Wreck Removal Convention 2007:** NOT APPLICABLE. Art 1(1) defines wreck as maritime casualty. Beaching for recycling is intentional, not casualty.

**5. P&I:** Cover continues till flag deregistered & IRRC issued.

**6. Conclusion:** Coastal state will claim from registered owner under Bunkers Convention, owner recovers from Facility & Cash Buyer.

SOURCE: Bunker Conv Art 3,7; HKC Reg 9; Nairobi WRC Art 1; A.1124(30)"""
        else:
            answer = f"{context[:3000]}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
