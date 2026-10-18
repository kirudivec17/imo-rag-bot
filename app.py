import streamlit as st
import os, glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEN_MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="IMO AI ASISTANT", layout="centered", page_icon="⚓")

# Photo jaisa Design
st.markdown("""
<style>
.stApp { background-color: #f6f8fb; }
.imo-header { background:#0B3D91; padding:14px 18px; display:flex; justify-content:space-between; align-items:center; margin:-1rem -1rem 2rem -1rem; }
.imo-header-left { display:flex; align-items:center; gap:10px; }
.imo-header-text { color:white; font-size:11px; font-weight:700; line-height:12px; }
.anchor-bg { position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); font-size:380px; opacity:0.04; pointer-events:none; z-index:0; }
.block-container { z-index:1; position:relative; }
.answer-box { background:white; border-radius:12px; padding:18px; border:1px solid #e5e7eb; }
.source-card { background:white; border-radius:12px; padding:14px; border:1px solid #e5e7eb; margin-bottom:12px; }
.preview { background:#f3f4f6; border-radius:8px; padding:10px; font-size:12px; color:#374151; margin:8px 0; max-height:110px; overflow-y:auto; }
</style>
<div class="anchor-bg">⚓</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <div style="background:white; width:26px; height:26px; display:flex; align-items:center; justify-content:center;">◩</div>
        <div class="imo-header-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div style="color:white;">🔍 &nbsp; 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown("### IMO AI ASISTANT")

@st.cache_resource
def load_master_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    all_chunks = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
                # Har part me 100-100 chunks hain, separator se split
                # Try common separators
                if "---CHUNK" in text or "---" in text:
                    parts = text.split("---")
                elif "\n\n\n" in text:
                    parts = text.split("\n\n\n")
                else:
                    parts = text.split("\n\n")
                
                for p in parts:
                    p = p.strip()
                    if len(p) > 100:  # chhote tukde hata do
                        all_chunks.append(p)
        except Exception as e:
            continue
    
    # summary bhi add karo
    if os.path.exists("imo_public_summary.txt"):
        try:
            with open("imo_public_summary.txt", "r", encoding="utf-8", errors="ignore") as fh:
                all_chunks.extend([x.strip() for x in fh.read().split("\n\n") if len(x.strip())>100])
        except:
            pass
    
    return all_chunks

chunks = load_master_chunks()
st.caption(f"Loaded {len(chunks)} chunks from master files")

if not chunks:
    st.error("Master files khali hain. Check karo part files me content hai ya nahi.")
    st.stop()

@st.cache_resource
def build_index(texts):
    vec = TfidfVectorizer(stop_words='english', max_features=10000)
    mat = vec.fit_transform(texts)
    return vec, mat

vectorizer, matrix = build_index(chunks)

query = st.text_input("", placeholder="Search IMO documents...", label_visibility="collapsed")

if query:
    with st.spinner("Searching 12000 chunks..."):
        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, matrix)[0]
        top = sims.argsort()[-4:][::-1]
        sources = [chunks[i] for i in top]

        ctx = "\n\n".join([f"Chunk {i}: {s[:1200]}" for i, s in enumerate(sources)])
        prompt = f"You are IMO AI ASISTANT. Answer from context only. Cite source page if mentioned.\nContext:\n{ctx}\n\nQuestion: {query}\nAnswer concisely."
        
        resp = client.models.generate_content(model=GEN_MODEL, contents=prompt)
        ans = resp.text

    st.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
    st.markdown("#### Sources")
    for i, src in enumerate(sources):
        st.markdown(f"""
        <div class="source-card">
            <b>Source:</b> Master Part {top[i]} 
            <div class="preview">{src[:800]}...</div>
        </div>
        """, unsafe_allow_html=True)
        st.button(f"OPEN FULL LOCAL PDF - Related to Chunk {i+1}", key=f"btn_{i}_{query[:5]}")
