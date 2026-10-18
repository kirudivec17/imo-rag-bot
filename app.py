import streamlit as st
import os, json
import numpy as np
from google import genai
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

# Gemini 2.5 - New SDK google-genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GENERATION_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "text-embedding-005"

st.set_page_config(page_title="IMO AI ASISTANT", layout="wide", page_icon="⚓")

# CSS - Blue Header + Anchor Watermark (Official logo nahi)
st.markdown("""
<style>
.stApp { background-color: #f6f8fb; }
.imo-header {
    background: #0B3D91;
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: -1rem -1rem 1.5rem -1rem;
    position: relative;
    z-index: 10;
}
.imo-header-left { display: flex; align-items: center; gap: 12px; }
.imo-header-text { color: white; font-size: 11px; font-weight: 700; line-height: 13px; letter-spacing: 0.3px; }
.watermark {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0.05;
    pointer-events: none;
    z-index: 0;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 100 100'><text x='50%' y='50%' font-size='40' text-anchor='middle' dominant-baseline='middle'>⚓</text></svg>");
    background-repeat: repeat;
}
.block-container { position: relative; z-index: 1; }
.source-card {
    background: white;
    border-radius: 12px;
    padding: 14px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.preview-box {
    background: #f3f4f6;
    border-radius: 8px;
    padding: 10px;
    font-size: 12px;
    color: #374151;
    max-height: 120px;
    overflow-y: auto;
    margin: 8px 0;
}
</style>
<div class="watermark"></div>
""", unsafe_allow_html=True)

# Header - FIXED, No st.image width=0
st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <span style="font-size:28px; color:white;">◩</span>
        <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div style="color:white; font-size:18px;">🔍 &nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown("### IMO AI ASISTANT - Ask from 1125 IMO Docs")

# Load DB
@st.cache_resource
def load_db():
    if not os.path.exists("embeddings.npy") or not os.path.exists("metadata.json"):
        return None, None
    embs = np.load("embeddings.npy")
    with open("metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    return embs, meta

embeddings, metadata = load_db()

if embeddings is None:
    st.warning("Embeddings not found. First run ingest.py locally to generate embeddings.npy + metadata.json and push to GitHub.")
    st.stop()

query = st.text_input("Search IMO documents...", placeholder="e.g. What is MARPOL Annex VI sulfur limit?")

if query:
    with st.spinner("Searching 1125 IMO PDFs..."):
        # Embed query
        q_resp = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query
        )
        q_emb = np.array(q_resp.embeddings[0].values).reshape(1, -1)
        
        # Cosine similarity
        sims = cosine_similarity(q_emb, embeddings)[0]
        top_idx = np.argsort(sims)[-4:][::-1]  # top 4

        context_text = ""
        sources = []
        for idx in top_idx:
            m = metadata[idx]
            context_text += f"\nSource: {m['pdf_name']} - Page {m['page']}\nContent: {m['text']}\n"
            sources.append(m)

        # Gemini 2.5 Flash Answer
        prompt = f"""You are IMO AI ASISTANT. Answer ONLY from provided context.
        If answer not in context, say not found in IMO docs.
        
        Context:
        {context_text}
        
        Question: {query}
        
        Give answer with citations like: [Source: filename - Page X]
        """

        ans_resp = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt
        )
        answer = ans_resp.text

    st.markdown("#### Answer")
    st.success(answer)

    st.markdown("#### Sources")
    for src in sources:
        st.markdown(f"""
        <div class="source-card">
            <b>Source:</b> {src['pdf_name']} — Page {src['page']}<br>
            <div class="preview-box">{src['text'][:600]}...</div>
            <small>File: {src['pdf_name']} | Local Path: ./imo_pdfs/{src['pdf_name']}</small>
        </div>
        """, unsafe_allow_html=True)
        # For local open - on cloud you can't open C: drive, so show path
        if st.button(f"OPEN FULL LOCAL PDF - {src['pdf_name']} - Page {src['page']}", key=f"{src['pdf_name']}_{src['page']}"):
            st.info(f"Local PDF location: imo_pdfs/{src['pdf_name']} - Open at Page {src['page']} in your local viewer. On Streamlit Cloud, download PDFs from GitHub repo.")
