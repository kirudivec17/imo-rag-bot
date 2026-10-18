import streamlit as st
import os, json
import numpy as np
from google import genai
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GENERATION_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "text-embedding-005"

st.set_page_config(page_title="IMO AI ASISTANT", layout="wide", page_icon="⚓")

# CSS - Blue header + Anchor watermark (official logo nahi)
st.markdown("""
<style>
.imo-header { background:#0B3D91; padding:10px 20px; display:flex; justify-content:space-between; align-items:center; margin:-1rem -1rem 1rem -1rem; position:relative; z-index:10; }
.imo-header-left { display:flex; align-items:center; gap:10px; }
.imo-header-left img { height:48px; filter:brightness(0) invert(1); }
.imo-header-text { color:white; font-size:11px; font-weight:700; line-height:13px; }
.watermark { position:fixed; top:0; left:0; width:100%; height:100%; opacity:0.06; pointer-events:none; z-index:0; 
background-image:url("data:image/svg+xml,%3Csvg width='200' height='200' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='50%25' y='50%25' font-size='40' fill='%230B3D91' text-anchor='middle' dominant-baseline='middle'%3E⚓%3C/text%3E%3C/svg%3E"); }
.answer-bubble { background:#D6E6FF; border-radius:20px; padding:18px; margin:12px 0; }
.source-card { background:white; border-radius:12px; padding:14px; border:1px solid #e0e0e0; margin-top:16px; }
.pdf-preview { background:#F0F0F0; border-radius:8px; padding:12px; font-family:monospace; font-size:12px; }
</style>
<div class="watermark"></div>
""", unsafe_allow_html=True)

# Load DB
@st.cache_resource
def load_db():
    emb = np.load("embeddings.npy")
    with open("metadata.json","r",encoding="utf-8") as f:
        meta = json.load(f)
    return emb, meta

# Header
col1, col2 = st.columns([4,1])
with st.container():
    st.markdown(f"""
    <div class="imo-header">
        <div class="imo-header-left">
            <img src="https://i.imgur.com/placeholder.png" id="imo-logo">
            <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
        </div>
        <div style="color:white;">🔍 👤</div>
    </div>
    <script>
        document.getElementById('imo-logo').src = localStorage.getItem('imo_logo') || '';
    </script>
    """, unsafe_allow_html=True)
    # Actual logo - put your wa_image file in assets/
    st.image("assets/imo_logo.png", width=0)  # hidden, CSS will show

st.markdown("<h1 style='text-align:center; color:#0B3D91;'>IMO AI ASISTANT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Your trusted assistant for IMO regulations, guidelines, and maritime safety</p>", unsafe_allow_html=True)

query = st.text_input("Query", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")

if query:
    embeddings, metadata = load_db()
    
    # Embed query - Gemini 2.5
    q_emb = client.models.embed_content(model=EMBEDDING_MODEL, contents=query).embeddings[0].values
    q_emb = np.array(q_emb).reshape(1,-1)
    
    # Cosine similarity - scikit-learn
    sims = cosine_similarity(q_emb, embeddings)[0]
    top_idx = np.argsort(sims)[-4:][::-1]
    
    context = ""
    sources = []
    for idx in top_idx:
        m = metadata[idx]
        context += f"\nSource: {m['pdf_name']} Page {m['page']}: {m['text']}\n"
        sources.append(m)
    
    # Generate - Gemini 2.5 Flash
    prompt = f"""You are IMO AI ASISTANT. Answer only from context.
    Context: {context}
    Question: {query}
    Cite at end: Source: [PDF Name] — Page [Number]
    """
    response = client.models.generate_content(model=GENERATION_MODEL, contents=prompt)
    answer = response.text
    
    st.markdown(f"<div class='answer-bubble'>{answer}</div>", unsafe_allow_html=True)
    st.markdown("`ISPS Code security levels` `MARPOL Annex VI limits`")
    
    # Source Card - Page + PDF name show
    best = sources[0]
    st.markdown(f"""
    <div class="source-card">
        <b>📄 Source: IMO Resolution {best['pdf_name']} — Page {best['page']}</b><br>
        <small>Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</small>
        <div class="pdf-preview" style="margin-top:10px;">
            MEPC 68/21/Add.1 — ANNEX 7 — PAGE {best['page']}<br><br>
            8.3.1 The ship recycling plan shall be developed.<br>
            {best['text'][:300]}...
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pdf_path = os.path.join("imo_pdfs", best['pdf_name'])
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button("📄 OPEN FULL LOCAL PDF", f, file_name=best['pdf_name'], mime="application/pdf", use_container_width=True)
        st.caption(f"Kaunse PDF se aaya: {best['pdf_name']} | Page: {best['page']} | File: {pdf_path}")
