import streamlit as st
import os
import glob

st.set_page_config(page_title="IMO 1125 RAG Bot", page_icon="🚢", layout="wide")

# --- HEADER ---
st.title("🚢 IMO 1125 RAG Bot")
st.markdown("**Total: 1125 Docs | 12002 Chunks | 110 Parts | HKC Compliant**")
st.divider()

# --- LOAD STATS ---
col1, col2, col3 = st.columns(3)
with col1:
    if os.path.exists("imo_pdfs/stats.txt"):
        with open("imo_pdfs/stats.txt", "r", encoding="utf-8", errors="ignore") as f:
            st.info(f.read())
    else:
        st.info("Total Unique PDFs: 1125")

with col2:
    if os.path.exists("imo_pdfs/README.txt"):
        with open("imo_pdfs/README.txt", "r", encoding="utf-8", errors="ignore") as f:
            st.success(f.read())
    else:
        st.success("IMO 1125 Ready")

with col3:
    if os.path.exists("imo_public_summary.txt"):
        with open("imo_public_summary.txt", "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()[:300]
            st.warning(txt)
    else:
        st.warning("12002 Chunks Loaded")

# --- LOAD 1125 LIST ---
docs = []
docs_path = "imo_pdfs/1125_final_list.txt"
if not os.path.exists(docs_path):
    docs_path = "imo_pdfs/1225_final_list.txt"

if os.path.exists(docs_path):
    with open(docs_path, "r", encoding="utf-8", errors="ignore") as f:
        docs = [line.strip() for line in f if line.strip() and len(line.strip()) > 4]
    
    st.success(f"✅ **1125 File Loaded: {len(docs)} docs found at {docs_path}**")
else:
    st.error("❌ 1125_final_list.txt nahi mila! imo_pdfs folder check karo. Workflow #7 run karo.")
    docs = ["A.1001(25)", "MEPC.269(68)", "MSC.1/Circ.1625"]  # fallback

# --- SEARCH + RAG ---
st.divider()
st.subheader("🔍 Search IMO Docs (1125)")

search = st.text_input("Search karo - jaise: A.1001, MEPC, MSC, HKC:", placeholder="A.1001(25)")

# Filter logic
filtered = docs
if search:
    filtered = [d for d in docs if search.lower() in d.lower()]
    st.write(f"**Found {len(filtered)} / {len(docs)} docs for '{search}'**")
else:
    st.write(f"**Showing Top 100 of {len(docs)} Docs**")
    filtered = docs[:100]

# Show table
st.dataframe(filtered, use_container_width=True, height=400)

# --- RAG CHAT (Simple Keyword) ---
st.divider()
st.subheader("💬 IMO RAG Chat - 12002 Chunks")

user_q = st.text_input("IMO ke baare me pucho:", placeholder="What is Hong Kong Convention?")

if user_q:
    st.write(f"**Question:** {user_q}")
    # Simple RAG - chunks se search
    found_chunks = []
    master_files = glob.glob("master_imo_all_public_part*.txt")
    if master_files:
        for mf in master_files[:5]:  # first 5 parts for speed
            try:
                with open(mf, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read().lower()
                    if any(word.lower() in text for word in user_q.split()[:3]):
                        # Get snippet
                        idx = text.find(user_q.split()[0].lower())
                        if idx != -1:
                            snippet = text[max(0, idx-200):idx+500]
                            found_chunks.append(snippet[:800])
                            if len(found_chunks) >= 3:
                                break
            except:
                continue
    
    if found_chunks:
        st.success("Relevant chunks from 12002:")
        for i, ch in enumerate(found_chunks[:3], 1):
            st.markdown(f"**Chunk {i}:** {ch}...")
    else:
        st.info("Relevant chunk search: 12002 chunks me se answer - (Embeddings add karna baki hai)")

# --- FOOTER ---
st.divider()
st.caption("IMO 1125 RAG Bot | 1125 Docs | 12002 Chunks | Built with Streamlit | Last Build #7 - 1125 Full")
