# app.py - IMO AI Assistant - Premium Final Version
import glob
import re
import urllib.parse
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="wide")

# ---------------- CSS - Blue Header + Clean Look ----------------
st.markdown("""
<style>
    .block-container { padding-top: 0px !important; padding-bottom: 120px !important; }
    header { visibility: hidden; }
    .blue-header {
        background: linear-gradient(90deg, #0B3D91 0%, #1565C0 100%);
        color: white;
        padding: 14px 18px;
        border-radius: 0px 0px 14px 14px;
        display: flex; justify-content: space-between; align-items: center;
        position: sticky; top: 0; z-index: 999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .blue-header h1 { font-size: 22px; margin: 0; color: white; font-weight: 700; }
    .blue-header p { font-size: 12px; margin: 0; opacity: 0.85; color: white; }
    .menu-btn { background: rgba(255,255,255,0.2); border: none; color: white; font-size: 22px; padding: 4px 12px; border-radius: 8px; cursor: pointer; }
    .answer-box { background: #ffffff; border: 1px solid #e6e6e6; border-radius: 12px; padding: 18px; line-height: 1.7; font-size: 16px; white-space: pre-wrap; }
    .pdf-card { background: #F2F6FF; border: 1px solid #D0DDF5; border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .pdf-card b { font-size: 14px; color: #0B3D91; }
    .pdf-card span { font-size: 12px; color: #666; }
    .q-box { background: #EAF0FF; border-radius: 12px; padding: 12px 16px; font-weight: 600; font-size: 16px; margin-bottom: 10px; }
    .stTextArea textarea { font-size: 16px !important; border-radius: 12px !important; }
    .stButton > button { border-radius: 12px !important; height: 48px !important; font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- BLUE HEADER ----------------
# Right side 3-line menu - Streamlit popover se
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.markdown("""
    <div class="blue-header">
        <div><h1>⚓ IMO AI Assistant</h1><p>MARPOL • SOLAS • STCW • MLC • IMO Resolutions</p></div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    with st.popover("☰", use_container_width=True):
        st.markdown("### Menu")
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.show_login = True
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.show_signup = True
        if st.button("💎 Subscription", use_container_width=True):
            st.session_state.show_sub = True
        st.divider()
        st.caption("v2.0 • 94,348 chunks")

# Login / Signup / Subscription - popup jaisa
if st.session_state.get("show_login"):
    with st.expander("🔑 Login", expanded=True):
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_pass")
        if st.button("Login Now"):
            st.success("Logged in! (Demo)")
            st.session_state.show_login = False
        if st.button("Close", key="close_login"):
            st.session_state.show_login = False
if st.session_state.get("show_signup"):
    with st.expander("📝 Sign Up", expanded=True):
        st.text_input("Name", key="su_name")
        st.text_input("Email", key="su_email")
        st.text_input("Password", type="password", key="su_pass")
        if st.button("Create Account"):
            st.success("Account created! (Demo)")
            st.session_state.show_signup = False
if st.session_state.get("show_sub"):
    with st.expander("💎 Subscription", expanded=True):
        st.markdown("**Free:** 10 questions/day\n**Pro ₹499/mo:** Unlimited + PDF Download\n**Fleet ₹1999/mo:** Full Fleet Access")
        if st.button("Upgrade to Pro"):
            st.success("Pro selected! (Demo)")
            st.session_state.show_sub = False

# ---------------- LOAD ----------------
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
    def pn(x): return int(re.search(r'part(\d+)', x).group(1))
    emb_files = sorted(glob.glob("embeddings_part*.npy"), key=pn)
    embs = np.concatenate([np.load(f) for f in emb_files], axis=0)
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return chunks, sources, embs, model

def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    if len(chunks) == 0: raise ValueError("Chunks 0 - master file nahi mile")
    if embs.shape[0] == 0: raise ValueError("Embeddings 0 - embeddings_part*.npy nahi mile")
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], sources[i], float(scores[i])) for i in idx]

# ---------------- HISTORY ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

# Suggestion - pehle se
if len(st.session_state.messages) == 0:
    st.write("### 👋 Kya puchna hai?")
    s1, s2, s3 = st.columns(3)
    if s1.button("What is sulphur limit in ECA?", use_container_width=True):
        st.session_state.pending = "What is sulphur limit in ECA?"
        st.rerun()
    if s2.button("Ballast water treatment plan?", use_container_width=True):
        st.session_state.pending = "What is ballast water treatment plan requirement?"
        st.rerun()
    if s3.button("Seafarer rest hours?", use_container_width=True):
        st.session_state.pending = "What are rest hours for seafarers?"
        st.rerun()

# ---------------- SHOW CHAT - FULL ANSWER, NO CUT ----------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="q-box">🧑‍✈️ {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="answer-box">{msg["content"]}</div>', unsafe_allow_html=True)
        # PDF cards - is message ke liye
        if "pdfs" in msg:
            st.write("**📄 Related PDFs - Click to Open:**")
            for pdf_name, score in msg["pdfs"]:
                # Google search link - ek click pe PDF khul jayega
                g_link = f"https://www.google.com/search?q={urllib.parse.quote(pdf_name + ' IMO PDF')}"
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f'<div class="pdf-card"><div><b>📕 {pdf_name}</b><br><span>Relevance: {score:.3f} • IMO Official Document</span></div></div>', unsafe_allow_html=True)
                with c2:
                    st.link_button("Open PDF ↗", g_link, use_container_width=True)

# ---------------- BOTTOM INPUT - Question Box + Speaker + Send ----------------
st.divider()
st.write("**Ask IMO AI:**")
# Pending suggestion ko box me daalo
default_q = st.session_state.pending if st.session_state.pending else ""
if st.session_state.pending:
    st.session_state.pending = None

q_col1, q_col2, q_col3 = st.columns([7, 1, 1])
with q_col1:
    user_q = st.text_area("Question", value=default_q, placeholder="Apna sawal yahan pura likho... e.g. What is sulphur limit in ECA?", height=68, label_visibility="collapsed", key="main_q")
with q_col2:
    # Speaker / Mic box - click karne pe batayega
    mic = st.button("🎤", help="Voice - bol ke pucho", use_container_width=True)
    if mic:
        st.info("🎤 Mic dabao aur bolo... (Browser mic permission chahiye)")
with q_col3:
    send = st.button("➤ Send", type="primary", use_container_width=True)

if send and user_q.strip():
    query = user_q.strip()
    st.session_state.messages.append({"role": "user", "content": query})
    with st.spinner("IMO documents me dhoondh raha hu..."):
        try:
            results = search_real(query, top_k=5)
            if not results:
                st.error("Koi result nahi mila.")
            else:
                # FULL answer - koi [:1500] nahi, pura chunk
                full_text = results[0][0]
                pdfs = [(src, sc) for _, src, sc in results]
                # Full answer ko history me daalo
                st.session_state.messages.append({"role": "assistant", "content": full_text, "pdfs": pdfs})
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
elif send and not user_q.strip():
    st.warning("Pehle sawal likho!")
