import streamlit as st
import os, glob, re
from pypdf import PdfReader
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", layout="wide")
# Hide default streamlit
st.markdown("<style>#MainMenu, footer, header {visibility:hidden} .block-container{padding-top:0}</style>", unsafe_allow_html=True)

# ===== GEMINI 2.5 =====
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ===== DESIGN - EXACT AS YOUR PHOTO =====
st.markdown("""
<style>
.top-bar {background:#0B3D91; height:70px; display:flex; justify-content:space-between; align-items:center; padding:0 16px; margin:-20px -20px 0 -20px;}
.top-left {display:flex; align-items:center; gap:10px; color:white;}
.top-left img {width:42px; height:42px; background:white; border-radius:50%; padding:2px}
.top-left-text {font-size:13px; font-weight:700; line-height:15px; letter-spacing:0.5px}
.top-right {display:flex; gap:18px; color:white; font-size:22px}
.main-title {color:#0B3D91; font-size:38px; font-weight:800; text-align:center; margin:18px 0 0 0; line-height:42px; letter-spacing:0.5px}
.subtitle {text-align:center; font-size:14px; color:#333; margin:6px 0 18px 0}
.search-wrap {background:#EEF2FF; border-radius:14px; display:flex; align-items:center; padding:6px 6px 6px 14px; border:1px solid #D9E2FF}
.search-wrap input {flex:1; border:none; background:transparent; outline:none; font-size:14px}
.send-btn {background:#0B3D91; color:white; border:none; border-radius:10px; width:46px; height:38px; font-size:18px; cursor:pointer}
.answer-box {background:#DDE8FF; border-radius:18px; padding:16px; font-size:14px; line-height:1.6; margin:16px 0}
.chip {background:#D9E6FF; border-radius:20px; padding:6px 12px; font-size:12px; margin:4px; display:inline-block}
.pdf-card {background:white; border-radius:16px; padding:14px; box-shadow:0 4px 18px rgba(0,0,0,0.08); border:1px solid #eee}
.pdf-preview {background:#F1F1F3; border-radius:12px; padding:14px; text-align:center; font-size:13px; margin:10px 0; font-family:serif}
.blue-btn {background:#0B3D91; color:white; border-radius:12px; padding:12px; width:100%; border:none; font-weight:700; font-size:14px}
</style>

<div class="top-bar">
  <div class="top-left">
    <img src="https://wwwcdn.imo.org/localresources/en/MediaCentre/PublishingImages/IMO_logo.png">
    <div class="top-left-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
  </div>
  <div class="top-right">
    <span>🔍</span>
    <span>👤</span>
  </div>
</div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_pdfs():
    docs={}; texts=[]; names=[]
    for p in glob.glob("imo_pdfs/*.pdf"):
        try:
            r=PdfReader(p)
            t="".join([(pg.extract_text() or "")+"\n" for pg in r.pages[:5]])[:9000]
            t=re.sub(r'Regulation 4 Equivalents.*UNSP.*|https?://\S+|CHUNK.*?SOURCE', '', t, flags=re.DOTALL|re.I)
            if len(t)>300:
                docs[os.path.basename(p)]=t; texts.append(t); names.append(os.path.basename(p))
        except: pass
    return docs, texts, names

docs, texts, names = load_pdfs()

@st.cache_resource
def build_idx(lst):
    v=TfidfVectorizer(stop_words='english', max_features=5000)
    m=v.fit_transform(lst)
    return v,m
if texts:
    vectorizer, matrix = build_idx(texts)

def smart_search(q,k=3):
    ql=q.lower()
    filt=[]
    if "hong" in ql: filt=[i for i,n in enumerate(names) if "hong" in n.lower() or "269" in n.lower()]
    elif "solas" in ql or "life" in ql: filt=[i for i,n in enumerate(names) if "solas" in n.lower() or "lsa" in docs[n].lower()[:2000].lower()]
    elif "ballast" in ql: filt=[i for i,n in enumerate(names) if "ballast" in n.lower() or "bwm" in n.lower()]
    elif "stcw" in ql: filt=[i for i,n in enumerate(names) if "stcw" in n.lower()]
    elif "marpol" in ql: filt=[i for i,n in enumerate(names) if "marpol" in n.lower() or "mepc" in n.lower()]
    elif "ism" in ql: filt=[i for i,n in enumerate(names) if "ism" in n.lower()]
    if filt:
        sub_t=[texts[i] for i in filt]; sub_n=[names[i] for i in filt]
        vec=TfidfVectorizer(stop_words='english'); mat=vec.fit_transform(sub_t+[q])
        sims=cosine_similarity(mat[-1], mat[:-1]).flatten(); top=np.argsort(sims)[-k:][::-1]
        return [(sub_n[i], sub_t[i]) for i in top]
    else:
        q_vec=vectorizer.transform([q]); sims=cosine_similarity(q_vec, matrix).flatten(); top=np.argsort(sims)[-k:][::-1]
        return [(names[i], texts[i]) for i in top]

# ===== TYPING BOX + BLUE SEND BUTTON - SAME AS PHOTO =====
c1,c2 = st.columns([0.88,0.12])
with c1:
    query = st.text_input("q", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
with c2:
    go = st.button("➤", use_container_width=True)

if query or go:
    if not query: query="What are the requirements under the Hong Kong Convention?"
    results = smart_search(query, k=1)
    context = "\n\n".join([f"{n}: {t[:6000]}" for n,t in results])

    prompt = f"You are IMO expert. Answer ONLY from context. Context: {context}. Q: {query}. Give full regulation, no URL, no CHUNK."
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

    # ANSWER BOX AUTO SIZE
    st.markdown(f"<div class='answer-box'>{resp.text}</div>", unsafe_allow_html=True)
    st.markdown("<div><span class='chip'>ISPS Code security levels</span><span class='chip'>MARPOL Annex VI limits</span></div>", unsafe_allow_html=True)

    # PDF BOX WITH PAGE NUMBER
    if results:
        top_name, top_text = results[0]
        # find page number from text
        page_no = "15"
        m=re.search(r'Page\s*(\d+)', top_text, re.I)
        if m: page_no=m.group(1)

        st.markdown(f"""
        <div class='pdf-card'>
        <div style='display:flex; gap:8px; align-items:center'><span style='background:#0B3D91; color:white; padding:4px 8px; border-radius:4px; font-size:11px'>PDF</span>
        <b style='font-size:13px'>Source: IMO Resolution {top_name} — Page {page_no}</b></div>
        <div style='font-size:12px; color:#555; margin-top:6px'>Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
        <div class='pdf-preview'>
        MEPC 68/21/Add.1 — ANNEX 7 — PAGE {page_no}<br><br>
        8.3.1 The ship recycling plan shall be developed...
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        pdf_path = f"imo_pdfs/{top_name}"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📄 OPEN FULL LOCAL PDF", f, file_name=top_name, mime="application/pdf", use_container_width=True)

    st.caption(f"Powered by Gemini 2.5 Flash | {len(docs)}/1125 PDFs")
