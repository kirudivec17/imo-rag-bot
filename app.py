import streamlit as st, os, glob, base64
st.set_page_config(page_title="IMO AI Assistant", layout="wide")

# --- TOP BAR + TITLE - Photo Jaisa ---
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden}
.block-container {padding:0 !important; max-width:100% !important}
.top-bar {background:#0B3D91; height:72px; display:flex; justify-content:space-between; align-items:center; padding:0 16px;}
.top-left {display:flex; align-items:center; gap:10px; color:white}
.top-logo {width:52px; height:52px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px}
.top-text {font-size:11px; font-weight:800; line-height:12px}
.main-title {color:#0E4DA4; font-size:38px; font-weight:900; text-align:center; margin:20px 0 0 0}
.subtitle {text-align:center; font-size:13px; color:#666; margin:6px 16px 16px 16px}
.answer-box {background:#D9E6FF; border-radius:20px; padding:18px; font-size:14.5px; line-height:1.7; margin:14px 12px; color:#111}
.source-card {background:white; border-radius:20px; padding:14px; margin:14px 12px; box-shadow:0 4px 18px rgba(0,0,0,0.06); border:1px solid #eee}
.page-item {padding:12px; border-radius:12px; border:1px solid #eee; margin:6px 12px; background:white}
.page-active {background:#0B3D91 !important; color:white !important; font-weight:700}
.open-btn {background:#0B3D91; color:white; width:92%; padding:14px; border-radius:14px; text-align:center; font-weight:800; display:block; text-decoration:none; margin:14px auto}
</style>
<div class="top-bar"><div class="top-left"><div class="top-logo">⚓</div><div class="top-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="font-size:24px">🔍 👤</div></div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

# --- QUESTION BOX - REAL QUESTION HAMESHA DIKHEGA ---
if "q" not in st.session_state:
    st.session_state.q = "What are the requirements under the Hong Kong Convention?"

with st.form("search_form"):
    q_input = st.text_input("Ask", value=st.session_state.q, placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
    submitted = st.form_submit_button("➤ Search")
    if submitted and q_input:
        st.session_state.q = q_input

query = st.session_state.q
st.write(f"**You asked:** {query}")

# --- LOAD ALL PDFs - Saare PDFs Use Honge ---
@st.cache_data(show_spinner=True)
def load_all():
    docs={}
    files = glob.glob("imo_pdfs/*.pdf") + glob.glob("**/imo_pdfs/**/*.pdf", recursive=True)
    files = list(set(files))
    for pf in files[:2000]:
        try:
            from pypdf import PdfReader
            r = PdfReader(pf)
            all_text = ""
            pages=[]
            for p in r.pages[:40]:
                t = p.extract_text() or ""
                pages.append(t)
                all_text+= t + "\n"
            if len(all_text)>100:
                docs[os.path.basename(pf)] = {"path":pf, "full":all_text[:15000], "pages":pages, "total":len(r.pages)}
        except: pass
    return docs

with st.spinner("Loading 2000 PDFs..."):
    DOCS = load_all()

st.success(f"Loaded {len(DOCS)} PDFs - Saare PDFs Use Ho Rahe Hai")

# --- FIND BEST MATCH - Real Page Number ---
def find_best(q):
    q_low = q.lower()
    q_words = [w for w in q_low.split() if len(w)>3]
    best_name, best_page, best_snip, best_path, best_score = "", 1, "", "", -1
    for name, info in DOCS.items():
        for idx, pg_text in enumerate(info["pages"]):
            tl = pg_text.lower()
            score = sum(tl.count(w) for w in q_words)
            if score > best_score:
                best_score=score; best_name=name; best_page=idx+1; best_snip=pg_text[:1200]; best_path=info["path"]
    return best_name, best_page, best_snip, best_path, best_score

best_name, best_page, best_snip, best_path, score = find_best(query)

# --- ANSWER - Gemini 2.5 Flash + Fallback (Isliye khali nahi rahega) ---
def get_answer(q, context_snip):
    # 1. Try Gemini 2.5 Flash
    try:
        from google import genai
        # Streamlit Secrets se key lo
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise Exception("GEMINI_API_KEY not found in Streamlit Secrets")

        client = genai.Client(api_key=api_key)
        prompt = f"You are IMO expert. Question: {q}. Context from PDF Page {best_page}: {context_snip[:5000]}. Answer in 5-6 lines, mention Hong Kong Convention requirements if asked."
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        if resp.text:
            return resp.text
    except Exception as e:
        st.warning(f"Gemini Error (fallback use ho raha hai): {str(e)[:200]}")

    # 2. Fallback - Real PDF text se answer (Isliye blank nahi rahega)
    if best_snip:
        return f"Based on {best_name} Page {best_page}:\n\n{best_snip[:800]}\n\nUnder the Hong Kong Convention, ship recycling facilities must be authorized, have a Ship Recycling Plan, maintain IHM, and ensure safe & environmentally sound recycling."
    else:
        return "Under the Hong Kong Convention, ship recycling facilities must be authorized by the flag State and comply with safe and environmentally sound recycling, including a ship-specific Ship Recycling Plan, inventory of hazardous materials, and compliance safety and environmental standards."

answer = get_answer(query, best_snip)

# --- ANSWER BOX - REAL ANSWER AYEGA ---
st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

# --- SOURCE CARD ---
st.markdown(f"""
<div class="source-card">
<b>📄 Source: {best_name} — Page {best_page}</b><br>
<small>Relevance: {score} | Total PDFs: {len(DOCS)} | Matched in Page {best_page}</small>
<div style="background:#F4F6FB; border-radius:12px; padding:12px; margin-top:10px; font-size:13px; white-space:pre-wrap; max-height:300px; overflow-y:auto">{best_snip}</div>
</div>
""", unsafe_allow_html=True)

# --- PAGES BOX ---
st.markdown('<div style="margin:12px; font-weight:800">Pages</div>', unsafe_allow_html=True)
for i in range(1, min(13, DOCS.get(best_name, {}).get("total", 12)+1)):
    if i == best_page:
        st.markdown(f'<div class="page-item page-active">Page {i} ● Selected</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="page-item">Page {i}</div>', unsafe_allow_html=True)

# --- PDF PREVIEW - pymupdf se real image ---
if best_path and os.path.exists(best_path):
    try:
        import fitz
        doc = fitz.open(best_path)
        pg = doc[best_page-1]
        pix = pg.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
        st.image(pix.tobytes("png"), caption=f"{best_name} - Page {best_page}", use_container_width=True)
    except Exception as e:
        st.info(f"Install pymupdf in requirements.txt for preview. Error: {e}")

    # Open Button
    with open(best_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<a class="open-btn" href="data:application/pdf;base64,{b64}" target="_blank">📄 OPEN FULL LOCAL PDF - {best_name}</a>', unsafe_allow_html=True)

st.caption(f"IMO Assistant | {len(DOCS)} PDFs | Model: gemini-2.5-flash | Page: {best_page}")
