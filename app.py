import streamlit as st
import os
import glob
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GENERATION_MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="IMO AI ASISTANT", layout="wide", page_icon="⚓")

# CSS - Same design as your photo
st.markdown("""
<style>
.stApp { background-color: #f6f8fb; }
.imo-header { background:#0B3D91; padding:12px 20px; display:flex; justify-content:space-between; align-items:center; margin:-1rem -1rem 1.5rem -1rem; }
.imo-header-left { display:flex; align-items:center; gap:12px; }
.imo-header-text { color:white; font-size:11px; font-weight:700; line-height:13px; }
.watermark { position:fixed; top:0; left:0; width:100%; height:100%; opacity:0.05; pointer-events:none; z-index:0; background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><text x='50%' y='50%' font-size='70' text-anchor='middle' dominant-baseline='middle'>⚓</text></svg>"); background-repeat:repeat; }
.block-container { position:relative; z-index:1; }
.source-card { background:white; border-radius:12px; padding:14px; border:1px solid #e5e7eb; box-shadow:0 1px 3px rgba(0,0,0,0.06); margin-bottom:10px; }
.preview-box { background:#f3f4f6; border-radius:8px; padding:10px; font-size:12px; color:#374151; max-height:120px; overflow-y:auto; margin:8px 0; }
</style>
<div class="watermark"></div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <span style="font-size:26px; color:white;">◩</span>
        <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div style="color:white;">🔍 &nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown("### IMO AI ASISTANT - Ask from 1125 IMO Docs")

PDF_FOLDER = "./imo_pdfs"

# Check PDFs
pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
if not pdf_files:
    st.error(f"PDFs nahi mile! GitHub repo me `{PDF_FOLDER}` folder banao aur usme IMO ke PDFs daalo. Abhi 0 PDFs hai.")
    st.info("Mobile se GitHub app me: Repo -> Add file -> Upload files -> imo_pdfs folder me PDFs daalo.")
    st.stop()

st.caption(f"Found {len(pdf_files)} PDFs")

@st.cache_data(show_spinner=False)
def load_and_split_pdfs():
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_chunks = []
    for pdf_path in pdf_files[:200]:  # Mobile ke liye pehle 200 PDFs se start karo, baad me 1125 kar dena
        try:
            reader = PdfReader(pdf_path)
            fname = os.path.basename(pdf_path)
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if not text or len(text.strip()) < 100:
                    continue
                chunks = splitter.split_text(text)
                for ch in chunks:
                    all_chunks.append({
                        "text": ch,
                        "pdf_name": fname,
                        "page": page_num,
                        "path": pdf_path
                    })
        except Exception as e:
            continue
    return all_chunks

with st.spinner("Loading IMO docs (first time thoda time lagega)..."):
    chunks_data = load_and_split_pdfs()

if not chunks_data:
    st.error("PDFs read nahi ho rahe. PDFs corrupt ho sakte hain.")
    st.stop()

# Build TF-IDF
@st.cache_resource
def build_tfidf(texts):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    return vectorizer, tfidf_matrix

all_texts = [c["text"] for c in chunks_data]
vectorizer, tfidf_matrix = build_tfidf(all_texts)

query = st.text_input("Search IMO documents...", placeholder="e.g. What is MARPOL Annex VI sulfur limit?")

if query:
    with st.spinner("Searching..."):
        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, tfidf_matrix)[0]
        top_idx = sims.argsort()[-4:][::-1]
        
        sources = [chunks_data[i] for i in top_idx]
        context = ""
        for s in sources:
            context += f"\nSource: {s['pdf_name']} - Page {s['page']}\nContent: {s['text']}\n"

        prompt = f"""You are IMO AI ASISTANT. Use ONLY this context from IMO docs.
        Context: {context}
        Question: {query}
        Answer concisely and cite as [Source: filename - Page X]
        If not in context, say: Not found in IMO docs.
        """

        resp = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt
        )
        answer = resp.text

    st.markdown("#### Answer")
    st.success(answer)

    st.markdown("#### Sources with Page")
    for src in sources:
        st.markdown(f"""
        <div class="source-card">
            <b>Source:</b> {src['pdf_name']} — Page {src['page']}<br>
            <div class="preview-box">{src['text'][:700]}</div>
            <small>OPEN: {src['path']} at Page {src['page']}</small>
        </div>
        """, unsafe_allow_html=True)
