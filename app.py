import streamlit as st
import os, glob, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from google import genai

# --- IMO LEVEL UI ---
st.set_page_config(page_title="HKC Intelligence Platform", page_icon="⚓", layout="wide")

st.markdown("""
<style>
.main-header { background: #0A4A7A; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
.citation-box { background: #E8F0FE; border-left: 4px solid #0A4A7A; padding: 10px; margin: 8px 0; border-radius: 4px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h2 style="margin:0">⚓ HKC & Ship Recycling Intelligence Platform</h2><p style="margin:0">Unofficial — 788 public IMO Docs | For HKC Implementation | IMO Level Product</p></div>', unsafe_allow_html=True)
st.caption("⚠️ Not an official IMO product - For official text refer to imo.org")

@st.cache_data
def load_all_chunks():
    chunks = []
    files = glob.glob("master_imo_all_public_part*.txt")
    if not files:
        files = glob.glob("**/master_imo_all_public_part*.txt", recursive=True)
    for f in sorted(files):
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                parts = re.split(r'---CHUNK---|---\n', content)
                for p in parts:
                    p = p.strip()
                    if len(p) > 200:
                        chunks.append(p)
        except:
            pass
    return chunks

chunks = load_all_chunks()

if not chunks:
    st.error("master_imo_all_public_part*.txt files not found! Root me daalo.")
    st.stop()

@st.cache_resource
def build_index(chunks_list):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf = vectorizer.fit_transform(chunks_list)
    return vectorizer, tfidf

vectorizer, tfidf_matrix = build_index(chunks)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📚 IMO Document Library")
    st.success(f"{len(chunks)} Chunks | 788 PDFs")
    st.markdown("**Hong Kong Convention**\n\n**MEPC.196(62) IHM**\n\n**MEPC.379(80) Cybutryne**\n\n**IHM Guidelines**")
    st.divider()
    st.markdown("REFERENCE:\n- SRP Template\n- Safe for Recycling Cert\n- Waste Management")

# --- API KEY ---
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Enter GEMINI_API_KEY (Streamlit Secrets me daalo)", type="password")

if not api_key:
    st.warning("Add GEMINI_API_KEY in Streamlit Secrets")
    st.stop()

client = genai.Client(api_key=api_key)

# --- MAIN ---
st.markdown("### 🤖 AI Assistant — Chat & Analysis")
st.caption("Powered by 788 Public IMO Docs | Citation Based")

query = st.text_input("Ask about HKC...", placeholder="What is Cybutryne limit under HKC? How to prepare SRP?")

if query:
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, tfidf_matrix).flatten()
    top_idx = np.argsort(scores)[-3:][::-1]
    top_chunks = [chunks[i] for i in top_idx]
    context = "\n\n---\n\n".join(top_chunks)

    prompt = f"""You are HKC & Ship Recycling Expert for IMO.
Use ONLY below context from 788 public IMO docs.
Always give citation like Source: MEPC.xxx
If not found, say not found in public docs.

Context:
{context}

Question: {query}

Answer with clear summary, limits, requirements, and Sources & Citations."""

    with st.spinner(f"Searching {len(chunks)} chunks from 788 PDFs..."):
        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            st.markdown(response.text)

            st.divider()
            st.markdown("#### 📑 Sources & Citations (IMO Level)")
            for i, idx in enumerate(top_idx):
                preview = chunks[idx][:200].replace('\n',' ')
                st.markdown(f'<div class="citation-box"><b>Source {i+1} (Relevance {scores[idx]:.2f}):</b><br>{preview}...</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Check GEMINI_API_KEY in Manage App > Settings > Secrets")

# --- FOOTER ---
st.divider()
st.caption(f"Built for IMO Delegates & Alang Recyclers | {len(chunks)} Chunks | 788 Public IMO Docs | Legal | Not Official IMO Product")
