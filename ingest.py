import os, fitz, chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

CHROMA_PATH = "./chroma_db"
PDF_FOLDER = "./imo_pdfs"  # tumhare 1125 PDFs ka folder
EMBEDDING_MODEL = "models/text-embedding-005"  # Gemini 2.5 latest

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection("imo_docs")

for file in os.listdir(PDF_FOLDER):
    if not file.endswith(".pdf"): continue
    path = os.path.join(PDF_FOLDER, file)
    doc = fitz.open(path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if len(text) < 50: continue
        
        emb = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )["embedding"]
        
        collection.add(
            ids=[f"{file}_{page_num}"],
            embeddings=[emb],
            documents=[text],
            metadatas=[{
                "file_name": file,
                "page_number": page_num + 1,
                "full_path": path,
                "page_preview": text[:200]
            }]
        )
        print(f"Added {file} Page {page_num+1}")

print("Done - 1125 PDFs indexed with Gemini 2.5 embedding 005")
