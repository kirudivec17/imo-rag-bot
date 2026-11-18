# app.py - IMO AI Assistant - Original Design + Embedding Fix
# Chunks: 94348 | Embeddings: 94348
import glob
import re
import urllib.parse
import os
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="wide")

# ---------------- ORIGINAL CSS - Blue Header + Watermark ----------------
st.markdown("""
<style>
    .stApp { background-color: #f6f8fb; }
    header { visibility: hidden; }
    .block-container { padding-top: 0px !important; padding-bottom: 20px !important; position: relative; z-index: 1; }

    /* BLUE HEADER - ORIGINAL */
    .imo-header {
        background: linear-gradient(90deg, #0A2540 0%, #0A4A7A 100%);
        padding: 14px 20px;
        display: flex; justify-content: space-between; align-items: center;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 0px 0px 12px 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .imo-header-left { display: flex; align-items: center; gap: 12px; }
    .imo-header-text { color: white; font-size: 11px; font-weight: 700; line-height: 13px; letter-spacing: 0.5px; }
    .imo-header-right { color: white; font-size: 20px; display: flex; gap: 14px; align-items: center; }

    /* WATERMARK */
    .watermark {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        opacity: 0.04; pointer-events: none; z-index: 0;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><text x='50' y='150' font-size='28' fill='black'>IMO ⚓</text></svg>");
        background-repeat: repeat;
    }

    .main-title { font-size: 24px; font-weight: 700; color: #0A2540; margin: 6px 0 2px 0; }
    .sub-title { font-size: 13px; color: #666; margin-bottom: 14px; }
    .q-box { background: #EAF0FF; border: 1px solid #D0DDF5; border-radius: 12px; padding: 12px 16px; font-weight: 600; font-size: 16px; margin: 12px 0 10px 0; }
    .answer-box { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; font-size: 16px; line-height: 1.75; white-space: pre-wrap; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .source-card { background: white; border-radius: 12px; padding: 14px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 10px; }
    .preview-box { background: #f3f4f6; border-radius: 8px; padding: 10px; font-size: 13px; color: #374151; max-height: 140px; overflow-y: auto; margin: 8px 0; }
    .stTextArea textarea { font-size: 16px !important; border-radius: 12px !important; background: white !important; }
    .stButton > button { border-radius: 12px !important; height: 52px !important; font-size: 16px !important; }
</style>
<div class="watermark"></div>
""", unsafe_allow_html=True)

