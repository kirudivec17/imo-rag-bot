import streamlit as st, os, glob, re, base64, uuid
from pypdf import PdfReader
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility:hidden} .block-container{padding-top:0; padding-left:0; padding-right:0}</style>", unsafe_allow_html=True)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# DESIGN - SAME
st.markdown("""
<style>
.top-bar {background:#0B3D91; height:72px; display:flex; justify-content:space-between; align-items:center; padding:0 16px; margin:0;}
.top-left {display:flex; align-items:center; gap:10px; color:white;}
.top-left-icon {width:48px; height:48px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:26px}
.top-left-text {font-size:12px; font-weight:700; line-height:14px;}
.top-right {display:flex; gap:20px; color:white; font-size:22px}
.main-title {color:#0B3D91; font-size:38px; font-weight:800; text-align:center; margin:18px 0 0 0;}
.subtitle {text-align:center; font-size:14px; margin:6px 0 18px 0}
.answer-box {background:#DDE8FF; border-radius:18px; padding:18px; font-size:14px; line-height:1.7; margin:16px 12px}
.pdf-card {background:white; border-radius:16px; padding:14px; margin:12px; box-shadow:0 4px 18px rgba(0,0,0,0.08); border:1px solid #eee}
.pdf-preview {background:#F4F5F7; border-radius:12px; padding:14px; font-size:13px; margin:10px 0; white-space:pre-wrap; line-height:1.5}
</style>
<div class="top-bar"><div class="top-left"><div class="top-left-icon">⚓</div><div class="top-left-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div class="top-right"><span>🔍</span><span>👤</span></div></div>
<div class="main-title">IMO AI ASISTANT</div><div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_pdfs():
    docs={}; texts=[]; names=[]
    pdf_files = glob.glob("imo_pdfs/*.pdf") + glob.glob("**/imo_pdfs/*.pdf", recursive=True)
    pdf_files=list(set(pdf_files))
    for p in pdf_files:
        try:
            name=os.path.basename(p)
            r=PdfReader(p)
            txt="".join([(pg.extract_text() or "")+"\n" for pg in r.pages[:12]])[:15000]
            if len(txt)>200:
                docs[name]={"path":p, "text":txt}
                texts.append(txt); names.append(name)
        except: pass
    return docs, texts, names
docs, texts, names = load_pdfs()

@st.cache_resource
def build_idx(lst):
    v=TfidfVectorizer(stop_words='english', max_features=8000)
    return v, v.fit_transform(lst)
if texts:
    vectorizer, matrix = build_idx(texts)

def smart_search(q,k=1): # k=1 hi rakho duplicate na ho
    nums=re.findall(r'A\.?1155|A\.?1156|428|BWM|Audit', q, re.I)
    filtered=[]
    if "1155" in q or "audit" in q.lower():
        filtered=[i for i,n in enumerate(names) if "1155" in n]
    elif "428" in q or "cyber" in q.lower():
        filtered=[i for i,n in enumerate(names) if "428" in n]
    if filtered:
        sub_t=[texts[i] for i in filtered]; sub_n=[names[i] for i in filtered]
        vec=TfidfVectorizer(stop_words='english'); mat=vec.fit_transform(sub_t+[q])
        sims=cosine_similarity(mat[-1], mat[:-1]).flatten(); top=np.argsort(sims)[-1:][::-1]
        return [(sub_n[i], sub_t[i]) for i in top]
    if texts:
        q_vec=vectorizer.transform([q]); sims=cosine_similarity(q_vec, matrix).flatten(); top=np.argsort(sims)[-k:][::-1]
        return [(names[i], texts[i]) for i in top]
    return []

c1,c2 = st.columns([0.85,0.15])
with c1:
    query = st.text_input("q", placeholder="What are requirements under Hong Kong Convention?", label_visibility="collapsed")
with c2:
    go = st.button("➤", use_container_width=True)

if query or go:
    if not query: query="What are requirements under Hong Kong Convention?"
    results = smart_search(query, k=1)
    if results:
        top_name, top_text = results[0]
        context = top_text[:8000]
        # PROMPT FIX - "no information" bolna band karo
        prompt = f"Answer the question using CONTEXT if possible, if context is about different IMO topic then answer from your own IMO knowledge but mention source file {top_name}. Do NOT say 'no information'. Context: {context}. Question: {query}"
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        st.markdown(f"<div class='answer-box'>{resp.text}</div>", unsafe_allow_html=True)
        
        info=docs.get(top_name)
        if info and os.path.exists(info["path"]):
            st.markdown(f"<div class='pdf-card'><b>📄 Source: {top_name} — Page 1-10</b><div class='pdf-preview'>{top_text[:1000]}</div></div>", unsafe_allow_html=True)
            with open(info["path"], "rb") as f:
                data=f.read()
                b64=base64.b64encode(data).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="background:#0B3D91; color:white; padding:12px; border-radius:12px; display:block; text-align:center; text-decoration:none; font-weight:700; margin:8px 12px">📄 OPEN FULL PDF IN NEW TAB</a>', unsafe_allow_html=True)
                # UNIQUE KEY FIX
                st.download_button(f"⬇️ DOWNLOAD {top_name}", data, file_name=top_name, mime="application/pdf", key=f"dl_{top_name}_{uuid.uuid4()}", use_container_width=True)

st.caption(f"Gemini 2.5 Flash | {len(docs)} PDFs loaded")
