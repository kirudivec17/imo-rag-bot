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
    api_key = st.text_input("GEMINI_API_KEY", type="password", help="aistudio.google.com se lo")
    if api_key:
        genai.configure(api_key=api_key)
        st.success("Key lag gayi ✅")
    st.info("Data: data/ folder private via .gitignore")
    st.markdown("---")
    st.caption("Tip: 429 aaye to 20 sec wait karo, free limit 5 req/min hai")

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
        except Exception as e:
            st.sidebar.warning(f"Master read error: {e}")
    if os.path.exists("data"):
        for file in os.listdir("data"):
            if file.lower().endswith(".pdf"):
                try:
                    reader = PdfReader(os.path.join("data", file))
                    full = "".join([p.extract_text() or "" for p in reader.pages])
                    if full.strip():
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
            try:
                reader = PdfReader(f)
                txt = "".join([p.extract_text() or "" for p in reader.pages])
                if txt.strip():
                    chunks.extend(splitter.split_text(txt))
            except Exception as e:
                st.error(f"{f.name} read fail: {e}")
        if chunks:
            st.success(f"✅ {len(chunks)} chunks ready from upload")

if chunks:
    st.success(f"✅ {len(chunks)} chunks ready - App working!")
    query = st.text_input("Sawal pucho:", placeholder="Cybutryne limit? SRP me kya chahiye? PFOS banned? imo full form")

    if query:
        relevant = [c for c in chunks if any(w.lower() in c.lower() for w in query.split() if len(w) > 2)][:4]
        if not relevant:
            relevant = chunks[:4]
        
        context = "\n\n".join(relevant)
        prompt = f"You are IMO expert. Use ONLY this context. If not found, say not found. Context: {context}\n\nQuestion: {query}\nAnswer in Hinglish with source like MEPC.405(83) if found."

        if not api_key:
            st.info("Sidebar me GEMINI API Key daalo, fir jawab ayega")
            for c in relevant:
                st.write(c[:600])
                st.divider()
        else:
            done = False
            last_error = ""
            for model_name in ["gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash-latest"]:
                try:
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    st.markdown("### 📝 Jawab:")
                    st.write(resp.text)
                    with st.expander("📄 Source chunks"):
                        for c in relevant:
                            st.write(c[:500]+"...")
                            st.divider()
                    done = True
                    break

                except Exception as e:
                    last_error = str(e)
                    err_low = last_error.lower()
                    
                    if "429" in last_error or "quota" in err_low or "exceeded" in err_low:
                        st.warning(f"⏳ Google free limit (5 req/min). Model: {model_name}. 20 sec me auto retry kar raha hu...")
                        time.sleep(20)
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
                        except Exception as e2:
                            st.error(f"Abhi bhi limit me hai. 1 min baad try karo. Error: {e2}")
                            done = True
                            break

                    if "404" in last_error or "not found" in err_low:
                        st.caption(f"{model_name} not found, next try...")
                        continue
                    else:
                        st.error(f"Gemini error: {last_error}")
                        done = True
                        break
            
            if not done:
                st.error(f"All models failed. Last: {last_error}. 1 min baad try karo ya naya API key banao aistudio.google.com pe")

st.caption("Legal: Uses only free public IMO Resolutions. BYOD Model | 30 Docs")
