import glob, re, urllib.parse
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_all():
    def clean_text(raw):
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
        txt = re.sub(r'-\s+', '', txt)
        return txt.strip()

    # 1. Chunks - rebuild wale order me hi
    all_chunks, all_sources = [], []
    for f in sorted(glob.glob("master_imo_all_public_part*.txt")):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        for p in txt.split("---CHUNK---"):
            p = p.strip()
            if len(p) < 200: continue
            m = re.search(r'SOURCE:\s*(.+\.pdf)', p, re.I)
            if not m: continue
            pdf = urllib.parse.unquote(m.group(1).strip()).split("/")[-1].split("\\")[-1].strip()
            body = clean_text(p)
            if len(body) < 200: continue
            all_chunks.append(body)
            all_sources.append(pdf)

    # 2. Embeddings - part1 se part10 tak, isi order me
    embs = np.concatenate([np.load(f) for f in sorted(glob.glob("embeddings_part*.npy"), key=lambda x: int(re.search(r'part(\d+)', x).group(1)))], axis=0)
    # Normalize - cosine ke liye
    embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)

    model = SentenceTransformer('all-MiniLM-L6-v2')
    return all_chunks, all_sources, embs, model

def search_real(query, top_k=5):
    chunks, sources, embs, model = load_all()
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = embs @ q
    idx = np.argsort(scores)[::-1][:top_k]
    return [(chunks[i], sources[i], float(scores[i])) for i in idx]
