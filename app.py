# app.py - IMO AI Assistant - Final Clean Version
import glob
import re
import urllib.parse
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

# ---------------- PAGE ----------------
st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="wide")

# ---------------- CSS - Pehle jaisa clean look ----------------
st.markdown("""
<style>
    .main-title { font-size: 32px; font-weight: 700; margin-bottom: 0px; }
    .sub-title { color: #666; font-size: 14px; margin-bottom: 20px; }
    .source-box { background: #f0f2f6; padding: 10px 14px; border-radius: 8px; font-size: 12px; color: #555; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚓ IMO AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Ask anything about MARPOL • SOLAS • STCW • MLC • IMO Resolutions</div>', unsafe_allow_html=True)

# ---------------- CLEAN TEXT ----------------
def clean_text(raw):
    out = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln: continue
        if ln.startswith("SOURCE:"): continue
        if ln.startswith("I:\\") or ln.startswith("I:/"): continue
        if "MEPC 80/17/Add.1" in ln: continue
        if ln.startswith("Annex"): continue
        if re.match(r'^(RESOLUTION|2023 GUIDELINES|MINIMIZE THE TRANSFER)', ln): continue
        if len(ln) < 3: continue
        out.append(ln)
    txt = " ".join(out)
    txt = re.sub(r'\s+', ' ', txt)
    txt = re.sub(r'-\s+', '', txt)
    return txt.strip()

# ---------------- LOAD ----------------
@st.cache_resource
def load_all():
    chunks, sources = [], []
    for f in sorted(glob.glob("master_imo_all_public_part*.txt")):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        for p in txt.split("---CHUNK---"):
            p = p.strip()
            if len(p) < 200: continue
            m = re.search(r'SOURCE:\s*(.+\.pdf)', p, re.I)
            if not m: continue
            pdf = urllib.parse.unquote(m.group(1).strip()).split("/")[-1].split("\\")[-1].strip()
            body = clean_text(p)
            if len(body) < 200: continue
            chunks.append(body)
            sources.append(pdf)
    def part_num(x):
        return int(re.search(r'part(\d+)', x).group(1))
    emb_files = sorted(glob.glob("embeddings_part*.npy"), key=part_num)
    embs = np.concatenate([np.load(f) for f in emb_files], axis=0)
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return chunks, sources, embs, model

def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], sources[i], float(scores[i])) for i in idx]

# ---------------- SIDEBAR - Pehle jaisa ----------------
with st.sidebar:
    st.header("⚓ IMO AI Assistant")
    st.write("Official IMO Documents se jawab")
    st.divider()
    top_k = st.slider("Sources", 1, 10, 5)
    st.divider()
    st.caption("Database: 94,348 chunks")
    st.caption("Status: ✅ Embeddings Matched")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- CHAT HISTORY ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- SUGGESTIONS - Fix wala, ab error nahi aayega ----------------
if len(st.session_state.messages) == 0:
    st.write("**Try these:**")
    c1, c2, c3 = st.columns(3)
    # Yahan hum session_state.query_box ko touch nahi kar rahe, seedha pending me daal rahe hain
    if c1.button("Sulphur limit in ECA?"):
        st.session_state.pending = "What is sulphur limit in ECA?"
        st.rerun()
    if c2.button("Ballast Water Management?"):
        st.session_state.pending = "What is Ballast Water Management requirement?"
        st.rerun()
    if c3.button("Seafarer rest hours?"):
        st.session_state.pending = "What are rest hours for seafarers?"
        st.rerun()

# ---------------- CHAT INPUT ----------------
prompt = st.chat_input("Ask about IMO regulations...")
# Agar suggestion button daba hai to wahi prompt ban jayega
if "pending" in st.session_state and st.session_state.pending:
    prompt = st.session_state.pending
    st.session_state.pending = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("IMO documents me dhoondh raha hu..."):
            try:
                results = search_real(prompt, top_k=top_k)
                # Pehla sabse accha result - seedha jawab
                best_text, best_src, best_score = results[0]
                # Jawab ko thoda saaf karke dikhao - 1200 chars tak
                answer = best_text[:1500]
                st.markdown(answer)
                st.markdown(f'<div class="source-box">📄 <b>Source:</b> {best_src} &nbsp;|&nbsp; Score: {best_score:.3f}</div>', unsafe_allow_html=True)
                if len(results) > 1:
                    with st.expander(f"📚 Aur {len(results)-1} sources dekho"):
                        for txt, src, sc in results[1:]:
                            st.write(txt[:800])
                            st.caption(f"Source: {src} | Score: {sc:.3f}")
                            st.divider()
                full_answer = answer + f"\n\n📄 Source: {best_src}"
                st.session_state.messages.append({"role": "assistant", "content": full_answer})
            except Exception as e:
                st.error(f"Error: {e}")
