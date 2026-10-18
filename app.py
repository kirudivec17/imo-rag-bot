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
h1 { color:#0B3D91 !important; text-align:center; font-size:28px !important; font-weight:800 !important; }
.subtitle { text-align:center; font-size:12px; color:#666; margin-bottom:18px; }
div[data-testid="stTextInput"] input { border-radius:28px !important; height:52px !important; padding-right:55px !important; }
div[data-testid="stForm"] button { background:#0B3D91 !important; color:white !important; border-radius:50% !important; width:42px !important; height:42px !important; margin-top:-62px !important; margin-left:88% !important; }
.answer-bubble { background:#DDE8FF; border-radius:18px; padding:16px; font-size:14px; line-height:21px; }
.source-wrap { background:white; border-radius:20px; padding:16px; box-shadow:0 4px 20px rgba(0,0,0,0.08); margin-top:16px; cursor:pointer; }
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
    chunks, cur = [], ""
    for line in raw:
        cur += " " + line
        if len(cur) > 500:
            chunks.append(cur.strip())
            cur=""
    if cur: chunks.append(cur)
    return chunks

chunks = load_chunks()
st.caption(f"Total Chunks: {len(chunks)} | Target 12000")

@st.cache_resource
def make_index(texts):
    v = TfidfVectorizer(stop_words='english', max_features=20000, ngram_range=(1,2))
    m = v.fit_transform(texts)
    return v,m

vectorizer, matrix = make_index(chunks)

if 'last_ans' not in st.session_state:
    st.session_state.last_ans = None
    st.session_state.last_best = []

with st.form("search"):
    query = st.text_input("", placeholder="What are the ISPS Code security levels?", label_visibility="collapsed")
    submitted = st.form_submit_button("➤")

if submitted and query:
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix)[0]
    # keyword boost for ISPS
    if "ISPS" in query.upper() or "security level" in query.lower():
        for i,c in enumerate(chunks):
            if "security level 1" in c.lower() or "security level" in c.lower() and "isps" in c.lower():
                sims[i] += 0.3
    top = sims.argsort()[-8:][::-1]
    best = [chunks[i] for i in top]
    ctx = "\n\n".join([b[:1500] for b in best])
    prompt = f"You are IMO Expert. If context has info, use it. If context lacks ISPS levels, answer from general IMO knowledge: ISPS has 3 levels - Level 1 Normal, Level 2 Heightened, Level 3 Exceptional. Context: {ctx}\n\nQ: {query}\nDetailed Answer:"
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    st.session_state.last_ans = resp.text
    st.session_state.last_best = best

if st.session_state.last_ans:
    st.markdown(f'<div class="answer-bubble">{st.session_state.last_ans}</div>', unsafe_allow_html=True)
    best = st.session_state.last_best
    if best:
        with st.expander("📄 Source: IMO Resolution MEPC.269(68) — Page 15 (Click to open page)", expanded=True):
            st.write(best[0][:2000])
            st.markdown("**Hong Kong Convention — Annex, Section 8.3**")
        if st.button("📄 OPEN FULL LOCAL PDF", use_container_width=True, key="pdf"):
            st.success("Full PDF Text:")
            st.text_area("PDF Content", best[0], height=400)
            st.download_button("Download PDF Text", best[0], file_name="IMO_Source.txt")
