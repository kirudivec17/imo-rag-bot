# rebuild_embeddings.py - Chunks aur Embeddings ko ek saath dobara banayega
# Isi parsing ko app.py bhi use karta hai, isliye mismatch khatam
import glob, re, urllib.parse
import numpy as np
from sentence_transformers import SentenceTransformer

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

print("1. Master files padh raha hu...")
chunk_files = sorted(glob.glob("master_imo_all_public_part*.txt"))
all_chunks = []
for f in chunk_files:
    txt = open(f, encoding="utf-8", errors="ignore").read()
    parts = txt.split("---CHUNK---")
    for p in parts:
        p = p.strip()
        if len(p) < 200: continue
        m = re.search(r'SOURCE:\s*(.+\.pdf)', p, re.I)
        if not m: continue
        raw_pdf = m.group(1).strip()
        pdf_name = urllib.parse.unquote(raw_pdf).split("/")[-1].split("\\")[-1].strip()
        body = clean_text(p)
        if len(body) < 200: continue
        all_chunks.append(body)

print(f"Total saaf chunks: {len(all_chunks)}")

print("2. Embeddings bana raha hu - 5-10 min lagega...")
model = SentenceTransformer('all-MiniLM-L6-v2')
# Batch me, taaki memory na phate
all_embs = []
for i in range(0, len(all_chunks), 1000):
    batch = all_chunks[i:i+1000]
    embs = model.encode(batch, convert_to_numpy=True, show_progress_bar=True, batch_size=64)
    all_embs.append(embs)
    print(f"{i+len(batch)} / {len(all_chunks)} ho gaya")

embs = np.concatenate(all_embs, axis=0)
print(f"Embeddings shape: {embs.shape} - Chunks: {len(all_chunks)}")

# Purane galat embeddings hata ke, naye sahi wale save karo
# Ek hi file me rakho taaki order bigde nahi, ya part me - par same order me
import os
for f in glob.glob("embeddings_part*.npy"):
    os.remove(f)
    print(f"Purana delete: {f}")

# 10000 ke part me save - app.py isi order me padhega
for idx, start in enumerate(range(0, len(embs), 10000)):
    part = embs[start:start+10000]
    np.save(f"embeddings_part{idx+1}.npy", part)
    print(f"Saved embeddings_part{idx+1}.npy - {len(part)} rows")

# Verify - sabse important
print("3. VERIFY - Kya chunk aur embedding match hai?")
print(f"Chunks: {len(all_chunks)} | Embeddings: {len(embs)} | Match: {len(all_chunks)==len(embs)}")
if len(all_chunks) != len(embs):
    print("❌ ABHI BHI MISMATCH HAI - COMMIT MAT KARNA")
else:
    print("✅ AB MATCH HO GAYA - Ab app sahi jawab dega")
