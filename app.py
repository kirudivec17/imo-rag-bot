import os
import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="IMO RAG Bot - HKC & ISPS", page_icon="🚢", layout="wide")
st.title("🚢 IMO RAG Bot - Hong Kong & ISPS Assistant")
st.caption("Ask in Hinglish/English - Answers from 17 Public IMO Resolutions | 5500+ chunks")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("GEMINI_API_KEY daalo (Private rahega)", type="password")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        genai.configure(api_key=api_key)

    st.markdown("---")
    st.markdown("### 📚 Data Status")
    st.info("Your `data/` folder is private due to.gitignore - 17 PDFs will not go to GitHub.")
    st.markdown("**Public Docs Used:**")
    st.markdown("- MEPC.196, 210, 211, 222, 223, 379, 405\n- HKSRC.2/Circ.1\n- ISPS, SOLAS XI-2, MSC.1/Circ.1191")

# --- Functions ---
def get_pdf_text(folder="data"):
    text = ""
    if not os.path.exists(folder):
        return ""
    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(os.path.join(folder, file))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            except:
                pass
    return text

def get_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_text(text)

# --- Main Logic ---
pdf_text = get_pdf_text()

if not pdf_text:
    st.warning("⚠️ `data/` folder me PDF nahi mila. Local me 17 PDFs daalo - GitHub pe nahi jayenge (.gitignore se safe).")
    uploaded = st.file_uploader("Ya yaha test ke liye 1-2 free Circular upload karo", type="pdf", accept_multiple_files=True)
    if uploaded:
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
        pdf_text = text

if pdf_text:
    chunks = get_chunks(pdf_text)
    st.success(f"✅ {len(chunks)} chunks ready - Data private hai, code public hai.")

    # ChromaDB Setup
    client = chromadb.Client()
    # Use Gemini embeddings if key available else default
    try:
        collection = client.get_or_create_collection("imo_bot")
        if collection.count() == 0:
            collection.add(documents=chunks, ids=[f"id_{i}" for i in range(len(chunks))])
    except Exception as e:
        st.error(f"DB Error: {e}")

    query = st.text_input("Sawal pucho (e.g., Cybutryne ka limit kya hai? / SRP me kya chahiye?)")
    if query:
        results = collection.query(query_texts=[query], n_results=3)
        context = "\n\n".join(results['documents'][0])

        prompt = f"Context from IMO public resolutions:\n{context}\n\nQuestion: {query}\nAnswer with source resolution name and be precise (IMO rules):"

        if api_key:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown("### 📝 Jawab:")
                st.write(response.text)
                st.markdown("### 📄 Source Chunks:")
                for doc in results['documents'][0]:
                    st.caption(doc[:400] + "...")
            except Exception as e:
                st.error(f"Gemini Error: {e}")
        else:
            st.info("API Key daalo sidebar me, phir jawab ayega. Source chunks upar se dekh lo.")
            st.write(results['documents'][0])

st.markdown("---")
st.caption("Legal: Uses only free public IMO Resolutions. BYOD model - Your data stays private via.gitignore")
