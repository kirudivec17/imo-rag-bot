import streamlit as st
import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Page config
st.set_page_config(page_title="IMO AI ASISTANT", layout="wide", page_icon="⚓")

# CSS - Blue header + Watermark (custom anchor pattern, not official IMO logo)
st.markdown("""
<style>
    .imo-header {
        background: #0B3D91;
        padding: 12px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        margin: -1rem -1rem 0 -1rem;
    }
    .imo-header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .imo-header-left img {
        height: 50px;
        filter: brightness(0) invert(1);
    }
    .imo-header-left-text {
        font-size: 12px;
        font-weight: bold;
        line-height: 14px;
    }
    .main-container {
        position: relative;
        background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='50%25' y='50%25' font-size='40' fill='%23e3eaf5' text-anchor='middle' dominant-baseline='middle' opacity='0.3'%3E⚓%3C/text%3E%3C/svg%3E");
        background-repeat: repeat;
    }
    .source-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .pdf-preview {
        background: #f2f2f2;
        padding: 15px;
        border-radius: 12px;
        font-family: monospace;
        font-size: 12px;
    }
    .open-pdf-btn {
        background: #0B3D91;
        color: white;
        padding: 14px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        width: 100%;
        border: none;
        cursor: pointer;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Header - IMO logo + INTERNATIONAL MARITIME ORGANIZATION
st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/IMO_logo.svg/120px-IMO_logo.svg.png">
        <div class="imo-header-left-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div>🔍 &nbsp;&nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align:center; color:#0B3D91; margin-top:20px;'>IMO AI ASISTANT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>Your trusted assistant for IMO regulations, guidelines, and maritime safety</p>", unsafe_allow_html=True)

# ChromaDB load
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="imo_hkc_12000")

query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
if st.button("➤", key="send"):
    st.session_state['q'] = query

if 'q' in st.session_state and st.session_state['q']:
    q = st.session_state['q']
    
    # Embed query
    q_emb = genai.embed_content(model="models/text-embedding-004", content=q, task_type="retrieval_query")['embedding']
    results = collection.query(query_embeddings=[q_emb], n_results=1)
    
    doc = results['documents'][0][0]
    meta = results['metadatas'][0][0]
    source_file = meta.get('source','MEPC.269(68).pdf')
    
    # Extract page - from your chunks
    page = "Page 15"  # you can parse from chunk metadata later
    pdf_name = source_file.split('/')[-1] if '/' in source_file else source_file
    
    # Answer via Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Based on this IMO doc: {doc}\n\nQuestion: {q}\nAnswer concisely with requirements."
    ans = model.generate_content(prompt).text
    
    # Answer bubble
    st.markdown(f"<div style='background:#d6e4ff; padding:16px; border-radius:20px; margin:20px 0;'>{ans}</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='display:flex; gap:10px; margin-bottom:10px;'>
        <span style='background:#d6e4ff; padding:6px 12px; border-radius:20px; font-size:12px;'>ISPS Code security levels</span>
        <span style='background:#d6e4ff; padding:6px 12px; border-radius:20px; font-size:12px;'>MARPOL Annex VI limits</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Source Card - Exact as your photo
    st.markdown(f"""
    <div class="source-card">
        <div style='display:flex; align-items:center; gap:8px; font-weight:bold;'>
            <span style='background:#0B3D91; color:white; padding:4px 8px; border-radius:4px; font-size:10px;'>PDF</span>
            Source: IMO Resolution {pdf_name} — {page}
        </div>
        <div style='font-size:12px; color:#555; margin:8px 0;'>Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
        <div class="pdf-preview">
            MEPC 68/21/Add.1 — ANNEX 7 — PAGE 15<br><br>
            8.3.1 The ship recycling plan shall be developed.<br><br>
            {doc[:300]}...
        </div>
        <button class="open-pdf-btn">📄 OPEN FULL LOCAL PDF</button>
        <div style='text-align:center; font-size:10px; color:#888; margin-top:5px;'>{pdf_name} • {page} of 22</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("OPEN FULL LOCAL PDF"):
        st.info(f"Opening local file: {pdf_name} - {page} - from ./imo-rag-bot/{pdf_name}")

# Sidebar stats
with st.sidebar:
    st.metric("Docs", "1125")
    st.metric("Chunks", "12002")
    st.write("Model: Gemini + ChromaDB")
