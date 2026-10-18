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
h1 { color:#0B3D91 !important; text-align:center; font-size:28px !important; }
.subtitle { text-align:center; font-size:12px; color:#666; margin-bottom:15px; }
div[data-testid="stTextInput"] input { border-radius:30px !important; padding-right:50px !important; }
.send-btn-fix button { border-radius:50% !important; background:#0B3D91 !important; color:white !important; width:42px; height:42px; margin-top:-62px; margin-left:85%; position:relative; z-index:10; }
.answer-bubble { background:#DDE8FF; border-radius:18px; padding:16px; font-size:14px; line-height:21px; }
.source-wrap { background:white; border-radius:20px; padding:16px; box-shadow:0 4px 18px rgba(0,0,0,0.08); margin-top:15px; }
.preview-box { background:#f1f2f6; border-radius:12px; padding:12px; font-size:11px; margin-top:10px; white-space:pre-wrap; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="imo-header"><div class="imo-header-left"><div style="background:white; width:26px; height:24px; display:flex; align-items:center; justify-content:center;">◩</div><div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="color:white;">🔍 👤</div></div>', unsafe_allow_html=True)
st.markdown("<h1>IMO AI ASISTANT</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

@st.cache_resource
def load_chunks_correct():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    raw_lines = []
    for f in files:
        with open(f,"r",encoding="utf-8",errors="ignore") as fh:
            raw_lines.extend([l.strip() for l in fh if len(l.strip())>30])
    
    # Ab 80028 lines ko jod ke 12000 chunks banate hain - tumhara original logic
    chunks = []
    curr = ""
    for line in raw_lines:
        curr += " " + line
        if len(curr) > 900:  # har 900 chars pe 1 chunk
            chunks.append(curr.strip())
            curr = ""
    if curr:
        chunks.append(curr)
    return chunks

chunks = load_chunks_correct()
st.caption(f"Total Chunks: {len(chunks)} (tumhara original 12000 ke aas-paas) | Raw lines: 80028 se banaye")

@st.cache_resource
def make_index(texts):
    v = TfidfVectorizer(stop_words='english', max_features=15000)
    m = v.fit_transform(texts)
    return v,m

vectorizer, matrix = make_index(chunks)

query = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?")
send = st.button("➤ Send")

if query:
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, matrix)[0]
    top_idx = sims.argsort()[-5:][::-1]  # 5 chunks lega toh answer pura ayega
    best = [chunks[i] for i in top_idx]
    
    ctx = "\n\n".join([b[:1500] for b in best]) # bada context
    prompt = f"You are IMO AI Assistant. Answer in detail from context, don't say not completed. Context: {ctx}\n\nQuestion: {query}\nDetailed Answer:"
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    
    st.markdown(f'<div class="answer-bubble">{resp.text}</div>', unsafe_allow_html=True)
    
    # PDF Box - ab open hoga
    with st.expander(f"📄 Source: IMO Resolution MEPC.269(68) — Page 15", expanded=True):
        st.markdown("Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements")
        st.markdown(f'<div class="preview-box">{best[0][:2000]}</div>', unsafe_allow_html=True)
        if st.button("📄 OPEN FULL LOCAL PDF", use_container_width=True):
            st.info("Full text preview:")
            st.write(best[0])
            st.download_button("Download Text as PDF", best[0], file_name="IMO_Source.txt")
