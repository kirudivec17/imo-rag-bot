import streamlit as st
import requests
import urllib.parse

# CONFIG
st.set_page_config(page_title="IMO RAG Bot", page_icon="🚢", layout="wide")
API_URL = "http://129.225.105.196:8001"

st.title("🚢 IMO RAG Bot - Official IMO Docs")
st.caption(f"Backend: {API_URL} | 2000+ PDFs | 24k+ Chunks | Gemini 2.5 Flash")

# HEALTH CHECK
try:
    h = requests.get(f"{API_URL}/health", timeout=5).json()
    st.success(f"✅ Backend LIVE - Chunks: {h.get('chunks',0)} | Status: {h.get('status')}")
except:
    st.error("❌ Backend DOWN - Check VM")

# QUERY INPUT
query = st.text_input("🔍 IMO se pucho:", placeholder="Ex: Hong Kong Convention requirements, Ballast Water D-2, EEXI...")
search_btn = st.button("Ask IMO Bot")

if search_btn and query:
    with st.spinner("📚 2000+ PDFs me search + Gemini 2.5 Flash polish... 10-15 sec..."):
        try:
            # No proxy needed for Streamlit Cloud
            resp = requests.post(
                f"{API_URL}/ask",
                json={"query": query},
                timeout=60
            )
            data = resp.json()
            
            # ANSWER
            st.subheader("✅ Answer (Gemini 2.5 Flash Polished)")
            st.write(data.get("answer", "No answer"))

            # SOURCES
            sources = data.get("sources", [])
            if sources:
                st.subheader(f"📄 Sources ({len(sources)} found)")
                for i, s in enumerate(sources, 1):
                    src_file = s.get("source", "Unknown.pdf")
                    # Safe filename for URL - yahi fix hai PDF bug ka!
                    safe_name = urllib.parse.quote(src_file.split("/")[-1].strip())
                    pdf_url = f"{API_URL}/pdf/{safe_name}"
                    
                    col1, col2 = st.columns([4,1])
                    with col1:
                        st.markdown(f"**{i}. {src_file}**")
                        st.caption(s.get("text","")[:300] + "...")
                    with col2:
                        st.link_button(f"📄 OPEN FULL PDF", pdf_url)
                    st.divider()
            else:
                st.warning("No sources found")

        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Backend ko 10 sec wait karke fir try karo - TF-IDF load ho raha hoga")

# SIDEBAR
with st.sidebar:
    st.header("How to Use")
    st.write("1. Query likho\n2. Ask pe click karo\n3. Source ke OPEN PDF se original IMO doc kholo")
    st.header("Test Queries")
    st.code("Hong Kong Convention\nBallast Water Management D-2\nEEXI requirements\nMARPOL Annex VI")
    
    if st.button("Check Total PDFs"):
        try:
            r = requests.get(f"{API_URL}/list-pdfs", timeout=10).json()
            st.metric("Total PDFs", r.get("count",0))
            st.write(r.get("pdfs",[])[:10])
        except Exception as e:
            st.write(f"Error: {e}")
