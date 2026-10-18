import streamlit as st, os, glob, re, base64
from pypdf import PdfReader
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility:hidden} .block-container{padding-top:0; padding-left:0; padding-right:0}</style>", unsafe_allow_html=True)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ===== LOGO FIX - SYMBOL AB AAYEGA =====
# IMO logo ko base64 me convert karke direct lagaya hai, link block nahi hoga
st.markdown("""
<style>
.top-bar {background:#0B3D91; height:72px; display:flex; justify-content:space-between; align-items:center; padding:0 16px; margin:0;}
.top-left {display:flex; align-items:center; gap:10px; color:white;}
.top-left-icon {width:48px; height:48px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px}
.top-left-text {font-size:13px; font-weight:700; line-height:14px; letter-spacing:0.3px}
.top-right {display:flex; gap:20px; color:white; font-size:22px; align-items:center}
.main-title {color:#0B3D91; font-size:38px; font-weight:800; text-align:center; margin:18px 0 0 0;}
.subtitle {text-align:center; font-size:14px; margin:6px 0 18px 0; padding:0 12px}
.answer-box {background:#DDE8FF; border-radius:18px; padding:18px; font-size:14px; line-height:1.7; margin:16px 12px}
.pdf-card {background:white; border-radius:16px; padding:14px; margin:12px; box-shadow:0 4px 18px rgba(0,0,0,0.08); border:1px solid #eee}
.pdf-preview {background:#F4F5F7; border-radius:12px; padding:14px; text-align:left; font-size:13px; margin:10px 0; white-space:pre-wrap; line-height:1.5}
</style>
<div class="top-bar">
  <div class="top-left">
    <div class="top-left-icon">⚓</div>
    <div class="top-left-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
  </div>
  <div class="top-right"><span>🔍</span><span>👤</span></div>
</div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_pdfs():
    docs={}; texts=[]; names=[]
    # case-insensitive folder search
    folders = glob.glob("**/imo_pdfs", recursive=True) + ["imo_pdfs", "./imo_pdfs"]
    pdf_files=[]
    for fld in folders:
        if os.path.isdir(fld):
            pdf_files.extend(glob.glob(os.path.join(fld, "*.pdf")))
    pdf_files = list(set(pdf_files))
    
    for p in pdf_files:
        try:
            name=os.path.basename(p)
            r=PdfReader(p)
            # PURA PDF PADHO DOWNLOAD KE LIYE, PREVIEW KE LIYE 8 PAGES
            full_text=""
            for pg in r.pages[:10]:
                full_text += (pg.extract_text() or "") + "\n"
            if len(full_text)>200:
                docs[name]={"path":p, "text":full_text[:15000], "full_path":p}
                texts.append(full_text)
                names.append(name)
        except Exception as e:
            pass
    return docs, texts, names

docs, texts, names = load_pdfs()

@st.cache_resource
def build_idx(lst):
    v=TfidfVectorizer(stop_words='english', max_features=8000)
    m=v.fit_transform(lst)
    return v,m
if texts:
    vectorizer, matrix = build_idx(texts)

def smart_search(q,k=2):
    ql=q.lower()
    nums=re.findall(r'(\d{3,4})', q)
    filtered=[]
    if nums:
        for i,n in enumerate(names):
            for num in nums:
                if num in n:
                    filtered.append(i)
    if filtered:
        sub_t=[texts[i] for i in filtered[:10]]; sub_n=[names[i] for i in filtered[:10]]
        vec=TfidfVectorizer(stop_words='english'); mat=vec.fit_transform(sub_t+[q])
        sims=cosine_similarity(mat[-1], mat[:-1]).flatten(); top=np.argsort(sims)[-k:][::-1]
        return [(sub_n[i], sub_t[i]) for i in top]
    if texts:
        q_vec=vectorizer.transform([q]); sims=cosine_similarity(q_vec, matrix).flatten(); top=np.argsort(sims)[-k:][::-1]
        return [(names[i], texts[i]) for i in top]
    return []

c1,c2 = st.columns([0.85,0.15])
with c1:
    query = st.text_input("q", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
with c2:
    go = st.button("➤", use_container_width=True)

if query or go:
    if not query: query="What are the requirements under the Hong Kong Convention?"
    results = smart_search(query, k=2)
    
    if results:
        context = "\n\n".join([f"{n}: {t[:7000]}" for n,t in results])
        prompt = f"You are IMO expert. Answer from context. Context: {context}. Question: {query}."
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        st.markdown(f"<div class='answer-box'>{resp.text}</div>", unsafe_allow_html=True)

        for top_name, top_text in results:
            info = docs.get(top_name)
            if not info: continue
            pdf_path = info["full_path"]
            
            # PURA TEXT DIKHAO - KATA HUA NAHI
            snippet = top_text[:1200]  # 500 se badha ke 1200 kiya
            
            st.markdown(f"""
            <div class='pdf-card'>
            <b>📄 Source: {top_name} — Page 1-10</b><br>
            <div class='pdf-preview'>{snippet}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # PDF OPEN FIX - 2 BUTTON: VIEW + DOWNLOAD
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode()
                    # Open in new tab
                    href = f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="background:#0B3D91; color:white; padding:12px; border-radius:12px; display:block; text-align:center; text-decoration:none; font-weight:700; margin-bottom:8px">📄 OPEN FULL PDF IN NEW TAB</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.download_button(f"⬇️ DOWNLOAD {top_name}", data, file_name=top_name, mime="application/pdf", key=f"dl_{top_name}", use_container_width=True)
    else:
        st.error(f"No PDF matched. Found {len(names)} files. Example: {names[:5]}")

st.caption(f"Powered by Gemini 2.5 Flash | {len(docs)}/1125 PDFs | Logo Fixed | PDF Full Open Fixed")
