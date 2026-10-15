import os
import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="IMO RAG Bot - 30 Files", page_icon="🚢", layout="wide")
st.title("🚢 IMO RAG Bot - 30 Files | HKC & ISPS")
st.caption("17 se 30 files upgrade | 7500+ chunks | SOLAS XI-2 / ISPS | Ask Hinglish/English")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("GEMINI_API_KEY daalo (Private)", type="password")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        genai.configure(api_key=api_key)
    st.markdown("---")
    st.info("📚 Data Status: `data/` private hai.gitignore se - 30 PDFs GitHub pe nahi jayenge")
    st.markdown("**30 Docs:** MEPC.196, 210, 211, 222, 223, 269, 335, 338, 379, 405, 392, 396, HKSRC.2/Circ.1, TM11, SOLAS XI-2, ISPS, MSC.1/Circ.1191, A.1118, A.741, etc")

def get_chunks_with_source(folder="data"):
    chunks_with_meta = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    if not os.path.exists(folder):
        return []
    for file in os.listdir(folder):
        if file.lower().endswith(".pdf"):
            try:
                reader = PdfReader(os.path.join(folder, file))
                full_text = ""
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        full_text += txt + "\n"
                splits = splitter.split_text(full_text)
                for s in splits:
                    chunks_with_meta.append({"text": s, "source": file})
            except Exception as e:
                st.warning(f"{file} error: {e}")
    return chunks_with_meta

# Check if master exists
if os.path.exists("master_imo_chunks.txt"):
    st.success("✅ master_imo_chunks.txt mila - 30 files ka master ready!")
    with open("master_imo_chunks.txt", encoding="utf-8", errors="ignore") as f:
        master_text = f.read()
    raw_chunks = master_text.split("---")
    chunks_data = []
    for rc in raw_chunks:
        if len(rc.strip()) > 100:
            source = "master"
            if "[Source:" in rc:
                try:
                    source = rc.split("[Source:")[1].split("|")[0].strip()
                except:
                    pass
            chunks_data.append({"text": rc, "source": source})
else:
    chunks_data = get_chunks_with_source("data")
    if not chunks_data:
        st.warning("⚠️ `data/` me PDF nahi. Local me 30 PDFs daalo - GitHub pe nahi jayenge.")
        uploaded = st.file_uploader("Test ke liye 1-2 free Circular upload karo", type="pdf", accept_multiple_files=True)
        if uploaded:
            chunks_data=[]
            for f in uploaded:
                reader=PdfReader(f)
                txt="".join([p.extract_text() or "" for p in reader.pages])
                splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                for s in splitter.split_text(txt):
                    chunks_data.append({"text":s,"source":f.name})

if chunks_data:
    st.success(f"✅ {len(chunks_data)} chunks ready - Data private, code public")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("imo_bot_30")
    if collection.count() < len(chunks_data):
        try:
            client.delete_collection("imo_bot_30")
            collection = client.get_or_create_collection("imo_bot_30")
        except:
            pass
        docs = [c["text"] for c in chunks_data]
        metas = [{"source": c["source"]} for c in chunks_data]
        ids = [f"id_{i}" for i in range(len(docs))]
        collection.add(documents=docs, metadatas=metas, ids=ids)
        st.toast(f"DB built: {len(docs)} embeddings")

    query = st.text_input("Sawal pucho: Cybutryne limit kya hai? PFOS banned? SRP me kya chahiye?")
    if query:
        results = collection.query(query_texts=[query], n_results=4)
        context = "\n\n".join(results['documents'][0])
        sources = results['metadatas'][0]
        prompt = f"""You are IMO expert. Use ONLY context from public IMO resolutions.
Context:
{context}

Question: {query}
Answer in Hinglish/English mix, precise, with source resolution name like MEPC.379(80) or MEPC.405(83) or SOLAS XI-2/9, ISPS Code Part A. If not found, say not found in 30 files.
"""
        if api_key:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown("### 📝 Jawab:")
                st.write(response.text)
                st.markdown("### 📄 Sources:")
                for doc, meta in zip(results['documents'][0], sources):
                    st.caption(f"Source: {meta['source']} | {doc[:350]}...")
            except Exception as e:
                st.error(f"Gemini Error: {e}")
        else:
            st.info("API Key sidebar me daalo. Source chunks:")
            for doc, meta in zip(results['documents'][0], sources):
                st.markdown(f"**{meta['source']}**")
                st.write(doc[:600])

st.markdown("---")
st.caption("Legal: Uses only free public IMO Resolutions. 30 files | BYOD - Your data private via.gitignore | Built ChromaDB+Gemini+LangChain")
