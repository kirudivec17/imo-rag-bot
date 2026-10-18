import streamlit as st
import os, glob, json
import numpy as np
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEN_MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="IMO AI ASISTANT", layout="centered", page_icon="⚓")

# DESIGN - Photo jaisa
st.markdown("""
<style>
.stApp { background-color: #f6f8fb; }
.imo-header {
    background: #0B3D91;
    padding: 14px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: -1rem -1rem 2rem -1rem;
}
.imo-header-left { display: flex; align-items: center; gap: 10px; }
.imo-header-text { color: white; font-size: 11px; font-weight: 700; line-height: 12px; letter-spacing: 0.2px; }
.anchor-bg {
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    font-size: 400px;
    opacity: 0.04;
    pointer-events: none;
    z-index: 0;
}
.block-container { z-index: 1; position: relative; }
div[data-testid="stTextInput"] input {
    background: white;
    border-radius: 12px;
    border: 1px solid #d1d5db;
    padding: 12px;
}
.answer-box {
    background: white;
    border-radius: 12px;
    padding: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.source-card {
    background: white;
    border-radius: 12px;
    padding: 14px;
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}
.preview {
    background: #f3f4f6;
    border-radius: 8px;
    padding: 10px;
    font-size: 12.5px;
    color: #374151;
    margin: 8px 0;
    max-height: 110px;
    overflow-y: auto;
}
</style>
<div class="anchor-bg">⚓</div>
""", unsafe_allow_html=True)

# Header - photo jaisa
st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <div style="background:white; width:26px; height:26px; display:flex; align-items:center; justify-content:center; font-size:12px;">◩</div>
        <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div style="color:white; font-size:18px;">🔍 &nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown("### IMO AI ASISTANT")
query = st.text_input("", placeholder="Search IMO documents...", label_visibility="collapsed")

PDF_FOLDER = "./imo_pdfs"
pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))

@st.cache_data
def get_chunks():
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=180)
    data = []
    for pdf_path in pdf_files:
        try:
            reader = PdfReader(pdf_path)
            fname = os.path.basename(pdf_path)
            for p_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if not text or len(text.strip()) < 80:
                    continue
                for ch in splitter.split_text(text):
                    data.append({"text": ch, "pdf_name": fname, "page": p_num, "path": pdf_path})
        except:
            continue
    return data

if not pdf_files:
    st.info("imo_pdfs folder khali hai. GitHub me PDFs add karo.")
    st.stop()

chunks = get_chunks()

@st.cache_resource
def build_index(texts):
    vec = TfidfVectorizer(stop_words='english', max_features=8000)
    mat = vec.fit_transform(texts)
    return vec, mat

if chunks:
    texts = [c["text"] for c in chunks]
    vectorizer, matrix = build_index(texts)

if query and chunks:
    with st.spinner("Searching..."):
        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, matrix)[0]
        top = sims.argsort()[-4:][::-1]
        sources = [chunks[i] for i in top]

        ctx = ""
        for s in sources:
            ctx += f"\n[{s['pdf_name']} Page {s['page']}] {s['text']}\n"

        prompt = f"You are IMO AI ASISTANT. Answer only from context. Cite page.\nContext:{ctx}\n\nQuestion:{query}\nAnswer with [Source: filename - Page X]"
        resp = client.models.generate_content(model=GEN_MODEL, contents=prompt)
        ans = resp.text

    st.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
    
    st.markdown("#### Sources")
    for src in sources:
        st.markdown(f"""
        <div class="source-card">
            <b>Source:</b> {src['pdf_name']} — Page {src['page']}
            <div class="preview">{src['text'][:650]}...</div>
        </div>
        """, unsafe_allow_html=True)
        st.button(f"OPEN FULL LOCAL PDF  -  {src['pdf_name']} Page {src['page']}", key=f"{src['pdf_name']}_{src['page']}_{src['text'][:10]}")
