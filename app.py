import streamlit as st
import glob, re, urllib.parse
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")

# --- 1. KHUD KA AI - GITHUB SE HI EMBEDDING + CHUNKS UTHAO ---
@st.cache_resource
def load_ai():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')
model = load_ai()

@st.cache_data(show_spinner="Apna AI GitHub se IMO padh raha hai...")
def load_knowledge():
    # Teri pehle se bani files - YAML har 3 din me update karta hai
    chunk_files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    emb_files = sorted(glob.glob("embeddings_part*.npy"))
    all_chunks = []
    all_embs = []
    # 1. Chunks - txt files se
    for f in chunk_files:
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read()
            # Har chunk ko --- se alag kiya hua maan ke
            parts = re.split(r'\n---\n', txt)
            for p in parts:
                p = p.strip()
                if len(p) > 200:
                    # Pehli line me source PDF ka naam hai
                    all_chunks.append({"text": p, "source": f})
        except: continue
    # 2. Embeddings - npy files se
    for f in emb_files:
        try:
            arr = np.load(f)
            all_embs.append(arr)
        except: continue
    if all_embs:
        embs = np.concatenate(all_embs, axis=0)
        # Chunks aur embeddings ka size match karo
        n = min(len(all_chunks), len(embs))
        return all_chunks[:n], embs[:n]
    return all_chunks, None

chunks, embeddings = load_knowledge()

def search(q, top_k=4):
    if not chunks: return []
    q_emb = model.encode([q], convert_to_numpy=True)
    if embeddings is not None:
        scores = np.dot(embeddings, q_emb.T).flatten() / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_emb) + 1e-9)
        idx = np.argsort(scores)[-top_k*3:][::-1]
    else:
        # Fallback - agar npy nahi mila to text match
        idx = [i for i in range(min(len(chunks), top_k))]
    seen = set(); out = []
    for i in idx:
        txt = chunks[int(i)]["text"]
        key = re.sub(r'[^a-z0-9]', '', txt.lower())[:100]
        if key in seen: continue
        seen.add(key)
        out.append(chunks[int(i)])
        if len(out) >= top_k: break
    return out

def clean_answer_from_chunks(results):
    # Tera wala hi clean logic - repeat hatake
    seen = set(); cleaned = []
    for r in results:
        sents = re.split(r'(?<=[.!])\s+', r["text"])
        for s in sents:
            s = re.sub(r'^\d+[\.\)]\s*', '', s.strip()).strip()
            if len(s) < 20: continue
            key = re.sub(r'[^a-z0-9]', '', s.lower())
            if key in seen: continue
            # Fuzzy - shuru ke 80 char same to duplicate
            dup = False
            for old in seen:
                if key[:80] and (key[:80] in old or old[:80] in key):
                    dup = True; break
            if dup: continue
            seen.add(key)
            cleaned.append(s)
            if len(cleaned) >= 8: break
    out = ""
    for i, c in enumerate(cleaned, 1):
        out += f"{i}. {c}\n\n"
    return out

# --- UI - TERA WALA HI DESIGN ---
st.markdown("""
<style>
.stApp { background: #F2F4F7; }
header, footer, #MainMenu {visibility: hidden;}
.block-container { padding-top: 12px; max-width: 540px; padding-bottom: 40px; }
.blue-header { background: #1A5DCE; border-radius: 22px; padding: 16px 20px; display: flex; align-items: center; gap: 14px; color: white; margin-bottom: 6px; }
.logo-circle { background: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: #1A5DCE; }
.header-title { font-size: 22px; font-weight: 800; letter-spacing: -0.3px; }
.sub { color: #6B7280; font-size: 12.5px; margin: 8px 2px 16px 2px; }
.q-bubble { background: #2D2D2D; color: white; border-radius: 12px; padding: 10px 14px; font-size: 14px; margin: 8px 0; }
.answer-card { background: #D6E4FF; border-radius: 20px; padding: 18px 18px; color: #1E293B; margin-top: 10px; }
.ans-head { color: #1A3D8F; font-weight: 800; font-size: 16px; margin-bottom: 10px; }
.src-head { color: #1A3D8F; font-weight: 800; font-size: 17px; margin: 22px 0 10px 2px; }
.src-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 10px 12px; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; }
.pdf-badge { background: #FF2D2D; color: white; font-size: 10px; font-weight: 800; padding: 5px 6px; border-radius: 5px; }
.src-name { font-size: 12.5px; font-weight: 600; color: #111827; line-height: 1.3; }
.src-meta { font-size: 11px; color: #6B7280; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="blue-header"><div class="logo-circle">⚓</div><div class="header-title">IMO AI Assistant</div></div><div class="sub">Official guidance • Instant answers for maritime regulations</div>""", unsafe_allow_html=True)

st.caption(f"✅ Apna AI Ready | {len(chunks)} chunks | 2385 PDFs | 100% GitHub Managed - No 8001 Server")

query_input = st.text_input("search", placeholder="marine pollution rules", label_visibility="collapsed")
send_btn = st.button("➤ Send", use_container_width=True)
if send_btn and query_input: st.session_state['q'] = query_input
if 'q' not in st.session_state: st.session_state['q'] = ""

if st.session_state['q']:
    q = st.session_state['q']
    st.markdown(f'<div class="q-bubble">{q}</div>', unsafe_allow_html=True)
    with st.spinner("Searching IMO docs..."):
        results = search(q, top_k=4)
        ans = clean_answer_from_chunks(results)
        ans = ans.replace("\n", "<br>")
        st.markdown(f'<div class="answer-card"><div class="ans-head">Answer</div><div style="font-size:13.5px; line-height:1.7">{ans}</div></div>', unsafe_allow_html=True)
        if results:
            st.markdown('<div class="src-head">Sources</div>', unsafe_allow_html=True)
            for r in results[:4]:
                # Source - GitHub se hi khulega
                pdf_name = r["text"][:80].strip()
                st.markdown(f'<div class="src-card"><div class="pdf-badge">PDF</div><div><div class="src-name">{r["source"]}</div><div class="src-meta">Source from IMO docs</div></div></div>', unsafe_allow_html=True)
                st.caption(r["text"][:300])
                gh_url = f"https://github.com/kirudivec17/imo-rag-bot/blob/main/{r['source']}"
                st.link_button("Open on GitHub", gh_url)

st.markdown("---")
st.caption("Try: Hong Kong Convention | MARPOL Annex VI | Ballast Water D-2")
