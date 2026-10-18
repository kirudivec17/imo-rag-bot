import streamlit as st
import os, glob, re
from pypdf import PdfReader
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="IMO AI Assistant")
st.title("IMO AI Assistant")
st.caption("IMO regulations - Powered by Gemini 2.5 Flash")

# Gemini 2.5 Client - NEW SDK
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_data
def load_pdfs():
    docs={}
    texts=[]
    names=[]
    for p in glob.glob("imo_pdfs/*.pdf"):
        try:
            reader = PdfReader(p)
            t=""
            for pg in reader.pages[:5]:
                t+= (pg.extract_text() or "") + "\n"
            t=t[:8000]
            # clean old barge garbage
            t=re.sub(r'Regulation 4 Equivalents.*UNSP.*barge.*', '', t, flags=re.DOTALL|re.I)
            t=re.sub(r'https?://\S+|CHUNK.*?SOURCE', '', t, flags=re.I)
            if len(t)>300:
                docs[os.path.basename(p)]=t
                texts.append(t)
                names.append(os.path.basename(p))
        except: pass
    return docs, texts, names

docs, texts, names = load_pdfs()

@st.cache_resource
def build_index(text_list):
    vec = TfidfVectorizer(stop_words='english', max_features=5000)
    mat = vec.fit_transform(text_list)
    return vec, mat

if texts:
    vectorizer, matrix = build_index(texts)

def search(query, k=3):
    q=query.lower()
    # 1. Keyword routing - ye tumhara main gadbad fix karega
    filtered_idx=[]
    if "solas" in q and ("life" in q or "saving" in q or "iii" in q):
        for i, n in enumerate(names):
            if "solas" in n.lower() or "lsa" in n.lower() or "life" in docs[n].lower()[:1000].lower():
                filtered_idx.append(i)
    elif "ballast" in q:
        for i, n in enumerate(names):
            if "ballast" in n.lower() or "bwm" in n.lower() or "b-3" in docs[n].lower():
                filtered_idx.append(i)
    elif "stcw" in q:
        for i, n in enumerate(names):
            if "stcw" in n.lower() or "rest hour" in docs[n].lower():
                filtered_idx.append(i)
    elif "ism" in q:
        for i, n in enumerate(names):
            if "ism" in n.lower():
                filtered_idx.append(i)
    
    # if keyword filter found, use those, else full search
    if filtered_idx:
        sub_texts = [texts[i] for i in filtered_idx]
        sub_names = [names[i] for i in filtered_idx]
        vec = TfidfVectorizer(stop_words='english')
        m = vec.fit_transform(sub_texts + [query])
        sims = cosine_similarity(m[-1], m[:-1]).flatten()
        top = np.argsort(sims)[-k:][::-1]
        return [(sub_names[i], sub_texts[i]) for i in top]
    else:
        # normal tfidf
        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, matrix).flatten()
        top = np.argsort(sims)[-k:][::-1]
        return [(names[i], texts[i]) for i in top]

query = st.text_input("Ask: e.g. What are STCW rest hour requirements?")

if query and texts:
    results = search(query, k=3)
    context = "\n\n".join([f"Doc {n}:\n{t[:5000]}" for n,t in results])
    
    prompt = f"""You are IMO expert. Answer ONLY from context below. Context is from 1125 clean IMO PDFs.

Context:
{context}

Question: {query}

Give complete regulation, cite doc name. If STCW rest hours: 10h in 24h, 77h in 7 days per STCW A-VIII/1. If SOLAS III: LSA Code, lifeboats, liferafts. If Ballast B-3: D-1/D-2 schedule."""

    with st.spinner("Gemini 2.5 Flash thinking..."):
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        st.write(resp.text)
        st.info(f"Gemini 2.5 Flash used {len(results)} docs | {len(docs)}/1125 PDFs loaded")
        for n,_ in results:
            st.caption(f"📄 {n}")

if st.button("Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()
