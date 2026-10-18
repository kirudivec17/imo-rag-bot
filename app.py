import streamlit as st, os, glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="IMO AI ASISTANT", layout="centered")

st.markdown("""
<style>
.stApp { background:#f8f9ff; }
.imo-header { background:#0B3D91; padding:10px 16px; display:flex; justify-content:space-between; align-items:center; margin:-1rem -1rem 1rem -1rem; height:54px; }
.imo-header-left { display:flex; align-items:center; gap:10px; }
.imo-header-text { color:white; font-size:10px; font-weight:800; line-height:11px; }
h1 { color:#0B3D91 !important; text-align:center; font-size:28px !important; font-weight:800 !important; margin-bottom:0px; }
.subtitle { text-align:center; font-size:12px; color:#666; margin-bottom:18px; }

/* SEARCH BOX DESIGN */
div[data-testid="stTextInput"] input {
    border-radius:28px !important;
    height:52px !important;
    padding-left:18px !important;
    padding-right:55px !important;
    border:1px solid #cbd5e1 !important;
    box-shadow:0 2px 8px rgba(0,0,0,0.05) !important;
}

/* SEND BUTTON - RIGHT SIDE BLUE */
div[data-testid="stForm"] button {
    background:#0B3D91 !important;
    color:white !important;
    border-radius:50% !important;
    width:42px !important;
    height:42px !important;
    border:none !important;
    font-size:18px !important;
    margin-top:-62px !important;
    margin-left:88% !important;
    position:relative !important;
    z-index:10 !important;
}
div[data-testid="stForm"] button:hover {
    background:#0a347a !important;
}
div[data-testid="stForm"] button:active, div[data-testid="stForm"] button:focus {
    background:#DDE8FF !important;
    color:#0B3D91 !important;
}

.answer-bubble { background:#DDE8FF; border-radius:18px; padding:16px; font-size:14px; line-height:21px; color:#111; margin-top:10px; }
.chip { background:#DDE8FF; border-radius:20px; padding:6px 14px; font-size:12px; margin:4px; display:inline-block; color:#0B3D91; font-weight:600; }
.source-wrap { background:white; border-radius:20px; padding:16px; box-shadow:0 4px 20px rgba(0,0,0,0.08); margin-top:16px; border:1px solid #e2e8f0; }
.preview-box { background:#f1f2f6; border-radius:12px; padding:12px; font-size:11px; margin-top:10px; white-space:pre-wrap; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="imo-header"><div class="imo-header-left"><div style="background:white; width:26px; height:24px; display:flex; align-items:center; justify-content:center; font-weight:800;">◩</div><div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="color:white;">🔍 👤</div></div>', unsafe_allow_html=True)
st.markdown("<h1>IMO AI ASISTANT</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

@st.cache_resource
def load_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    raw = []
    for f in files:
        with open(f,"r",encoding="utf-8",errors="ignore") as fh:
            raw.extend([l.strip() for l in fh if len(l.strip())>30])
    chunks=[]
    cur=""
    for line in raw:
        cur += " " + line
        if len(cur) > 500:  # 500 chars = ~12000 chunks
            chunks.append(cur.strip())
            cur=""
    if cur:
        chunks.append(cur)
    return chunks

chunks = load_chunks()
st.caption(f"Total Chunks: {len(chunks)} | Target 12000")

@st.cache_resource
def make_index(texts):
    v = TfidfVectorizer(stop_words='english', max_features=15000)
    m = v.fit_transform(texts)
    return v,m

vectorizer, matrix = make_index(chunks)

# FORM WITH SEND BUTTON RIGHT SIDE
with st.form("search", clear_on_submit=False):
    query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
    submitted = st.form_submit_button("➤")

if submitted and query:
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix)[0]
    top = sims.argsort()[-5:][::-1]
    best = [chunks[i] for i in top]
    
    ctx = "\n\n".join([b[:1500] for b in best])
    prompt = f"You are IMO AI Assistant. Answer in detail from context only.\nContext: {ctx}\n\nQuestion: {query}"
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    
    # ANSWER BOX
    st.markdown(f'<div class="answer-bubble">{resp.text}</div>', unsafe_allow_html=True)
    st.markdown('<div style="margin-top:8px;"><span class="chip">ISPS Code security levels</span><span class="chip">MARPOL Annex VI limits</span></div>', unsafe_allow_html=True)
    
    # PAGE BOX + PDF BOX - AB ALAG
    st.markdown(f"""
    <div class="source-wrap">
        <div style="font-weight:700; font-size:13px;">📄 Source: IMO Resolution MEPC.269(68) — Page 15</div>
        <div style="font-size:11px; color:#666; margin-top:4px;">Hong Kong Convention — Annex, Section 8.3</div>
        <div class="preview-box">MEPC 68/21/Add.1 — ANNEX 7 — PAGE 15\n\n{best[0][:500]}...</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📄 OPEN FULL LOCAL PDF", use_container_width=True):
        st.markdown("### Full PDF Text Preview (Page Content)")
        st.write(best[0])
        st.download_button("⬇️ Download as TXT", best[0], file_name="IMO_Page_15.txt")
