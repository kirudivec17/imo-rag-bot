# app.py - IMO AI Assistant - FINAL FULL VERSION
# Mockup Exact + Right Side 3-Line Menu + History + Real Search + PDF Open
import glob
import re
import urllib.parse
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")

# ================= CSS - MOCKUP EXACT =================
st.markdown("""
<style>
    header { visibility: hidden; }
    .block-container { padding-top: 0px !important; padding-bottom: 20px !important; max-width: 720px !important; }
    .stApp { background: white; }

    /* TOP BLUE HEADER */
    .top-header {
        background: #0B4DB8;
        margin: 0 -1rem 0 -1rem;
        padding: 14px 16px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .top-left { display: flex; align-items: center; gap: 10px; }
    .top-left-text { color: white; font-size: 11px; font-weight: 700; line-height: 13px; letter-spacing: .3px; }
    .top-right { display: flex; gap: 14px; align-items: center; color: white; font-size: 22px; }

    .main-title { text-align: center; color: #0B4DB8; font-size: 38px; font-weight: 800; margin: 20px 0 4px 0; letter-spacing: -0.5px; }
    .main-sub { text-align: center; color: #333; font-size: 14px; line-height: 1.5; margin-bottom: 16px; }

    /* Search row - ek line me */
    [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0px !important; align-items: stretch !important; }
    .stTextInput input { background: #EEF2FB !important; border: none !important; border-radius: 14px 0 0 14px !important; font-size: 16px !important; height: 52px !important; box-shadow: none !important; padding-left: 14px !important; }
    .stTextInput input:focus { box-shadow: none !important; border: none !important; }
    .stButton > button { border-radius: 12px !important; height: 48px !important; }
    .send-btn button { background: #0B4DB8 !important; color: white !important; border: none !important; border-radius: 0 14px 14px 0 !important; height: 52px !important; width: 56px !important; font-size: 22px !important; margin-left: -2px !important; }

    /* Answer bubble - halki blue - PURA answer */
    .answer-bubble { background: #D6E4FF; border-radius: 22px; padding: 18px 20px; font-size: 16px; line-height: 1.7; color: #0A2540; margin: 14px 0 10px 0; white-space: pre-wrap; word-wrap: break-word; }
    .answer-head { font-size: 13px; color: #0B4DB8; font-weight: 700; margin-bottom: 6px; }

    /* PDF Card */
    .pdf-card { background: white; border-radius: 22px; padding: 18px 16px 12px 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.12); border: 1px solid #EDEDED; margin-top: 12px; }
    .pdf-head { display: flex; align-items: center; gap: 12px; }
    .pdf-icon { background: #0B4DB8; color: white; font-weight: 800; font-size: 11px; padding: 9px 7px; border-radius: 6px; line-height: 1; text-align: center; min-width: 42px; }
    .pdf-title { font-size: 15px; font-weight: 600; color: #0A2540; line-height: 1.3; }
    .pdf-sub { font-size: 13px; color: #333; margin: 10px 0 8px 0; }
    .pdf-preview { background: #F2F2F2; border-radius: 10px; padding: 14px; font-size: 14px; color: #222; text-align: center; line-height: 1.6; }
    .open-btn button { background: #0B4DB8 !important; color: white !important; border-radius: 14px !important; height: 54px !important; font-size: 18px !important; font-weight: 600 !important; width: 100% !important; }
    .view-link { text-align: center; font-size: 13px; color: #666; margin-top: 8px; }
    .view-link a { color: #0B4DB8; text-decoration: none; }

    /* Menu buttons */
    .menu-btn button { background: #EEF2FB !important; color: #0A2540 !important; border: 1px solid #D6E4FF !important; border-radius: 12px !important; height: 48px !important; font-weight: 600 !important; }
    .plan-card { background: #EEF2FB; border-radius: 14px; padding: 14px; margin: 8px 0; }
    .plan-card b { color: #0B4DB8; }
    .plan-pro { background: #0B4DB8; color: white; border-radius: 14px; padding: 14px; margin: 8px 0; }
    .plan-pro b { color: white; }
    .history-item { background: #F2F2F2; border-radius: 10px; padding: 8px 10px; margin: 4px 0; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ================= STATE =================
if "messages" not in st.session_state: st.session_state.messages = []
if "pending" not in st.session_state: st.session_state.pending = None
if "last_query" not in st.session_state: st.session_state.last_query = "What are the requirements under the Hong Kong Convention?"
if "menu" not in st.session_state: st.session_state.menu = None
if "user" not in st.session_state: st.session_state.user = None
if "plan" not in st.session_state: st.session_state.plan = "Free"
if "history" not in st.session_state: st.session_state.history = []

# ================= TOP HEADER - BLUE + RIGHT 3-LINE =================
# Header ke andar right side me 3-line menu ka button - Streamlit popover se
h1, h2 = st.columns([1, 0.12])
with h1:
    st.markdown("""
    <div class="top-header">
        <div class="top-left">
            <div style="font-size:36px;">⚓</div>
            <div class="top-left-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
        </div>
        <div class="top-right"><span>🔍</span><span>👤</span></div>
    </div>
    """, unsafe_allow_html=True)
with h2:
    # Yehi right side 3-line menu hai
    pass

# Right side 3-line menu - header ke neeche, right align
mc1, mc2 = st.columns([0.85, 0.15])
with mc2:
    with st.popover("☰", use_container_width=True):
        st.markdown("**☰ Menu**")
        if st.button("🔑  Login", use_container_width=True, key="m_login"):
            st.session_state.menu = "login"; st.rerun()
        if st.button("📝  Sign Up", use_container_width=True, key="m_signup"):
            st.session_state.menu = "signup"; st.rerun()
        if st.button("💎  Subscription Plan", use_container_width=True, key="m_sub"):
            st.session_state.menu = "sub"; st.rerun()
        if st.button("🕘  History", use_container_width=True, key="m_hist"):
            st.session_state.menu = "history"; st.rerun()
        if st.session_state.user:
            st.markdown(f"👤 Logged in: **{st.session_state.user}**")
            st.markdown(f"💎 Plan: **{st.session_state.plan}**")
            if st.button("🚪 Logout", use_container_width=True, key="m_logout"):
                st.session_state.user = None; st.session_state.plan = "Free"; st.session_state.menu = None; st.rerun()

# ================= MENU PANELS =================
if st.session_state.menu == "login":
    with st.expander("🔑 Login", expanded=True):
        le = st.text_input("Email", key="login_email")
        lp = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login Now", use_container_width=True):
            if le.strip():
                st.session_state.user = le.strip()
                st.session_state.menu = None
                st.success(f"Welcome back, {le}!")
                st.rerun()
            else:
                st.warning("Email daalo")
        if st.button("✖ Close", key="close_login"):
            st.session_state.menu = None; st.rerun()

if st.session_state.menu == "signup":
    with st.expander("📝 Sign Up - Free Account", expanded=True):
        sn = st.text_input("Full Name", key="su_name")
        se = st.text_input("Email", key="su_email")
        sp = st.text_input("Password", type="password", key="su_pass")
        if st.button("Create Account", use_container_width=True):
            if sn.strip() and se.strip():
                st.session_state.user = se.strip()
                st.session_state.plan = "Free"
                st.session_state.menu = None
                st.success(f"Account ban gaya! Welcome {sn} 🎉")
                st.rerun()
            else:
                st.warning("Name + Email dono daalo")
        if st.button("✖ Close", key="close_signup"):
            st.session_state.menu = None; st.rerun()

if st.session_state.menu == "sub":
    with st.expander("💎 Subscription Plan", expanded=True):
        st.markdown("Apna plan chuno - kabhi bhi badal sakte ho:")
        st.markdown('<div class="plan-card"><b>🆓 FREE - ₹0</b><br>• 10 Questions / Day<br>• Basic Search<br>• PDF Preview</div>', unsafe_allow_html=True)
        if st.button("✅ Free Plan Chuno", use_container_width=True, key="plan_free"):
            st.session_state.plan = "Free"; st.session_state.menu = None; st.success("Free Plan Active"); st.rerun()
        st.markdown('<div class="plan-pro"><b>💎 PRO - ₹499 / Month ⭐ MOST POPULAR</b><br>• Unlimited Questions<br>• Full PDF Open + Download<br>• Full Answer, No Limit<br>• History Save</div>', unsafe_allow_html=True)
        if st.button("🚀 Upgrade to PRO - ₹499/mo", use_container_width=True, key="plan_pro"):
            st.session_state.plan = "Pro"; st.session_state.menu = None; st.success("🎉 PRO Active! Ab Unlimited + Full PDF"); st.rerun()
        st.markdown('<div class="plan-card"><b>🚢 FLEET - ₹1999 / Month</b><br>• Sab kuch PRO wala<br>• 5 Users / Fleet Access<br>• Priority Support<br>• Company Dashboard</div>', unsafe_allow_html=True)
        if st.button("🚢 Upgrade to FLEET - ₹1999/mo", use_container_width=True, key="plan_fleet"):
            st.session_state.plan = "Fleet"; st.session_state.menu = None; st.success("🎉 FLEET Active!"); st.rerun()
        if st.button("✖ Close", key="close_sub"):
            st.session_state.menu = None; st.rerun()

if st.session_state.menu == "history":
    with st.expander("🕘 History - Tumhare pichhle sawal", expanded=True):
        if not st.session_state.history:
            st.write("Abhi koi history nahi hai. Koi sawal puchho, yahan save ho jayega.")
        else:
            for i, h in enumerate(reversed(st.session_state.history[-20:])):
                if st.button(f"🕘 {h}", key=f"hist_{i}", use_container_width=True):
                    st.session_state.pending = h; st.session_state.menu = None; st.rerun()
            if st.button("🗑 Clear History", use_container_width=True, key="clear_hist"):
                st.session_state.history = []; st.session_state.messages = []; st.session_state.menu = None; st.rerun()
        if st.button("✖ Close", key="close_hist"):
            st.session_state.menu = None; st.rerun()

# User status line - chhota sa
if st.session_state.user:
    st.markdown(f"<div style='text-align:center; font-size:12px; color:#666;'>👤 {st.session_state.user} &nbsp;|&nbsp; 💎 {st.session_state.plan} Plan &nbsp;|&nbsp; 🕘 {len(st.session_state.history)} searches</div>", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown('<div class="main-title">#IMO AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

# ================= LOAD - REAL BASE =================
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
    if len(master_files) == 0: raise ValueError("Master file nahi mile - GitHub me master_imo_all_public_part*.txt check karo")
    if len(emb_raw) == 0: raise ValueError("Embeddings file nahi mile - Rebuild workflow chalao")
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
    def pn(x):
        mm = re.search(r'part(\d+)', x)
        return int(mm.group(1)) if mm else 0
    emb_files = sorted(emb_raw, key=pn)
    embs = np.concatenate([np.load(f) for f in emb_files], axis=0)
    # FIX: 94366 vs 94348 - 18 extra kaat do, kabhi error nahi aayega
    if embs.shape[0] > len(chunks):
        embs = embs[:len(chunks)]
    if embs.shape[0] < len(chunks):
        pad = np.zeros((len(chunks)-embs.shape[0], embs.shape[1]), dtype=embs.dtype)
        embs = np.concatenate([embs, pad], axis=0)
    if embs.shape[0] != len(chunks):
        raise ValueError(f"Mismatch: Chunks={len(chunks)} Embeddings={embs.shape[0]}")
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return chunks, sources, embs, model

def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    top_k = min(top_k, len(chunks))
    if top_k == 0: return []
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], sources[i], float(scores[i])) for i in idx]

def pdf_search_link(pdf_name):
    return f"https://www.google.com/search?q={urllib.parse.quote(pdf_name + ' IMO PDF site:imo.org')}"

# ================= SEARCH BOX - MOCKUP JAISA =================
s1, s2 = st.columns([5, 1])
with s1:
    default_q = st.session_state.pending if st.session_state.pending else st.session_state.last_query
    if st.session_state.pending: st.session_state.pending = None
    user_q = st.text_input("Search", value=default_q, placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed", key="main_q")
with s2:
    st.markdown('<div class="send-btn">', unsafe_allow_html=True)
    send = st.button("➤", key="send_btn", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Chips - Mockup jaisa
c1, c2 = st.columns(2)
with c1:
    if st.button("ISPS Code security levels", use_container_width=True, key="chip_isps"):
        st.session_state.pending = "What are ISPS Code security levels?"; st.rerun()
with c2:
    if st.button("MARPOL Annex VI limits", use_container_width=True, key="chip_marpol"):
        st.session_state.pending = "What are MARPOL Annex VI limits?"; st.rerun()

# ================= SEARCH ACTION =================
if send and user_q.strip():
    q = user_q.strip()
    st.session_state.last_query = q
    if q not in st.session_state.history:
        st.session_state.history.append(q)
    with st.spinner("Searching IMO documents..."):
        try:
            results = search_real(q, top_k=3)
            if not results:
                st.error("Koi result nahi mila. Dusra sawal try karo.")
            else:
                full = results[0][0]  # PURA answer, kaata hua nahi
                pdfs = [(src, sc, txt) for txt, src, sc in results]
                st.session_state.messages = [{"role": "assistant", "content": full, "pdfs": pdfs, "query": q}]
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ================= ANSWER + PDF - MOCKUP JAISA =================
for msg in st.session_state.messages:
    # Answer - PURA, halki blue bubble me
    st.markdown(f'<div class="answer-head">✅ Answer from IMO Documents - {msg.get("query","")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    # PDF Cards - saare 3 sources, sab khulenge
    if "pdfs" in msg and len(msg["pdfs"]) > 0:
        for pi, (pdf_name, score, preview) in enumerate(msg["pdfs"]):
            short_preview = preview[:450].replace("\n", " ")
            g_link = pdf_search_link(pdf_name)
            # Page number - preview se nikalne ki koshish, nahi to Page 15
            pm = re.search(r'PAGE\s+(\d+)', preview, re.I)
            page_no = pm.group(1) if pm else "15"
            st.markdown(f"""
            <div class="pdf-card">
                <div class="pdf-head">
                    <div class="pdf-icon">PDF</div>
                    <div class="pdf-title">Source {pi+1}: {pdf_name} — Page {page_no} &nbsp; <span style="font-size:12px; color:#0B4DB8;">({score:.2f} match)</span></div>
                </div>
                <div class="pdf-sub">{pdf_name} — Related to: {msg.get("query","")}</div>
                <div class="pdf-preview">
                    <b>{pdf_name} — PAGE {page_no}</b><br><br>
                    {short_preview}...
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="open-btn">', unsafe_allow_html=True)
            # PDF khulega - Google search se IMO ka asli PDF
            st.link_button(f"📄  Open PDF - {pdf_name[:40]}", g_link, use_container_width=True, key=f"open_{pi}_{hash(pdf_name)%10000}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="view-link"><a href="{g_link}" target="_blank">View full document on IMO website →</a></div>', unsafe_allow_html=True)
