import streamlit as st
import glob, re, urllib.parse
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")

# ============ 1. BUCKET - YAHI 1 LINE BADALNI HAI ============
# 8001 wala mat daal - OCI Bucket ka Public URL daal
# Example: https://objectstorage.ap-mumbai-1.oraclecloud.com/n/TERA-NAMESPACE/b/imo-pdfs/o
BUCKET_URL = "https://objectstorage.ap-mumbai-1.oraclecloud.com/n/REPLACE/b/imo-pdfs/o"

if 'user' not in st.session_state: st.session_state.user = None
if 'plan' not in st.session_state: st.session_state.plan = None
if 'trial_started' not in st.session_state: st.session_state.trial_started = False
if 'free_used' not in st.session_state: st.session_state.free_used = 0
if 'show_plans' not in st.session_state: st.session_state.show_plans = False
if 'sel_plan' not in st.session_state: st.session_state.sel_plan = 'Yearly'

PLANS = [
    {"name": "Weekly", "price": "$79", "per": "/ week", "save": ""},
    {"name": "Monthly", "price": "$199", "per": "/ month", "save": ""},
    {"name": "3 Month", "price": "$499", "per": "/ 3 months", "save": "SAVE 16%"},
    {"name": "6 Month", "price": "$999", "per": "/ 6 months", "save": "SAVE 17%"},
    {"name": "Yearly", "price": "$1799", "per": "/ year", "save": "BEST VALUE - SAVE 25%"},
]

st.markdown("""
<style>
.stApp { background: #F2F4F7; }
header, footer, #MainMenu {visibility: hidden;}
.block-container { padding-top: 12px; max-width: 560px; padding-bottom: 40px; }
.blue-header { background: #1A5DCE; border-radius: 22px; padding: 16px 20px; display: flex; align-items: center; gap: 14px; color: white; margin-bottom: 6px; }
.logo-circle { background: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: #1A5DCE; }
.header-title { font-size: 22px; font-weight: 800; }
.sub { color: #6B7280; font-size: 12.5px; margin: 8px 2px 16px 2px; }
.q-bubble { background: #2D2D2D; color: white; border-radius: 12px; padding: 10px 14px; font-size: 14px; margin: 8px 0; }
.answer-card { background: #D6E4FF; border-radius: 20px; padding: 18px; color: #1E293B; margin-top: 10px; }
.ans-head { color: #1A3D8F; font-weight: 800; font-size: 16px; margin-bottom: 10px; }
.src-head { color: #1A3D8F; font-weight: 800; font-size: 17px; margin: 22px 0 10px 2px; }
.src-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 10px 12px; margin-bottom: 6px; }
.pdf-badge { background: #FF2D2D; color: white; font-size: 10px; font-weight: 800; padding: 5px 6px; border-radius: 5px; display:inline-block; }
.src-name { font-size: 12.5px; font-weight: 600; color: #111827; word-break: break-all; }
.src-meta { font-size: 11px; color: #6B7280; margin-top: 2px; }
.plan-card { background: white; border: 2px solid #E5E7EB; border-radius: 12px; padding: 12px; margin-bottom: 8px; }
.plan-sel { border-color: #1A5DCE; background: #D6E4FF; }
</style>
""", unsafe_allow_html=True)

# TOP BAR + 3-LINE
c1, c2 = st.columns([5, 1])
with c1:
    st.markdown("""<div class="blue-header"><div class="logo-circle">⚓</div><div class="header-title">IMO AI Assistant</div></div><div class="sub">Official guidance • Instant answers for maritime regulations</div>""", unsafe_allow_html=True)
with c2:
    with st.popover("☰", use_container_width=True):
        if st.session_state.user:
            st.write(f"👤 {st.session_state.user}")
            if st.session_state.plan: st.success(f"Plan: {st.session_state.plan}")
            elif st.session_state.trial_started: st.success("5 Days FREE Trial")
            else: st.warning("No Plan - Free mode")
            if st.button("💎 Subscription Plans", use_container_width=True):
                st.session_state.show_plans = True; st.rerun()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None; st.session_state.plan = None; st.session_state.trial_started = False; st.rerun()
        else:
            st.write("**Sign In**")
            if st.button("🔵 Continue with Google", use_container_width=True):
                st.session_state.user = "Google User"; st.session_state.show_plans = True; st.rerun()
            if st.button("⚫ Continue with GitHub", use_container_width=True):
                st.session_state.user = "GitHub User"; st.session_state.show_plans = True; st.rerun()
            if st.button("📧 Continue with Email", use_container_width=True):
                st.session_state.user = "Email User"; st.session_state.show_plans = True; st.rerun()
            st.caption("Sign in ke baad 5 Days FREE Trial milega.")

# SUBSCRIPTION
if st.session_state.show_plans:
    st.markdown("### 💎 Unlock Full Access")
    st.markdown("**5 DAYS FREE TRIAL** - No charge for 5 days • Cancel anytime")
    for p in PLANS:
        is_sel = (st.session_state.sel_plan == p['name'])
        cls = "plan-card plan-sel" if is_sel else "plan-card"
        st.markdown(f"""<div class="{cls}"><b>{p['name']}</b> - <b>{p['price']}{p['per']}</b> <span style="color:green;font-size:11px">{p['save']}</span></div>""", unsafe_allow_html=True)
        if st.button(f"Select {p['name']} - {p['price']}", key=f"plan_{p['name']}", use_container_width=True):
            st.session_state.sel_plan = p['name']; st.rerun()
    st.write(f"Selected: **{st.session_state.sel_plan}**")
    if st.button(f"▶ Start 5 Days FREE Trial - {st.session_state.sel_plan}", use_container_width=True, type="primary"):
        st.session_state.trial_started = True; st.session_state.plan = st.session_state.sel_plan; st.session_state.show_plans = False; st.success("Trial Started"); st.rerun()
    if st.button("Later - Free me try karo (2 sawal)", use_container_width=True):
        st.session_state.show_plans = False; st.rerun()
    st.stop()