# ---------------- BLUE HEADER + 3-LINE MENU ----------------
h1, h2 = st.columns([6, 1])
with h1:
    st.markdown("""
    <div class="imo-header">
        <div class="imo-header-left">
            <span style="font-size:28px; color:white;">◩</span>
            <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
        </div>
        <div style="color:white; text-align:right;">
            <div style="font-size:18px; font-weight:700;">IMO AI ASSISTANT</div>
            <div style="font-size:11px; opacity:0.85;">Ask from IMO Docs • MARPOL • SOLAS • STCW • MLC</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with h2:
    with st.popover("☰ Menu", use_container_width=True):
        st.markdown("### ☰ Menu")
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.show_login = True
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.show_signup = True
        if st.button("💎 Subscription", use_container_width=True):
            st.session_state.show_sub = True
        st.divider()
        st.caption("94,348 chunks • ✅ Matched")

if st.session_state.get("show_login"):
    with st.expander("🔑 Login", expanded=True):
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_pass")
        c1, c2 = st.columns(2)
        if c1.button("Login Now", use_container_width=True):
            st.success("Logged in!")
            st.session_state.show_login = False
        if c2.button("Close", key="close_login", use_container_width=True):
            st.session_state.show_login = False
if st.session_state.get("show_signup"):
    with st.expander("📝 Sign Up", expanded=True):
        st.text_input("Name", key="su_name")
        st.text_input("Email", key="su_email")
        st.text_input("Password", type="password", key="su_pass")
        if st.button("Create Account"):
            st.success("Account created!")
            st.session_state.show_signup = False
if st.session_state.get("show_sub"):
    with st.expander("💎 Subscription", expanded=True):
        st.markdown("**Free:** 10 Q/day\n**Pro ₹499/mo:** Unlimited + Full PDF\n**Fleet ₹1999/mo:** Full Fleet Access")
        if st.button("Upgrade to Pro"):
            st.success("Pro selected!")
            st.session_state.show_sub = False

st.markdown('<div class="main-title">IMO AI Assistant — Ask from IMO Docs</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Answer seedha IMO ke official PDF se aayega, full answer, koi katkut nahi.</div>', unsafe_allow_html=True)

# ---------------- LOAD - LIST INDEX FIX KE SAATH ----------------
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

@st.cache_resource
def load_all():
    master_files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    emb_raw = sorted(glob.glob("embeddings_part*.npy"))
    if len(master_files) == 0:
        raise ValueError("Master file nahi mile - GitHub root me master_imo_all_public_part*.txt check karo")
    if len(emb_raw) == 0:
        raise ValueError("Embeddings file nahi mile - embeddings_part*.npy check karo")
    chunks, sources = [], []
    for f in master_files:
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
    if len(chunks) == 0:
        raise ValueError("Chunks 0 bane - ---CHUNK--- format galat hai")
    def pn(x):
        mm = re.search(r'part(\d+)', x)
        return int(mm.group(1)) if mm else 0
    emb_files = sorted(emb_raw, key=pn)
    embs = np.concatenate([np.load(f) for f in emb_files], axis=0)
    if embs.shape[0] != len(chunks):
        raise ValueError(f"Mismatch: Chunks={len(chunks)} Embeddings={embs.shape[0]}")
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return chunks, sources, embs, model

def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    top_k = min(top_k, len(chunks))
    if top_k == 0:
        return []
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], sources[i], float(scores[i])) for i in idx]

# ---------------- SIDEBAR - Original Document Library ----------------
with st.sidebar:
    st.markdown("### 📚 Document Library")
    try:
        _c, _s, _e, _m = load_all()
        st.metric("Total Chunks", len(_c))
        st.metric("Embeddings", _e.shape[0])
        st.success("✅ Matched")
    except Exception as e:
        st.error(str(e))
    st.divider()
    st.markdown("**Standards:**\n- MARPOL\n- SOLAS\n- STCW\n- MLC\n- Hong Kong Convention")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- CHAT STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

if len(st.session_state.messages) == 0:
    st.write("**Try karo:**")
    s1, s2, s3 = st.columns(3)
    if s1.button("Sulphur limit in ECA?", use_container_width=True):
        st.session_state.pending = "What is sulphur limit in ECA?"
        st.rerun()
    if s2.button("Ballast Water Management?", use_container_width=True):
        st.session_state.pending = "What is Ballast Water Management requirement?"
        st.rerun()
    if s3.button("Seafarer rest hours?", use_container_width=True):
        st.session_state.pending = "What are rest hours for seafarers?"
        st.rerun()

# ---------------- SHOW HISTORY - FULL ANSWER ----------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="q-box">🧑‍✈️ {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        # FULL answer - koi [:1500] nahi
        st.markdown(f'<div class="answer-box">{msg["content"]}</div>', unsafe_allow_html=True)
        if "pdfs" in msg:
            st.markdown("#### 📑 Sources with PDF")
            for pdf_name, score, preview in msg["pdfs"]:
                g_link = f"https://www.google.com/search?q={urllib.parse.quote(pdf_name + ' IMO PDF')}"
                st.markdown(f"""
                <div class="source-card">
                    <b>Source:</b> {pdf_name} — Relevance {score:.3f}<br>
                    <div class="preview-box">{preview}</div>
                </div>
                """, unsafe_allow_html=True)
                st.link_button(f"📕 Open {pdf_name} ↗", g_link, use_container_width=True)

# ---------------- BOTTOM - Question Box + Speaker + Send ----------------
st.divider()
st.write("**Ask IMO AI:**")
default_q = st.session_state.pending if st.session_state.pending else ""
if st.session_state.pending:
    st.session_state.pending = None

q1, q2, q3 = st.columns([7, 1, 1])
with q1:
    user_q = st.text_area("Question", value=default_q, placeholder="Apna sawal yahan pura likho... e.g. What is sulphur limit in ECA?", height=68, label_visibility="collapsed", key="main_q")
with q2:
    mic = st.button("🎤", help="Voice - bol ke pucho", use_container_width=True)
    if mic:
        st.info("🎤 Mic on karo aur bolo... (Browser permission chahiye)")
with q3:
    send = st.button("➤ Send", type="primary", use_container_width=True)

if send and user_q.strip():
    query = user_q.strip()
    st.session_state.messages.append({"role": "user", "content": query})
    with st.spinner("Searching 94,348 chunks..."):
        try:
            results = search_real(query, top_k=5)
            if not results:
                st.error("Koi result nahi mila. Dobara try karo.")
                st.session_state.messages.pop()
            else:
                # FULL answer - pura chunk, koi cut nahi
                full_text = results[0][0]
                pdfs = [(src, sc, txt[:700].replace("\n", " ")) for txt, src, sc in results]
                st.session_state.messages.append({"role": "assistant", "content": full_text, "pdfs": pdfs})
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.messages.pop()
elif send and not user_q.strip():
    st.warning("Pehle sawal likho!")
