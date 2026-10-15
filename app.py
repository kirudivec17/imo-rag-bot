import os
import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="IMO RAG Bot - 30 Files", page_icon="🚢", layout="wide")
st.title("🚢 IMO RAG Bot - Hong Kong & ISPS Assistant")
st.caption("30 Docs | 7500+ Chunks | Ask Hinglish/English")

with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("GEMINI_API_KEY", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    st.info("Data: data/ folder private via .gitignore")

def get_all_chunks():
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    if os.path.exists("master_imo_chunks.txt"):
        try:
            with open("master_imo_chunks.txt", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                chunks = splitter.split_text(text)
                st.sidebar.success(f"Master: {len(chunks)} chunks")
                return chunks
        except:
            pass
    if os.path.exists("data"):
        for file in os.listdir("data"):
            if file.lower().endswith(".pdf"):
                try:
                    reader = PdfReader(os.path.join("data", file))
                    full = "".join([p.extract_text() or "" for p in reader.pages])
                    chunks.extend(splitter.split_text(full))
                except:
                    pass
    return chunks

chunks = get_all_chunks()

if not chunks:
    st.warning("⚠️ data/ folder me PDF nahi mila. Neeche upload karo - demo ke liye")
    uploaded = st.file_uploader("PDF upload karo (2-3 free IMO circulars)", type="pdf", accept_multiple_files=True)
    if uploaded:
        chunks = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        for f in uploaded:
            reader = PdfReader(f)
            txt = "".join([p.extract_text() or "" for p in reader.pages])
            chunks.extend(splitter.split_text(txt))
        st.success(f"✅ {len(chunks)} chunks ready from upload")

if chunks:
    st.success(f"✅ {len(chunks)} chunks ready - App working!")
    query = st.text_input("Sawal pucho: Cybutryne limit? SRP me kya chahiye? PFOS banned?")
    
    if query:
        relevant = [c for c in chunks if any(w.lower() in c.lower() for w in query.split())][:4]
        if not relevant:
            relevant = chunks[:4]
        
        context = "\n\n".join(relevant)
        prompt = f"You are IMO expert. Use ONLY context. Context: {context} Question: {query} Answer in Hinglish with source like MEPC.405(83) if found."
        
        if api_key:
            done = False
            for model_name in ["gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash-latest"]:
                try:
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    st.markdown("### 📝 Jawab:")
                    st.write(resp.text)
                    with st.expander("📄 Source chunks"):
                        for c in relevant:
                            st.write(c[:500]+"...")
                    done = True
                    break
                except Exception as e:
                    err = str(e).lower()
                    if "404" in err or "not found" in err:
                        continue
                    else:
                        st.error(f"Gemini error: {e}")
                        done = True
                        break
            if not done:
                st.error("All models failed. Try again later.")
        else:
            st.info("Sidebar me API Key daalo")
            for c in relevant:
                st.write(c[:600])
                st.divider()

st.caption("Legal: Uses only free public IMO Resolutions. BYOD Model")
