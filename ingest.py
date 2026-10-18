import os
import json
import numpy as np
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PDF_FOLDER = "./imo_pdfs"  # yaha tumhare 1125 PDFs
EMBEDDING_MODEL = "text-embedding-005"
OUTPUT_EMB = "embeddings.npy"
OUTPUT_META = "metadata.json"

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

all_embeddings = []
all_metadata = []

for pdf_file in tqdm(os.listdir(PDF_FOLDER)):
    if not pdf_file.endswith(".pdf"):
        continue
    path = os.path.join(PDF_FOLDER, pdf_file)
    reader = PdfReader(path)
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text or len(text.strip()) < 50:
            continue
        
        chunks = splitter.split_text(text)
        for chunk in chunks:
            # Gemini 2.5 embedding - new SDK
            resp = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=chunk
            )
            emb = resp.embeddings[0].values
            
            all_embeddings.append(emb)
            all_metadata.append({
                "pdf_name": pdf_file,
                "page": page_num,
                "text": chunk,
                "source_label": f"IMO Resolution {pdf_file} — Page {page_num}"
            })

# Save
np.save(OUTPUT_EMB, np.array(all_embeddings))
with open(OUTPUT_META, "w", encoding="utf-8") as f:
    json.dump(all_metadata, f, ensure_ascii=False, indent=2)

print(f"Done: {len(all_embeddings)} chunks from {len(os.listdir(PDF_FOLDER))} PDFs")
