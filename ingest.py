import os, re, glob, hashlib
from tqdm import tqdm
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

patterns = [
    "master_imo_all_public_part*.txt",
    "imo-rag-bot/master_imo_all_public_part*.txt",
    "imo-rag-bot/*.txt"
]
all_files = []
for pat in patterns:
    all_files.extend(glob.glob(pat))

all_files = [f for f in all_files if "summary" not in f.lower()]
all_files = sorted(list(set(all_files)))

print(f"Found {len(all_files)} part files")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="imo_hkc_12000")

seen_hashes = set()
existing_ids = set(collection.get()['ids']) if collection.count() > 0 else set()

def get_chunk_hash(text):
    return hashlib.md5(text.strip().encode()).hexdigest()[:16]

def split_file_content(content):
    parts = re.split(r'\n\s*-{3,}\s*\n', content)
    if len(parts) > 1 and len(parts) < 5000:
        return parts
    parts = re.split(r'\n===+\s*DOC', content)
    if len(parts) > 1:
        return parts
    if len(content) > 5000:
        return [content[i:i+1000] for i in range(0, len(content), 800)]
    return [content]

all_chunks = []
for filepath in tqdm(all_files, desc="Reading"):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    for c in split_file_content(content):
        c = c.strip()
        if len(c) < 100: continue
        h = get_chunk_hash(c)
        if h in seen_hashes or h in existing_ids: continue
        seen_hashes.add(h)
        all_chunks.append({"text": c, "hash": h, "source": filepath})

print(f"NEW unique chunks: {len(all_chunks)}")

BATCH = 80
for i in tqdm(range(0, len(all_chunks), BATCH), desc="Embedding"):
    batch = all_chunks[i:i+BATCH]
    texts = [b["text"] for b in batch]
    ids = [b["hash"] for b in batch]
    metas = [{"source": b["source"]} for b in batch]
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="retrieval_document"
        )
        collection.add(ids=ids, embeddings=result['embedding'], documents=texts, metadatas=metas)
    except Exception as e:
        print(f"Batch fail {e}")

print(f"DONE! Final count: {collection.count()} chunks | 1125 PDFs")