# ============ AI - SAHI PARSING ============
@st.cache_resource
def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')
model = load_model()

def clean_text(raw):
    # Line join karo, kachra hatao
    lines = raw.splitlines()
    out = []
    for ln in lines:
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
    txt = re.sub(r'-\s+', '', txt)  # tuti hui line jodo
    return txt.strip()

@st.cache_data(show_spinner="Apna AI GitHub se IMO PDF padh raha hai...")
def load_knowledge():
    chunk_files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    emb_files = sorted(glob.glob("embeddings_part*.npy"))
    all_chunks = []
    for f in chunk_files:
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read()
            # SAHI SPLIT - ---CHUNK--- se
            parts = txt.split("---CHUNK---")
            for p in parts:
                p = p.strip()
                if len(p) < 200: continue
                m = re.search(r'SOURCE:\s*(.+\.pdf)', p, re.I)
                if not m: continue
                raw_pdf = m.group(1).strip()
                # %20 -> space, sahi naam dikhane ke liye
                pdf_name = urllib.parse.unquote(raw_pdf).split("/")[-1].split("\\")[-1].strip()
                body = clean_text(p)
                if len(body) < 200: continue
                all_chunks.append({"text": body, "pdf": pdf_name, "raw_pdf": raw_pdf, "file": f})
        except: continue
    all_embs = []
    for f in emb_files:
        try: all_embs.append(np.load(f))
        except: continue
    if all_embs:
        embs = np.concatenate(all_embs, axis=0)
        n = min(len(all_chunks), len(embs))
        return all_chunks[:n], embs[:n]
    return all_chunks, None

chunks, embeddings = load_knowledge()
st.caption(f"✅ Apna AI Ready | {len(chunks)} chunks | PDF Bucket se, AI GitHub se")

def search_real(q, top_k=3):
    if not chunks: return []
    q_emb = model.encode([q], convert_to_numpy=True)
    if embeddings is not None:
        denom = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_emb) + 1e-9
        scores = (embeddings @ q_emb.T).flatten() / denom
        idx = np.argsort(scores)[-top_k*5:][::-1]
        idx = [int(i) for i in idx if scores[i] > 0.30]
    else:
        idx = list(range(min(len(chunks), top_k)))
    seen_pdf = set(); out = []
    for i in idx:
        c = chunks[i]
        if c["pdf"].lower() in seen_pdf: continue
        seen_pdf.add(c["pdf"].lower()); out.append(c)
        if len(out) >= top_k: break
    return out

def make_clean_answer(results, q):
    # Sirf 3 chunk, har chunk se 2-3 saaf sentence, koi repeat nahi
    seen = set(); paras = []
    for r in results:
        sents = re.split(r'(?<=[.!])\s+', r["text"])
        take = []
        for s in sents:
            s = s.strip()
            if len(s) < 40 or len(s) > 400: continue
            if "http" in s.lower() or "www." in s.lower(): continue
            key = re.sub(r'[^a-z0-9]', '', s.lower())[:100]
            if key in seen: continue
            seen.add(key); take.append(s)
            if len(take) >= 3: break
        if take:
            paras.append(" ".join(take))
        if len(paras) >= 3: break
    if not paras:
        return "Is sawal ka seedha jawab in IMO docs me nahi mila. Alag words me pucho - jaise MARPOL Annex VI, Ballast Water, Hong Kong Convention."
    return "\n\n".join(paras)

# SEARCH UI
query_input = st.text_input("search", placeholder="marine pollution rules", label_visibility="collapsed")
send_btn = st.button("➤ Send", use_container_width=True)
if send_btn and query_input: st.session_state['q'] = query_input
if 'q' not in st.session_state: st.session_state['q'] = ""

if st.session_state['q']:
    q = st.session_state['q']
    if not st.session_state.user and st.session_state.free_used >= 2:
        st.warning("Free ke 2 sawal khatam. Sign In + 5 Days FREE Trial lo.")
        if st.button("💎 Plans Dekho", use_container_width=True):
            st.session_state.show_plans = True; st.rerun()
        st.stop()
    st.markdown(f'<div class="q-bubble">{q}</div>', unsafe_allow_html=True)
    with st.spinner("Searching real IMO docs..."):
        results = search_real(q, top_k=3)
        if not results:
            st.warning("Koi real match nahi mila. Alag words me try karo.")
        else:
            if not st.session_state.user: st.session_state.free_used += 1
            ans = make_clean_answer(results, q)
            ans_html = ans.replace("\n", "<br><br>")
            st.markdown(f'<div class="answer-card"><div class="ans-head">Answer - Real IMO Docs Se</div><div style="font-size:14px; line-height:1.7">{ans_html}</div></div>', unsafe_allow_html=True)
            st.markdown('<div class="src-head">Sources - PDF Kholo</div>', unsafe_allow_html=True)
            for r in results:
                pdf_name = r["pdf"]
                safe = urllib.parse.quote(pdf_name, safe='')
                pdf_url = f"{BUCKET_URL}/{safe}"
                st.markdown(f"""<div class="src-card"><span class="pdf-badge">PDF</span><div class="src-name">{pdf_name}</div><div class="src-meta">{r['file']} • Bucket se</div></div>""", unsafe_allow_html=True)
                st.caption(r["text"][:350])
                st.link_button(f"📄 Open {pdf_name[:35]}", pdf_url, use_container_width=True)
                st.write("")
st.markdown("---")
st.caption("Try: Hong Kong Convention | MARPOL Annex VI | Ballast Water D-2")
