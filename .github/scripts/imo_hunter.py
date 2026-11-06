import os, json, requests, time, hashlib
from pathlib import Path

SERPER_KEY = os.environ.get("SERPER_API_KEY")
BASE = Path("data")
PDF_DIR = BASE / "pdfs"
CHUNK_DIR = BASE / "chunks"
MANIFEST = BASE / "manifest.json"

PDF_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

# --- 50 Searches - Multiple Tarike Se ---
QUERIES = [
    "IMO MEPC circular 2026 pdf site:imo.org",
    "IMO MSC resolution 2026 pdf site:imo.org",
    "IMO SOLAS amendment pdf site:imo.org",
    "IMO MARPOL amendment 2026 pdf",
    "IMO MEPC 83 resolution pdf",
    "IMO MSC 110 circular pdf",
    "IMO GHG strategy pdf site:imo.org",
    "IMO Ballast Water Management pdf",
    "IMO STCW amendment pdf",
    "IMO COLREG pdf site:imo.org",
    "IMO Load Lines Convention pdf",
    "IMO ISM Code pdf",
    "IMO ISPS Code pdf",
    "IMO EEDI EEXI CII pdf",
    "IMO Carbon Intensity Indicator pdf",
    "IMO FuelEU Maritime pdf",
    "IMO MEPC.377 pdf",
    "IMO MEPC.378 pdf",
    "IMO A.1185 resolution pdf",
    "IMO NAV warning pdf",
    "IMO SAR Convention pdf",
    "IMO SUA Convention pdf",
    "IMO FAL Convention pdf",
    "IMO BWM Convention pdf",
    "IMO Hong Kong Convention ship recycling pdf",
    "IMO Polar Code pdf",
    "IMO IGF Code LNG pdf",
    "IMO IMDG Code amendment pdf",
    "IMO IBC Code pdf",
    "IMO IGC Code pdf",
    "IMO Casualty Investigation Code pdf",
    "IMO LSA Code pdf",
    "IMO FSS Code pdf",
    "IMO FTP Code pdf",
    "IMO SPS Code pdf",
    "IMO MODU Code pdf",
    "IMO Grain Code pdf",
    "IMO Timber Deck Cargo Code pdf",
    "IMO CSS Code cargo stowage pdf",
    "IMO IMSBC Code pdf",
    "IMO CSS Code pdf",
    "IMO MEPC circular 2025 pdf",
    "IMO MSC circular 2025 pdf",
    "IMO Assembly resolution A. pdf",
    "IMO Council document pdf",
    "IMO Legal Committee LEG pdf",
    "IMO Technical Cooperation pdf",
    "IMO Maritime Safety Committee pdf",
    "IMO Marine Environment Protection pdf",
    "IMO 2026 new regulation shipping pdf",
]

def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"seen_urls": [], "seen_hashes": [], "pdfs": []}

def save_manifest(m):
    MANIFEST.write_text(json.dumps(m, indent=2))

def serper_search(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 10, "type": "search"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            return r.json().get("organic", [])
    except Exception as e:
        print(f"Search fail {query}: {e}")
    return []

def is_pdf_link(link):
    link = link.lower()
    return link.endswith(".pdf") or "pdf" in link

def download_pdf(url, filename):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code == 200 and len(r.content) > 5000:
            # Check PDF hai ya nahi
            if r.content[:4] != b'%PDF':
                print(f"Not PDF skip: {url}")
                return None
            path = PDF_DIR / filename
            path.write_bytes(r.content)
            # Hash - repeat rokne ke liye
            h = hashlib.md5(r.content).hexdigest()
            return str(path), h
    except Exception as e:
        print(f"Download fail {url}: {e}")
    return None

def make_chunks_and_embedding(pdf_path, pdf_name):
    # Simple Chunking - PDF text ko 1000 char ke tukdo me
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages[:30]: # Pehle 30 pages hi - size bachane ke liye
            full_text += (page.extract_text() or "") + "\n"
        chunks = []
        for i in range(0, len(full_text), 1000):
            chunk = full_text[i:i+1000].strip()
            if len(chunk) > 100:
                chunks.append({"text": chunk, "source": pdf_name, "chunk_id": i//1000})
        # Embedding baad me Cloud Server banayega - yaha sirf chunks save karte hain
        # Taaki GitHub Action heavy na ho
        out = CHUNK_DIR / f"{pdf_name.replace('.pdf','')}.json"
        out.write_text(json.dumps(chunks, indent=2)[:500000]) # Max 500KB
        print(f"Chunks done: {pdf_name} - {len(chunks)} chunks")
        return len(chunks)
    except Exception as e:
        print(f"Chunk fail {pdf_name}: {e}")
        return 0

def main():
    print(f"Starting Hunter - Total Queries: {len(QUERIES)}")
    manifest = load_manifest()
    seen_urls = set(manifest["seen_urls"])
    seen_hashes = set(manifest["seen_hashes"])
    new_count = 0

    for idx, q in enumerate(QUERIES):
        print(f"[{idx+1}/50] Searching: {q}")
        results = serper_search(q)
        for res in results:
            link = res.get("link", "")
            if not is_pdf_link(link):
                continue
            if link in seen_urls:
                continue # Repeat - skip
            # Safe filename
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in res.get("title","imo")[:60])
            fname = f"{safe}_{hashlib.md5(link.encode()).hexdigest()[:6]}.pdf"
            dl = download_pdf(link, fname)
            if dl is None:
                seen_urls.add(link) # Fail bhi hua to dobara try nahi karenge
                continue
            path, h = dl
            if h in seen_hashes:
                print(f"Duplicate PDF content skip: {fname}")
                Path(path).unlink(missing_ok=True)
                seen_urls.add(link)
                continue
            # Naya PDF mila!
            seen_urls.add(link)
            seen_hashes.add(h)
            chunk_count = make_chunks_and_embedding(path, fname)
            manifest["pdfs"].append({"file": fname, "url": link, "title": res.get("title",""), "chunks": chunk_count, "date": time.strftime("%Y-%m-%d")})
            new_count += 1
            print(f"NEW PDF Saved: {fname}")
            if new_count >= 30: # Ek run me max 30 naye PDF - 24GB bachane ke liye
                print("Limit 30 reached, stopping")
                break
        if new_count >= 30:
            break
        time.sleep(1) # Serper ko thoda rest

    manifest["seen_urls"] = list(seen_urls)
    manifest["seen_hashes"] = list(seen_hashes)
    save_manifest(manifest)
    print(f"DONE! New PDFs this run: {new_count}, Total: {len(manifest['pdfs'])}")

if __name__ == "__main__":
    main()
