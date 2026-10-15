import os
import time
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
        st.success("Key OK ✅")
    st.info("Data: master_imo_chunks.txt se auto load (30 files)")

def get_all_chunks():
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    if os.path.exists("master_imo_chunks.txt"):
        try:
            with open("master_imo_chunks.txt", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                if "---CHUNK---" in text:
                    chunks = text.split("---CHUNK---")
                else:
                    chunks = splitter.split_text(text)
                st.sidebar.success(f"Master Loaded: {len(chunks)} chunks (30 files)")
                return chunks
        except Exception as e:
            st.sidebar.warning(f"Master read error: {e}")
    return chunks

chunks = get_all_chunks()

if not chunks:
    st.warning("⚠️ master_imo_chunks.txt abhi ban raha hai. Action workflow complete hone do.")
    uploaded = st.file_uploader("Tab tak PDF upload karo", type="pdf", accept_multiple_files=True)
    if uploaded:
        chunks = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        for f in uploaded:
            reader = PdfReader(f)
            txt = "".join([p.extract_text() or "" for p in reader.pages])
            chunks.extend(splitter.split_text(txt))
        st.success(f"✅ {len(chunks)} chunks from upload")

if chunks:
    st.success(f"✅ {len(chunks)} chunks ready - 30 Files System LIVE!")
    query = st.text_input("Sawal pucho:", placeholder="Cybutryne limit? SRP? Hong Kong Convention entry?")

    if query:
        relevant = [c for c in chunks if any(w.lower() in c.lower() for w in query.split() if len(w)>2)][:4]
        if not relevant: relevant = chunks[:4]
        context = "\n\n".join(relevant)
        prompt = f"You are IMO expert. Use ONLY this context. Context: {context}\n\nQuestion: {query}\nAnswer in Hinglish with source like MEPC.405(83)."

        if not api_key:
            st.info("Sidebar me API Key daalo")
            for c in relevant:
                st.write(c[:600]); st.divider()
        else:
            done=False
            last_error=""
            for model_name in ["gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash-latest"]:
                try:
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    st.markdown("### 📝 Jawab:"); st.write(resp.text)
                    with st.expander("📄 Source chunks"):
                        for c in relevant: st.write(c[:600]+"...")
                    done=True; break
                except Exception as e:
                    last_error=str(e)
                    if "429" in last_error or "quota" in last_error.lower():
                        st.warning(f"⏳ Free limit 5 req/min. 20 sec wait... Model: {model_name}")
                        time.sleep(20)
                        try:
                            model = genai.GenerativeModel(model_name)
                            resp = model.generate_content(prompt)
                            st.markdown("### 📝 Jawab:"); st.write(resp.text)
                            done=True; break
                        except Exception as e2:
                            st.error(f"1 min baad try karo: {e2}"); done=True; break
                    if "404" in last_error: continue
                    else: st.error(last_error); done=True; break
