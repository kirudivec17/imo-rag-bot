import streamlit as st, os, glob, re, base64, uuid
from pypdf import PdfReader
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="IMO AI Assistant", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility:hidden} .block-container{padding-top:0; padding-left:0; padding-right:0} .stButton button{border-radius:20px}</style>", unsafe_allow_html=True)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- TOP BAR + STYLE (Photo jaisa) ---
st.markdown("""
<style>
.top-bar {background:#0B3D91; height:68px; display:flex; justify-content:space-between; align-items:center; padding:0 16px;}
.top-left {display:flex; align-items:center; gap:10px; color:white;}
.top-left-icon {width:46px; height:46px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:24px}
.top-left-text {font-size:11px; font-weight:800; line-height:13px; letter-spacing:0.5px}
.main-title {color:#0B3D91; font-size:36px; font-weight:900; text-align:center; margin:16px 0 0 0; letter-spacing:-0.5px}
.subtitle {text-align:center; font-size:13px; color:#555; margin:4px 0 14px 0}
.answer-box {background:#DDE8FF; border-radius:18px; padding:18px 20px; font-size:14px; line-height:1.75; margin:14px 12px; border:1px solid #C5D8FF}
.pdf-card {background:white; border-radius:16px; padding:14px 16px; margin:12px; box-shadow:0 4px 18px rgba(0,0,0,0.07); border:1px solid #eee}
.page-list {background:white; border-radius:16px; padding:12px; margin:12px; border:1px solid #eee; max-height:420px; overflow-y:auto}
.page-item {padding:9px 12px; border-radius:10px; margin:4px 0; font-size:13px; display:flex; justify-content:space-between; border:1px solid #f0f0f0}
.page-active {background:#0B3D91; color:white; font-weight:700; border-color:#0B3D91}
.chip {display:inline-block; background:#EEF3FF; border:1px solid #D0DEFF; padding:6px 12px; border-radius:20px; font-size:12px; margin:4px}
</style>
<div class="top-bar"><div class="top-left"><div class="top-left-icon">⚓</div><div class="top-left-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="color:white; font-size:22px">🔍&nbsp;&nbsp;👤</div></div>
<div class="main-title">IMO AI ASSISTANT</div><div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

# --- LOAD PDFs (Low MB - sirf first 8 pages) ---
@st.cache_data(show_spinner=False)
def load_pdfs():
    docs, texts, names = {}, [], []
    pdf_files = glob.glob("imo_pdfs/*.pdf") + glob.glob("**/imo_pdfs/*.pdf", recursive=True)
    pdf_files = list(set(pdf_files))[:2000]
    for p in pdf_files:
        try:
            name = os.path.basename(p)
            r = PdfReader(p)
            # First 8 pages only - MB bachega
            txt_pages = []
            for pg in r.pages[:8]:
                txt_pages.append(pg.extract_text() or "")
            full_txt = "\n".join(txt_pages)[:12000]
            if len(full_txt) > 150:
                docs[name] = {"path": p, "text": full_txt, "pages_text": txt_pages, "total": len(r.pages)}
                texts.append(full_txt)
                names.append(name)
        except: pass
    return docs, texts, names

docs, texts, names = load_pdfs()

@st.cache_resource(show_spinner=False)
def build_idx(lst):
    v = TfidfVectorizer(stop_words='english', max_features=5000)
    return v, v.fit_transform(lst)

if texts:
    vectorizer, matrix = build_idx(texts)

def smart_search(q, k=1):
    if not texts: return []
    q_vec = vectorizer.transform([q])
    sims = cosine_similarity(q_vec, matrix).flatten()
    top = np.argsort(sims)[-k:][::-1]
    return [(names[i], texts[i], sims[i]) for i in top]

def find_best_page(pages_text, query):
    q_words = query.lower().split()
    best_idx, best_score = 0, -1
    for idx, pt in enumerate(pages_text):
        low = pt.lower()
        score = sum(low.count(w) for w in q_words if len(w)>3)
        if score > best_score:
            best_score, best_idx = score, idx
    return best_idx # 0-based

# --- SEARCH BOX ---
c1, c2 = st.columns([0.85, 0.15])
with c1:
    query = st.text_input("q", placeholder="What are requirements under Hong Kong Convention?", label_visibility="collapsed")
with c2:
    go = st.button("➤", use_container_width=True)

# Suggestions chips (photo jaisa)
st.markdown("<div style='margin:2px 14px'><span class='chip'>What is the ISPS Code?</span> <span class='chip'>What are MARPOL Annex VI requirements?</span> <span class='chip'>What is Ballast Water Management?</span></div>", unsafe_allow_html=True)

if query or go:
    if not query: query = "What are requirements under Hong Kong Convention?"
    results = smart_search(query, k=1)
    if results:
        top_name, top_text, score = results[0]
        info = docs.get(top_name)
        best_page_idx = find_best_page(info["pages_text"], query) if info else 0
        
        # --- GEMINI ANSWER ---
        context = info["pages_text"][best_page_idx][:6000] if info else top_text[:6000]
        prompt = f"You are IMO expert. Use context if relevant else own IMO knowledge. Mention source {top_name} Page {best_page_idx+1}. Never say 'no information'. Context: {context}. Question: {query}"
        try:
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            ans = resp.text
        except Exception as e:
            ans = f"Based on {top_name} Page {best_page_idx+1}: {context[:800]}..."

        st.markdown(f"<div class='answer-box'>{ans}</div>", unsafe_allow_html=True)

        # --- SOURCE + PAGES + PDF (Photo jaisa) ---
        if info and os.path.exists(info["path"]):
            st.markdown(f"<div class='pdf-card'><b>📄 Source: {top_name} — Page {best_page_idx+1}</b><br><small>Relevance: {score:.2f} | Total Pages: {info['total']} | Matched in Page {best_page_idx+1}</small><div style='margin-top:8px; background:#F4F5F7; border-radius:12px; padding:12px; font-size:12.5px; white-space:pre-wrap; line-height:1.5; max-height:220px; overflow-y:auto'>{info['pages_text'][best_page_idx][:1200]}</div></div>", unsafe_allow_html=True)

            left, right = st.columns([1, 1.6])
            with left:
                st.markdown("<div class='page-list'><b>Pages</b></div>", unsafe_allow_html=True)
                html = "<div class='page-list'>"
                for i in range(min(12, info["total"])):
                    cls = "page-item page-active" if i==best_page_idx else "page-item"
                    dot = "●" if i==best_page_idx else ""
                    html += f"<div class='{cls}'><span>Page {i+1}</span><span>{dot}</span></div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
            
            with right:
                # PDF image preview - PyMuPDF try karo, nahi to text dikhao
                try:
                    import fitz
                    doc = fitz.open(info["path"])
                    page = doc[best_page_idx]
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3))
                    st.image(pix.tobytes("png"), caption=f"{top_name} - Page {best_page_idx+1}", use_container_width=True)
                except:
                    st.info("PDF preview will show after adding pymupdf in requirements.txt")

            # Open + Download
            with open(info["path"], "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="background:#0B3D91; color:white; padding:12px; border-radius:12px; display:block; text-align:center; text-decoration:none; font-weight:700; margin:8px 12px">📄 OPEN FULL PDF IN NEW TAB</a>', unsafe_allow_html=True)
                st.download_button(f"⬇️ DOWNLOAD {top_name}", data, file_name=top_name, mime="application/pdf", key=f"dl_{top_name}_{uuid.uuid4()}", use_container_width=True)
    else:
        st.warning("No PDFs found in imo_pdfs folder")

st.caption(f"IMO Assistant | {len(docs)} PDFs loaded | Low-MB Mode | No GitHub Actions used")
