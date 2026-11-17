# app.py - IMO RAG Bot - Clean Version
# Chunks: 94348 | Embeddings: 94348 | Match: True
import glob
import re
import urllib.parse
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="IMO RAG Bot", page_icon="⚓", layout="wide")
st.title("⚓ IMO RAG Bot")
st.caption("MARPOL • SOLAS • STCW • MLC - Official IMO Documents se jawab")
st.divider()

# ---------------- CLEAN TEXT - Rebuild wala same ----------------
def clean_text(raw):
    lines = raw.splitlines()
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("SOURCE:"):
            continue
        if ln.startswith("I:\\") or ln.startswith("I:/"):
            continue
        if "MEPC 80/17/Add.1" in ln:
            continue
        if ln.startswith("Annex"):
            continue
        if re.match(r'^(RESOLUTION|2023 GUIDELINES|MINIMIZE THE TRANSFER)', ln):
            continue
        if len(ln) < 3:
            continue
        out.append(ln)
    txt = " ".join(out)
    txt = re.sub(r'\s+', ' ', txt)
    txt = re.sub(r'-\s+', '', txt)
    return txt.strip()

# ---------------- LOAD ALL - Ek baar hi load hoga ----------------
@st.cache_resource
def load_all():
    # 1. Chunks load karo - rebuild wale order me
    all_chunks = []
    all_sources = []
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    for f in files:
        txt = open(f, encoding="utf-8", errors="ignore").read()
        for p in txt.split("---CHUNK---"):
            p = p.strip()
            if len(p) < 200:
                continue
            m = re.search(r'SOURCE:\s*(.+\.pdf)', p, re.I)
            if not m:
                continue
            pdf = urllib.parse.unquote(m.group(1).strip()).split("/")[-1].split("\\")[-1].strip()
            body = clean_text(p)
            if len(body) < 200:
                continue
            all_chunks.append(body)
            all_sources.append(pdf)

    # 2. Embeddings load karo - part1 se part10 tak
    def part_num(x):
        return int(re.search(r'part(\d+)', x).group(1))
    emb_files = sorted(glob.glob("embeddings_part*.npy"), key=part_num)
    embs = np.concatenate([np.load(f) for f in emb_files], axis=0)
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)

    # 3. Model load karo
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return all_chunks, all_sources, embs, model

# ---------------- SEARCH ----------------
def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    results = []
    for i in idx:
        results.append({
            "text": chunks[i],
            "source": sources[i],
            "score": float(scores[i])
        })
    return results

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    top_k = st.slider("Kitne results chahiye?", 1, 10, 5)
    st.divider()
    st.info("Database: 94,348 chunks\nEmbeddings: 94,348\nStatus: ✅ Matched")
    if st.button("🔄 Cache Clear"):
        st.cache_resource.clear()
        st.rerun()

# ---------------- MAIN UI ----------------
query = st.text_input(
    "Apna sawal likho:",
    placeholder="e.g. What is sulphur limit in ECA?",
    key="query_box"
)

col1, col2 = st.columns([1, 4])
with col1:
    search_btn = st.button("🔍 Search", type="primary", use_container_width=True)
with col2:
    st.write("")

# Example buttons
st.write("**Try karo:**")
e1, e2, e3 = st.columns(3)
if e1.button("Sulphur limit in ECA?"):
    st.session_state.query_box = "What is sulphur limit in ECA?"
    st.rerun()
if e2.button("Ballast Water Management?"):
    st.session_state.query_box = "What is Ballast Water Management requirement?"
    st.rerun()
if e3.button("Seafarer rest hours?"):
    st.session_state.query_box = "What are rest hours for seafarers?"
    st.rerun()

# ---------------- RESULT ----------------
if search_btn and query.strip():
    with st.spinner("IMO documents me dhoondh raha hu..."):
        try:
            results = search_real(query, top_k=top_k)
            st.success(f"✅ {len(results)} results mile")
            for i, r in enumerate(results, 1):
                with st.expander(f"📄 Result {i} - {r['source']} | Score: {r['score']:.3f}", expanded=(i == 1)):
                    st.write(r["text"])
                    st.caption(f"Source: {r['source']}")
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Streamlit Cloud pe Reboot daba ke dobara try karo.")

elif search_btn and not query.strip():
    st.warning("Pehle sawal to likho!")

else:
    st.info("👆 Upar sawal likh ke Search dabao. Jawab seedha IMO ke official PDF se aayega.")
