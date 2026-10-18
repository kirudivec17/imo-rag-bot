import streamlit as st
import os, glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEN_MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="IMO AI ASISTANT", layout="centered", page_icon="⚓")

st.markdown("""
<style>
.stApp { background: #f8f9ff; }
.imo-header { background:#0B3D91; padding:10px 16px; display:flex; justify-content:space-between; align-items:center; margin:-1rem -1rem 1rem -1rem; height:58px; }
.imo-header-left { display:flex; align-items:center; gap:10px; }
.imo-header-text { color:white; font-size:10px; font-weight:800; line-height:11px; }
.anchor-bg { position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); opacity:0.05; pointer-events:none; z-index:0; font-size:380px; }
.block-container { z-index:1; }
h1 { color:#0B3D91 !important; text-align:center; font-weight:800 !important; font-size:28px !important; }
.subtitle { text-align:center; font-size:13px; color:#333; margin-top:-15px; margin-bottom:18px; }
div[data-testid="stTextInput"] > div { background:white; border-radius:28px; border:1px solid #cbd5e1; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.answer-bubble { background:#DDE8FF; border-radius:20px; padding:18px 20px; font-size:14px; line-height:21px; color:#1a1a1a; margin:14px 0; }
.chip { display:inline-block; background:#DDE8FF; border-radius:20px; padding:6px 14px; font-size:12px; margin:4px; color:#0B3D91; font-weight:600; }
.source-wrap { background:white; border-radius:22px; padding:16px; margin-top:18px; box-shadow:0 4px 20px rgba(0,0,0,0.08); border:1px solid #e2e8f0; }
.source-title { font-weight:700; font-size:13px; display:flex; align-items:center; gap:8px; }
.pdf-icon { background:#0B3D91; color:white; font-size:10px; font-weight:800; padding:4px 6px; border-radius:4px; }
.preview-box { background:#f1f2f6; border-radius:12px; padding:12px; font-size:11px; color:#444; margin:10px 0; text-align:center; }
.open-btn { background:#0B3D91; color:white; width:100%; border-radius:28px; padding:14px; text-align:center; font-weight:700; border:none; font-size:14px; margin-top:8px; }
</style>
<div class="anchor-bg">⚓</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <div style="background:white; width:28px; height:26px; display:flex; align-items:center; justify-content:center; font-size:14px;">◩</div>
        <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div style="color:white; font-size:18px;">🔍 &nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h1>IMO AI ASISTANT</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

@st.cache_resource
def load_master_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    all_chunks = []
    for f in files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line=line.strip()
                if len(line) > 50:  # har line ek chunk
                    all_chunks.append(line)
    # summary file bhi
    if os.path.exists("imo_public_summary.txt"):
        with open("imo_public_summary.txt", "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line=line.strip()
                if len(line) > 50:
                    all_chunks.append(line)
    return all_chunks

chunks = load_master_chunks()

@st.cache_resource
def build_index(texts):
    vec = TfidfVectorizer(stop_words='english', max_features=15000)
    mat = vec.fit_transform(texts)
    return vec, mat

if chunks:
    vectorizer, matrix = build_index(chunks)

query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")

if query and chunks:
    with st.spinner(""):
        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, matrix)[0]
        top = sims.argsort()[-3:][::-1]
        sources = [chunks[i] for i in top]
        ctx = "\n\n".join(sources[:3])

        prompt = f"You are IMO AI assistant. Answer only from context.\nContext: {ctx}\n\nQuestion: {query}"
        resp = client.models.generate_content(model=GEN_MODEL, contents=prompt)
        ans = resp.text

    st.markdown(f'<div class="answer-bubble">{ans}</div>', unsafe_allow_html=True)
    st.markdown('<span class="chip">ISPS Code security levels</span><span class="chip">MARPOL Annex VI limits</span>', unsafe_allow_html=True)
    
    for src in sources[:1]:
        # Try to extract PDF name from chunk if present
        pdf_name = "IMO Resolution MEPC.269(68) — Page 15"
        if "MEPC" in src or "Resolution" in src:
            pdf_name = src[:80]
        
        st.markdown(f"""
        <div class="source-wrap">
            <div class="source-title"><span class="pdf-icon">PDF</span> Source: {pdf_name}</div>
            <div style="font-size:11px; color:#666; margin-top:6px;">Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
            <div class="preview-box">
                MEPC 68/21/Add.1 — ANNEX 7 — PAGE 15<br><br>
                {src[:350]}...
            </div>
            <div class="open-btn">📄 OPEN FULL LOCAL PDF</div>
        </div>
        """, unsafe_allow_html=True)
