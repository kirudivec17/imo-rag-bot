import streamlit as st
import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Config
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "imo_docs"

# Gemini 2.5 - Final Locked
GENERATION_MODEL = "models/gemini-2.5-flash"
EMBEDDING_MODEL = "models/text-embedding-005"

st.set_page_config(page_title="IMO AI ASISTANT", layout="wide", page_icon="⚓")

# CSS - Blue header + Custom Anchor Watermark (NOT official logo)
st.markdown("""
<style>
    .stApp { background-color: #f5f7fa; }
    .imo-header {
        background: #0B3D91;
        padding: 10px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: -1rem -1rem 1rem -1rem;
    }
    .imo-header-left { display: flex; align-items: center; gap: 10px; }
    .imo-header-left img { height: 48px; filter: brightness(0) invert(1); }
    .imo-header-text { color: white; font-size: 11px; font-weight: 700; line-height: 13px; }
    .watermark {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        opacity: 0.06;
        pointer-events: none;
        z-index: 0;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Ctext x='50%25' y='50%25' font-size='40' fill='%230B3D91' opacity='0.5'%3E⚓%3C/text%3E%3C/svg%3E");
        background-repeat: repeat;
    }
    .main-title { color: #0B3D91; font-size: 42px; font-weight: 800; text-align: center; margin-top: 10px; }
    .subtitle { text-align: center; color: #555; font-size: 14px; }
    .answer-box { background: #D6E8FF; padding: 18px; border-radius: 20px; margin: 15px 0; }
    .pill { background: #D6E8FF; padding: 6px 14px; border-radius: 20px; display: inline-block; margin: 4px; font-size: 13px; }
    .source-card { background: white; border-radius: 20px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-top: 20px; }
</style>
<div class="watermark"></div>
""", unsafe_allow_html=True)

# Header - Tumhari photo jaisa
st.markdown(f"""
<div class="imo-header">
    <div class="imo-header-left">
        <img src="https://upload.wikimedia.org/wikipedia/commons/5/5f/IMO_logo.svg">
        <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div style="color:white; font-size:22px;">🔍 &nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">IMO AI ASISTANT</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

# Chroma
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(COLLECTION_NAME)

query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")

if query:
    # Embedding with 005 - Gemini 2.5
    q_emb = genai.embed_content(model=EMBEDDING_MODEL, content=query, task_type="retrieval_query")["embedding"]
    
    results = collection.query(query_embeddings=[q_emb], n_results=3)
    
    # Context build
    context = ""
    sources = []
    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        context += f"\n{doc}\n"
        sources.append(meta)  # meta has: file_name, page_number, full_path

    # Answer with Gemini 2.5 Flash
    gen_model = genai.GenerativeModel(GENERATION_MODEL)
    prompt = f"""
    You are IMO AI ASISTANT. Answer only from context.
    Context: {context}
    Question: {query}
    Provide concise answer and mention source file and page.
    """
    ans = gen_model.generate_content(prompt).text

    st.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
    st.markdown('<span class="pill">ISPS Code security levels</span> <span class="pill">MARPOL Annex VI limits</span>', unsafe_allow_html=True)

    # Source Card - Page + PDF Name + Which PDF
    for meta in sources:
        file_name = meta.get("file_name", "Unknown.pdf")
        page_no = meta.get("page_number", "?")
        full_path = meta.get("full_path", "")
        preview_text = results["documents"][0][0][:400]

        st.markdown(f"""
        <div class="source-card">
            <div style="display:flex; gap:10px; align-items:center;">
                <div style="background:#0B3D91; color:white; padding:6px 10px; border-radius:6px; font-size:12px;">PDF</div>
                <b>Source: IMO Resolution {file_name} — Page {page_no}</b>
            </div>
            <div style="font-size:12px; color:#555; margin-top:6px;">Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
            <div style="background:#f0f0f0; padding:12px; border-radius:10px; margin-top:10px; font-size:12px;">
                MEPC 68/21/Add.1 — ANNEX 7 — PAGE {page_no}<br><br>
                {preview_text}...
            </div>
        </div>
        """, unsafe_allow_html=True)

        # OPEN FULL LOCAL PDF - Button
        if st.button(f"📄 OPEN FULL LOCAL PDF - {file_name} Page {page_no}", key=f"{file_name}_{page_no}"):
            st.info(f"Opening local file: {full_path} at Page {page_no}")
            # For Streamlit Cloud, show file path; for local, use webbrowser
            st.markdown(f"[Download PDF]({full_path})")
