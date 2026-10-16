import streamlit as st
import os, glob, re
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- PAGE CONFIG - IMO LEVEL ---
st.set_page_config(
    page_title="HKC Intelligence Platform",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- IMO BLUE THEME CSS ---
st.markdown("""
<style>
   .main-header { background: #0A4A7A; color: white; padding: 1rem; border-radius: 8px; }
   .citation-box { background: #E8F0FE; border-left: 4px solid #0A4A7A; padding: 10px; margin: 10px 0; border-radius: 4px; }
   .doc-card { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
   .unofficial-badge { background: #FFF3CD; color: #856404; padding: 5px 10px; border-radius: 12px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <h2 style="margin:0">⚓ HKC & Ship Recycling Intelligence Platform</h2>
    <p style="margin:0; opacity:0.9">Unofficial — Built using 788 public IMO Resolutions | For HKC Implementation</p>
</div>
""", unsafe_allow_html=True)
st.markdown('<span class="unofficial-badge">⚠️ Not an official IMO product - For official text refer to imo.org</span>', unsafe_allow_html=True)

# --- LOAD YOUR 10 PART FILES (788 PDFs) ---
@st.cache_data
def load_all_chunks():
    chunks = []
    # tumhare files root me hai
    files = glob.glob("master_imo_all_public_part*.txt")
    if not files:
        files = glob.glob("**/master_imo_all_public_part*.txt", recursive=True)

    for f in sorted(files):
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                # Split by CHUNK or double newline
                parts = re.split(r'---CHUNK---|---\n', content)
                for p in parts:
                    p = p.strip()
                    if len(p) > 200: # Only meaningful chunks
                        chunks.append(p)
        except: pass
    return chunks

@st.cache_resource
def build_index(chunks):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf = vectorizer.fit_transform(chunks)
    return vectorizer, tfidf

# --- SIDEBAR - IMO DOCUMENT LIBRARY ---
with st.sidebar:
    st.markdown("### 📚 IMO Document Library")
    st.text_input("Search documents...", placeholder="MEPC.196, IHM, SRP...")

    st.markdown("**Hong Kong Convention**")
    st.caption("Current • 2023 • 17 Core Docs")
    st.markdown("**MEPC Resolutions**")
    st.caption("MEPC.196(62), MEPC.210(63), MEPC.379(80)")
    st.markdown("**IHM Guidelines**")
    st.caption("Inventory v2021 • Cybutryne 1000 μg/kg")

    st.divider()
    st.markdown("**REFERENCE MATERIALS**")
    st.markdown("- 📄 SRP Template")
    st.markdown("- 📄 Safe for Recycling Certificate")
    st.markdown("- 📄 Waste Management Guidelines")

    st.divider()
    status = st.empty()

# --- LOAD ---
chunks = load_all_chunks()
if not chunks:
    st.error("No master_imo_*.txt files found! Check folder.")
    st.stop()

vectorizer, tfidf_matrix = build_index(chunks)
status = f"✅ {len(chunks)} Chunks from 788 PDFs Loaded"

with st.sidebar:
    st.success(f"All documents synced • {len(chunks)} chunks")
    st.info("Updated: 788 Public IMO Docs")

# --- MAIN LAYOUT ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🤖 AI Assistant — Chat & Analysis")
    st.caption("Powered by IMO Knowledge Base (788 PDFs)")

    # Gemini Setup
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter GEMINI API KEY", type="password")

    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        query = st.text_input("Ask about HKC...", placeholder="What is Cybutryne limit under HKC? How to prepare SRP?")

        if query:
            # TF-IDF Search - Best 3 chunks
            q_vec = vectorizer.transform([query])
            scores = cosine_similarity(q_vec, tfidf_matrix).flatten()
            top_idx = np.argsort(scores)[-3:][::-1]
            top_chunks = [chunks[i] for i in top_idx]

            context = "\n\n---\n\n".join(top_chunks)

            prompt = f"""You are HKC & Ship Recycling Expert for IMO delegates.
            Use ONLY below context from 788 public IMO docs to answer.
            Always give citation like Source: MEPC.xxx.
            If answer not in context, say not found in public docs.

            Context:
            {context}

            Question: {query}

            Answer with:
            1. Clear summary
            2. Key limits/requirements
            3. Sources & Citations
            """

            with st.spinner("Searching 788 PDFs..."):
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)

                    st.divider()
                    st.markdown("#### 📑 Sources & Citations")
                    for i, idx in enumerate(top_idx):
                        # Extract source name
                        src = chunks[idx][:120].replace('\n',' ')
                        st.markdown(f'<div class="citation-box"><b>Source {i+1}:</b> {src}...<br><small>Relevance: {scores[idx]:.2f}</small></div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Add GEMINI_API_KEY in Streamlit Secrets")

with col2:
    st.markdown("### 📄 Document Preview & Regulation Details")
    tab1, tab2 = st.tabs(["Preview", "Regulation Details"])

    with tab1:
        st.info("**MEPC.196(62) — Guidelines for IHM**\n\nAdopted: 15 July 2011 • Status: In Force")
        st.markdown("**Cybutryne — Regulation Details**")
        st.markdown("""
        - Substance: Cybutryne (Irgarol-1051)
        - CAS No.: 28159-98-0
        - Limit: 1000 μg/kg (1.0 mg/kg)
        - Source: MEPC.379(80)
        """)

    with tab2:
        st.markdown("**SRP Checklist — Cybutryne Compliance**")
        st.checkbox("Cybutryne identified in IHM Part I", value=True)
        st.checkbox("Concentration quantified in sampling report", value=True)
        st.checkbox("Management plan in SRP Section 6.3", value=True)
        st.checkbox("Verification by approved surveyor pending")
        st.warning("Action Required: Ensure sampling report attached to Part I before Recycling Plan approval.")
        st.button("📥 Download PDF Report")

# --- FOOTER ---
st.divider()
st.caption("Built for IMO Delegates & Ship Recyclers | 788 Public IMO Docs | 100% Legal | Not Official IMO Product")
