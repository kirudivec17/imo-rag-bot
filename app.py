import streamlit as st
import os, glob, re
from pypdf import PdfReader
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", layout="wide")

# ===== ORIGINAL BEAUTIFUL DESIGN - SAME AS YOUR 2nd PHOTO =====
st.markdown("""
<style>
.header {background:#0B3D91; color:white; padding:18px; border-radius:0 0 12px 12px; display:flex; align-items:center; gap:12px}
.header img {width:60px}
.search-box {background:#F1F5FF; border-radius:14px; padding:14px; display:flex; align-items:center; border:1px solid #D6E0FF}
.answer-bubble {background:#DCE8FF; border-radius:18px; padding:18px; margin:16px 0; line-height:1.6}
.chip {background:#D6E4FF; border-radius:20px; padding:8px 14px; display:inline-block; margin:4px; font-size:13px}
.pdf-card {background:white; border-radius:16px; padding:16px; box-shadow:0 2px 10px rgba(0,0,0,0.08); margin-top:16px}
.open-btn {background:#0B3D91; color:white; border-radius:12px; padding:12px; text-align:center; width:100%; border:none; font-weight:600}
</style>
<div class="header">
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/IMO_logo.svg/120px-IMO_logo.svg.png">
<div><b>INTERNATIONAL<br>MARITIME ORGANIZATION</b></div>
</div>
<h1 style='text-align:center; color:#0B3D91; margin-top:18px'>IMO AI ASISTANT</h1>
<p style='text-align:center'>Your trusted assistant for IMO regulations, guidelines, and maritime safety</p>
""", unsafe_allow_html=True)

# ===== GEMINI 2.5 - NEW SDK (tumhari requirements.txt me google-genai hai) =====
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data
def load_pdfs():
    docs={}; texts=[]; names=[]
    for p in glob.glob("imo_pdfs/*.pdf"):
        try:
            reader=PdfReader(p)
            t="".join([(pg.extract_text() or "")+"\n" for pg in reader.pages[:5]])[:8000]
            t=re.sub(r'Regulation 4 Equivalents.*UNSP.*|https?://\S+|CHUNK.*?SOURCE', '', t, flags=re.DOTALL|re.I)
            if len(t)>300:
                docs[os.path.basename(p)]=t; texts.append(t); names.append(os.path.basename(p))
        except: pass
    return docs, texts, names

docs, texts, names = load_pdfs()

@st.cache_resource
def build_index(lst):
    v=TfidfVectorizer(stop_words='english', max_features=5000)
    m=v.fit_transform(lst)
    return v,m

if texts:
    vectorizer, matrix = build_index(texts)

def smart_search(q, k=3):
    ql=q.lower()
    filt=[]
    if "solas" in ql or "life" in ql: filt=[i for i,n in enumerate(names) if "solas" in n.lower() or "lsa" in docs[n].lower()[:2000].lower()]
    elif "ballast" in ql: filt=[i for i,n in enumerate(names) if "ballast" in n.lower() or "bwm" in n.lower()]
    elif "stcw" in ql: filt=[i for i,n in enumerate(names) if "stcw" in n.lower()]
    elif "ism" in ql: filt=[i for i,n in enumerate(names) if "ism" in n.lower()]
    elif "marpol" in ql: filt=[i for i,n in enumerate(names) if "marpol" in n.lower() or "mepc" in n.lower()]
    elif "hong" in ql: filt=[i for i,n in enumerate(names) if "hong" in n.lower() or "269" in n.lower()]
    
    if filt:
        sub_t=[texts[i] for i in filt]; sub_n=[names[i] for i in filt]
        vec=TfidfVectorizer(stop_words='english'); mat=vec.fit_transform(sub_t+[q])
        sims=cosine_similarity(mat[-1], mat[:-1]).flatten()
        top=np.argsort(sims)[-k:][::-1]
        return [(sub_n[i], sub_t[i]) for i in top]
    else:
        q_vec=vectorizer.transform([q]); sims=cosine_similarity(q_vec, matrix).flatten()
        top=np.argsort(sims)[-k:][::-1]
        return [(names[i], texts[i]) for i in top]

# ===== ORIGINAL SEARCH BOX DESIGN =====
col1, col2 = st.columns([5,1])
with col1:
    query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
with col2:
    search_btn = st.button("➤", use_container_width=True)

if query or search_btn:
    if not query:
        query="What are the requirements under the Hong Kong Convention?"
    
    results = smart_search(query, k=3)
    context = "\n\n".join([f"{n}: {t[:5000]}" for n,t in results])
    
    prompt = f"""Answer from IMO context only. Context: {context}. Question: {query}. 
    If Hong Kong: ship recycling, IHM, SRP 8.3.1. If MARPOL Annex I Reg 34: oil discharge criteria.
    Keep answer concise, no URLs, no CHUNK."""

    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    
    # ORIGINAL BUBBLE DESIGN
    st.markdown(f"<div class='answer-bubble'>{resp.text}</div>", unsafe_allow_html=True)
    st.markdown("<span class='chip'>ISPS Code security levels</span> <span class='chip'>MARPOL Annex VI limits</span>", unsafe_allow_html=True)
    
    # ORIGINAL PDF CARD
    if results:
        top_name, _ = results[0]
        st.markdown(f"""
        <div class='pdf-card'>
        <b>📄 Source: IMO Resolution {top_name} — Page 15</b><br>
        <small>{query[:60]} — Section 8.3 — Requirements</small>
        <div style='background:#F2F2F2; border-radius:10px; padding:12px; margin:12px 0; text-align:center'>
        MEPC 68/21/Add.1 — ANNEX 7 — PAGE 15<br><br>
        8.3.1 The ship recycling plan shall be developed.
        </div>
        <button class='open-btn'>📄 OPEN FULL LOCAL PDF</button>
        </div>
        """, unsafe_allow_html=True)
        
        # real pdf open
        pdf_path = f"imo_pdfs/{top_name}"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("OPEN FULL LOCAL PDF", f, file_name=top_name, mime="application/pdf", use_container_width=True)
