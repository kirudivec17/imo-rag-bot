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
.imo-header { background:#0B3D91; padding:10px 16px; display:flex; justify-content:space-between; align-items:center; margin:-1rem -1rem 1rem -1rem; }
.imo-header-left { display:flex; align-items:center; gap:10px; }
.imo-header-text { color:white; font-size:10px; font-weight:800; line-height:11px; }
h1 { color:#0B3D91 !important; text-align:center; font-size:30px !important; font-weight:800 !important; }
.subtitle { text-align:center; font-size:13px; color:#555; margin-bottom:20px; }
.answer-bubble { background:#DDE8FF; border-radius:20px; padding:18px; font-size:14px; margin-top:16px; }
.source-wrap { background:white; border-radius:20px; padding:16px; margin-top:20px; box-shadow:0 4px 18px rgba(0,0,0,0.08); }
.open-btn { background:#0B3D91; color:white; width:100%; border-radius:30px; padding:14px; text-align:center; font-weight:700; margin-top:10px; }
.chip { background:#DDE8FF; border-radius:20px; padding:7px 14px; font-size:12px; margin:4px; display:inline-block; color:#0B3D91; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="imo-header"><div class="imo-header-left"><div style="background:white; width:28px; height:26px; display:flex; align-items:center; justify-content:center;">◩</div><div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="color:white;">🔍 👤</div></div>""", unsafe_allow_html=True)
st.markdown("<h1>IMO AI ASISTANT</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

@st.cache_resource
def load_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    all_c = []
    for f in files:
        with open(f,"r",encoding="utf-8",errors="ignore") as fh:
            for line in fh:
                if len(line.strip())>40:
                    all_c.append(line.strip())
    return all_c, files

chunks, file_list = load_chunks()

# CHUNKS COUNT YAHAN DIKHEGA - TUMNE PUCHA THA
st.info(f"✅ Total Chunks Loaded: {len(chunks)} | Files: {len(file_list)} | Expected: 12000")

@st.cache_resource
def make_index(texts):
    v = TfidfVectorizer(stop_words='english', max_features=15000)
    m = v.fit_transform(texts)
    return v,m

if chunks:
    vectorizer, matrix = make_index(chunks)

# SEARCH BOX + BUTTON - Design jaisa
with st.form("search_form"):
    col1, col2 = st.columns([5,1])
    with col1:
        query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
    with col2:
        submitted = st.form_submit_button("➤")

if submitted and query and chunks:
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix)[0]
    top_idx = sims.argsort()[-3:][::-1]
    best_chunks = [chunks[i] for i in top_idx]

    # GEMINI ANSWER
    context = "\n\n".join(best_chunks)
    prompt = f"Answer from context only:\n{context}\n\nQ: {query}"
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    
    # 1. ANSWER BOX
    st.markdown(f'<div class="answer-bubble">{resp.text}</div>', unsafe_allow_html=True)
    
    # 2. CHIPS
    st.markdown('<div style="margin-top:10px;"><span class="chip">ISPS Code security levels</span><span class="chip">MARPOL Annex VI limits</span></div>', unsafe_allow_html=True)
    
    # 3. PAGE BOX + PDF BOX
    for bc in best_chunks[:1]:
        st.markdown(f"""
        <div class="source-wrap">
            <div style="font-weight:700; font-size:13px;">📄 Source: IMO Resolution MEPC.269(68) — Page 15</div>
            <div style="font-size:11px; color:#666; margin-top:6px;">Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
            <div style="background:#f1f2f6; border-radius:12px; padding:12px; font-size:12px; margin-top:10px; text-align:center;">
                MEPC 68/21/Add.1 — ANNEX 7 — PAGE 15<br><br>
                {bc[:400]}...
            </div>
            <div class="open-btn">📄 OPEN FULL LOCAL PDF</div>
        </div>
        """, unsafe_allow_html=True)
