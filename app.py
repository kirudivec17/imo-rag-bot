# app.py - IMO AI Assistant - FINAL SYSTEM DESIGN
# Header me Right ☰ + Question -> Answer -> PDF + New $$$ Plans
import glob
import re
import urllib.parse
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")

st.markdown("""
<style>
    header { visibility: hidden; }
    .block-container { padding-top: 0px !important; padding-bottom: 20px !important; max-width: 720px !important; }
    .stApp { background: #FFFFFF; }

    /* ===== HEADER - EK HI BLUE BAR ===== */
    .header-bar {
        background: #0B4DB8;
        margin: 0 -1rem 0 -1rem;
        padding: 12px 14px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .header-left { display: flex; align-items: center; gap: 10px; }
    .header-left-text { color: white; font-size: 11px; font-weight: 700; line-height: 13px; letter-spacing: .3px; }
    /* Header ke andar popover ko white karo */
    [data-testid="stPopover"] button { background: transparent !important; color: white !important; border: none !important; font-size: 26px !important; font-weight: 800 !important; height: 40px !important; }

    .main-title { text-align: center; color: #0B4DB8; font-size: 38px; font-weight: 800; margin: 18px 0 4px 0; letter-spacing: -0.5px; }
    .main-sub { text-align: center; color: #555; font-size: 14px; line-height: 1.5; margin-bottom: 16px; }

    /* ===== SEARCH - EK LINE ===== */
    [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0px !important; align-items: stretch !important; }
    .stTextInput input { background: #EEF2FB !important; border: none !important; border-radius: 14px 0 0 14px !important; font-size: 16px !important; height: 52px !important; box-shadow: none !important; padding-left: 14px !important; }
    .stTextInput input:focus { box-shadow: none !important; border: none !important; }
    .stButton > button { border-radius: 12px !important; height: 48px !important; }
    .send-btn button { background: #0B4DB8 !important; color: white !important; border: none !important; border-radius: 0 14px 14px 0 !important; height: 52px !important; width: 56px !important; font-size: 22px !important; margin-left: -2px !important; }

    /* ===== ANSWER BOX - QUESTION KE NICHE ===== */
    .answer-bubble { background: #D6E4FF; border-radius: 22px; padding: 18px 20px; font-size: 16px; line-height: 1.7; color: #0A2540; margin: 14px 0 10px 0; white-space: pre-wrap; word-wrap: break-word; }
    .answer-head { font-size: 13px; color: #0B4DB8; font-weight: 700; margin-bottom: 6px; }

    /* ===== PDF - SABSE NICHE ===== */
    .pdf-card { background: white; border-radius: 22px; padding: 18px 16px 12px 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.12); border: 1px solid #EDEDED; margin-top: 12px; }
    .pdf-head { display: flex; align-items: center; gap: 12px; }
    .pdf-icon { background: #0B4DB8; color: white; font-weight: 800; font-size: 11px; padding: 9px 7px; border-radius: 6px; line-height: 1; text-align: center; min-width: 42px; }
    .pdf-title { font-size: 15px; font-weight: 600; color: #0A2540; line-height: 1.3; }
    .pdf-sub { font-size: 13px; color: #333; margin: 10px 0 8px 0; }
    .pdf-preview { background: #F2F2F2; border-radius: 10px; padding: 14px; font-size: 14px; color: #222; text-align: center; line-height: 1.6; }
    .open-btn button { background: #0B4DB8 !important; color: white !important; border-radius: 14px !important; height: 54px !important; font-size: 18px !important; font-weight: 600 !important; width: 100% !important; }
    .view-link { text-align: center; font-size: 13px; color: #666; margin-top: 8px; }
    .view-link a { color: #0B4DB8; text-decoration: none; }

    /* ===== SUBSCRIPTION CARDS - $$$ ===== */
    .plan-free { background: #EEF2FB; border-radius: 14px; padding: 14px; margin: 8px 0; border: 1px solid #D6E4FF; }
    .plan-hot { background: #0B4DB8; color: white; border-radius: 14px; padding: 14px; margin: 8px 0; }
    .plan-hot b { color: white; }
    .plan-normal { background: white; border: 1px solid #E0E0E0; border-radius: 14px; padding: 14px; margin: 8px 0; }
    .price-big { font-size: 24px; font-weight: 800; }
    .badge { background: #FFC107; color: #000; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "pending" not in st.session_state: st.session_state.pending = None
if "last_query" not in st.session_state: st.session_state.last_query = "What are the requirements under the Hong Kong Convention?"
if "menu" not in st.session_state: st.session_state.menu = None
if "user" not in st.session_state: st.session_state.user = None
if "plan" not in st.session_state: st.session_state.plan = "Free"
if "history" not in st.session_state: st.session_state.history = []

# ================= HEADER - BLUE BAR + RIGHT SIDE ☰ ANDAR HI =================
# Ek hi row: Left IMO | Right ☰ - neeche nahi, andar hi
hc1, hc2 = st.columns([0.88, 0.12])
with hc1:
    st.markdown("""
    <div style="background:#0B4DB8; margin:0 -1rem 0 -1rem; padding:12px 14px; display:flex; align-items:center; gap:10px; height:62px;">
        <div style="font-size:36px;">⚓</div>
        <div style="color:white; font-size:11px; font-weight:700; line-height:13px;">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    """, unsafe_allow_html=True)
with hc2:
    # Ye ☰ header ke andar right side me hai
    st.markdown('<div style="background:#0B4DB8; height:62px; display:flex; align-items:center; justify-content:center; margin:0 -1rem 0 0;">', unsafe_allow_html=True)
    with st.popover("☰", use_container_width=True):
        st.markdown("**☰ Menu**")
        if st.button("🔑  Login", use_container_width=True, key="m_login"): st.session_state.menu="login"; st.rerun()
        if st.button("📝  Sign Up", use_container_width=True, key="m_signup"): st.session_state.menu="signup"; st.rerun()
        if st.button("💎  Subscription Plan", use_container_width=True, key="m_sub"): st.session_state.menu="sub"; st.rerun()
        if st.button("🕘  History", use_container_width=True, key="m_hist"): st.session_state.menu="history"; st.rerun()
        if st.session_state.user:
            st.markdown(f"👤 {st.session_state.user}\n💎 {st.session_state.plan}")
            if st.button("🚪 Logout", use_container_width=True, key="m_logout"): st.session_state.user=None; st.session_state.plan="Free"; st.session_state.menu=None; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ================= MENU PANELS =================
if st.session_state.menu == "login":
    with st.expander("🔑 Login", expanded=True):
        le = st.text_input("Email", key="login_email"); lp = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login Now", use_container_width=True):
            if le.strip(): st.session_state.user=le.strip(); st.session_state.menu=None; st.success("Welcome back!"); st.rerun()
        if st.button("✖ Close", key="close_login"): st.session_state.menu=None; st.rerun()

if st.session_state.menu == "signup":
    with st.expander("📝 Sign Up", expanded=True):
        sn = st.text_input("Full Name", key="su_name"); se = st.text_input("Email", key="su_email"); sp = st.text_input("Password", type="password", key="su_pass")
        if st.button("Create Account", use_container_width=True):
            if sn.strip() and se.strip(): st.session_state.user=se.strip(); st.session_state.plan="Free"; st.session_state.menu=None; st.success(f"Welcome {sn}!"); st.rerun()
        if st.button("✖ Close", key="close_signup"): st.session_state.menu=None; st.rerun()

if st.session_state.menu == "sub":
    with st.expander("💎 Subscription Plan - $$$", expanded=True):
        st.markdown("Apna plan chuno - kabhi bhi badal sakte ho. Sab plans me Full Answer + PDF Open hai.")
        # FREE
        st.markdown('<div class="plan-free"><b>🆓 FREE - $0</b><br><span class="price-big">$0</span> / forever<br>• 10 Questions / Day<br>• PDF Preview</div>', unsafe_allow_html=True)
        if st.button("✅ Free Plan - $0", use_container_width=True, key="plan_free"): st.session_state.plan="Free"; st.session_state.menu=None; st.success("Free Active"); st.rerun()
        # WEEKLY - $79
        st.markdown('<div class="plan-normal"><b>⚡ WEEKLY</b><br><span class="price-big">$79</span> / week<br>• Unlimited Questions<br>• Full PDF Open<br>• History Save</div>', unsafe_allow_html=True)
        if st.button("⚡ Buy Weekly - $79 / week", use_container_width=True, key="plan_week"): st.session_state.plan="Weekly $79"; st.session_state.menu=None; st.success("🎉 Weekly $79 Active!"); st.rerun()
        # MONTHLY - $199 - MOST POPULAR
        st.markdown('<div class="plan-hot"><b>💎 MONTHLY <span class="badge">MOST POPULAR</span></b><br><span class="price-big">$199</span> / month<br>• Unlimited Questions<br>• Full PDF Open + Download<br>• History Save<br>• Priority Search</div>', unsafe_allow_html=True)
        if st.button("🚀 Buy Monthly - $199 / month", use_container_width=True, key="plan_month"): st.session_state.plan="Monthly $199"; st.session_state.menu=None; st.success("🎉 Monthly $199 Active!"); st.rerun()
        # 3 MONTH - $499
        st.markdown('<div class="plan-normal"><b>📅 3 MONTHS - SAVE $98</b><br><span class="price-big">$499</span> / 3 months<br>• Monthly wala sab kuch<br>• 3 mahine ka ek saath<br>• $166 / month hi pada</div>', unsafe_allow_html=True)
        if st.button("📅 Buy 3 Months - $499", use_container_width=True, key="plan_3m"): st.session_state.plan="3 Months $499"; st.session_state.menu=None; st.success("🎉 3 Months $499 Active!"); st.rerun()
        # 6 MONTH - $799
        st.markdown('<div class="plan-normal"><b>📅 6 MONTHS - SAVE $395</b><br><span class="price-big">$799</span> / 6 months<br>• Monthly wala sab kuch<br>• $133 / month hi pada<br>• Best Value</div>', unsafe_allow_html=True)
        if st.button("📅 Buy 6 Months - $799", use_container_width=True, key="plan_6m"): st.session_state.plan="6 Months $799"; st.session_state.menu=None; st.success("🎉 6 Months $799 Active!"); st.rerun()
        # 1 YEAR - $1799
        st.markdown('<div class="plan-normal"><b>🏆 1 YEAR - SAVE $589</b><br><span class="price-big">$1799</span> / year<br>• Monthly wala sab kuch<br>• $149 / month hi pada<br>• 1 Year Full Access</div>', unsafe_allow_html=True)
        if st.button("🏆 Buy 1 Year - $1799", use_container_width=True, key="plan_1y"): st.session_state.plan="1 Year $1799"; st.session_state.menu=None; st.success("🎉 1 Year $1799 Active!"); st.rerun()
        if st.button("✖ Close", key="close_sub"): st.session_state.menu=None; st.rerun()

if st.session_state.menu == "history":
    with st.expander("🕘 History", expanded=True):
        if not st.session_state.history: st.write("Abhi koi history nahi hai.")
        else:
            for i, h in enumerate(reversed(st.session_state.history[-20:])):
                if st.button(f"🕘 {h}", key=f"hist_{i}", use_container_width=True): st.session_state.pending=h; st.session_state.menu=None; st.rerun()
            if st.button("🗑 Clear History", use_container_width=True): st.session_state.history=[]; st.session_state.messages=[]; st.session_state.menu=None; st.rerun()
        if st.button("✖ Close", key="close_hist"): st.session_state.menu=None; st.rerun()

if st.session_state.user:
    st.markdown(f"<div style='text-align:center; font-size:12px; color:#666;'>👤 {st.session_state.user} &nbsp;|&nbsp; 💎 {st.session_state.plan}</div>", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown('<div class="main-title">#IMO AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

# ================= CLEANING =================
def clean_text(raw):
    txt = raw
    txt = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', txt)
    txt = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', txt)
    out = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln: continue
        if ln.startswith("SOURCE:"): continue
        if ln.startswith("I:\\") or ln.startswith("I:/"): continue
        if "MEPC 80/17/Add.1" in ln: continue
        if re.match(r'^(RESOLUTION|2023 GUIDELINES|MINIMIZE THE TRANSFER|ANNEX \d+)', ln): continue
        if re.match(r'^\d+\s*$', ln): continue
        if len(ln) < 4: continue
        out.append(ln)
    txt = " ".join(out)
    txt = re.sub(r'\s+', ' ', txt)
    txt = txt.replace("..", ".").replace(" .", ".")
    return txt.strip()

def split_sentences(text):
    text = re.sub(r'\b(e\.g|i\.e|No|Mr|Dr|Art)\.\s', r'\1< DOT > ', text)
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])', text)
    parts = [p.replace("< DOT > ", ". ") for p in parts]
    return [p.strip() for p in parts if len(p.strip()) > 25]

def is_good_sentence(s):
    if len(s) < 30 or len(s) > 600: return False
    if re.match(r'^[a-z]{1,3}\b', s): return False
    if s[0].islower(): return False
    if s.count(" ") < 5: return False
    if len(re.findall(r'\d', s)) > 15: return False
    if "..." in s or "___" in s: return False
    return True

def build_clean_answer(query, results):
    q_words = [w.lower() for w in re.findall(r'[a-zA-Z]{4,}', query)]
    stop = {"what", "are", "the", "under", "with", "from", "about", "requirements", "requirement"}
    q_words = [w for w in q_words if w not in stop]
    seen = set(); scored = []
    for txt, src, score in results:
        for sent in split_sentences(txt):
            if not is_good_sentence(sent): continue
            low = sent.lower()
            key = low[:80]
            if key in seen: continue
            seen.add(key)
            hits = sum(1 for w in q_words if w in low)
            total = score + (hits * 0.15)
            scored.append((total, sent))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:10]]
    if not top:
        for txt, src, score in results:
            for sent in split_sentences(txt):
                if is_good_sentence(sent):
                    top.append(sent)
                    if len(top) >= 6: break
            if top: break
    paras = []
    for i in range(0, len(top), 3):
        paras.append(" ".join(top[i:i+3]))
    answer = "\n\n".join(paras)
    if results: answer += f"\n\n— Based on: {results[0][1]}"
    return answer

def clean_preview(text):
    sents = [s for s in split_sentences(text) if is_good_sentence(s)]
    if not sents: return text[:350]
    return " ".join(sents[:2])[:450]

@st.cache_resource
def load_all():
    master_files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    emb_raw = sorted(glob.glob("embeddings_part*.npy"))
    if len(master_files) == 0: raise ValueError("Master file nahi mile")
    if len(emb_raw) == 0: raise ValueError("Embeddings file nahi mile")
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
            chunks.append(body); sources.append(pdf)
    def pn(x):
        mm = re.search(r'part(\d+)', x)
        return int(mm.group(1)) if mm else 0
    emb_files = sorted(emb_raw, key=pn)
    embs = np.concatenate([np.load(f) for f in emb_files], axis=0)
    if embs.shape[0] > len(chunks): embs = embs[:len(chunks)]
    if embs.shape[0] < len(chunks):
        pad = np.zeros((len(chunks)-embs.shape[0], embs.shape[1]), dtype=embs.dtype)
        embs = np.concatenate([embs, pad], axis=0)
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return chunks, sources, embs, model

def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], sources[i], float(scores[i])) for i in idx]

def pdf_search_link(pdf_name):
    return f"https://www.google.com/search?q={urllib.parse.quote(pdf_name + ' IMO PDF site:imo.org')}"

# ================= LAYOUT: QUESTION -> ANSWER -> PDF =================
# 1. QUESTION BOX
s1, s2 = st.columns([5, 1])
with s1:
    default_q = st.session_state.pending if st.session_state.pending else st.session_state.last_query
    if st.session_state.pending: st.session_state.pending = None
    user_q = st.text_input("Search", value=default_q, placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed", key="main_q")
with s2:
    st.markdown('<div class="send-btn">', unsafe_allow_html=True)
    send = st.button("➤", key="send_btn", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# NO EXTRA QUESTIONS - chips hata diye, bilkul saaf

if send and user_q.strip():
    q = user_q.strip()
    st.session_state.last_query = q
    if q not in st.session_state.history: st.session_state.history.append(q)
    with st.spinner("Searching IMO documents..."):
        try:
            results = search_real(q, top_k=5)
            if not results: st.error("Koi result nahi mila.")
            else:
                clean_answer = build_clean_answer(q, results)
                pdfs = [(src, sc, txt) for txt, src, sc in results[:3]]
                st.session_state.messages = [{"role": "assistant", "content": clean_answer, "pdfs": pdfs, "query": q}]
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# 2. ANSWER BOX - QUESTION KE NICHE
for msg in st.session_state.messages:
    st.markdown(f'<div class="answer-head">✅ Answer from IMO Documents - {msg.get("query","")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="answer-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    # 3. PDF - SABSE NICHE
    if "pdfs" in msg and len(msg["pdfs"]) > 0:
        for pi, (pdf_name, score, preview_raw) in enumerate(msg["pdfs"]):
            preview = clean_preview(preview_raw)
            g_link = pdf_search_link(pdf_name)
            pm = re.search(r'PAGE\s+(\d+)', preview_raw, re.I)
            page_no = pm.group(1) if pm else "15"
            st.markdown(f"""
            <div class="pdf-card">
                <div class="pdf-head"><div class="pdf-icon">PDF</div><div class="pdf-title">Source {pi+1}: {pdf_name} — Page {page_no} &nbsp; <span style="font-size:12px; color:#0B4DB8;">({score:.2f} match)</span></div></div>
                <div class="pdf-sub">{pdf_name} — Related to: {msg.get("query","")}</div>
                <div class="pdf-preview"><b>{pdf_name} — PAGE {page_no}</b><br><br>{preview}...</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="open-btn">', unsafe_allow_html=True)
            st.link_button(f"📄  Open PDF - {pdf_name[:40]}", g_link, use_container_width=True, key=f"open_{pi}_{abs(hash(pdf_name))%10000}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="view-link"><a href="{g_link}" target="_blank">View full document on IMO website →</a></div>', unsafe_allow_html=True)
