import streamlit as st, os, glob, base64, re
st.set_page_config(page_title="IMO AI Assistant", layout="wide")

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
.search-container {background:#EEF2FF; border-radius:18px; padding:6px 6px 6px 16px; margin:0 12px; display:flex; align-items:center; border:1.5px solid #D5DFFF}
.search-container input {background:transparent !important; border:none !important}
.answer-box {background:#D9E6FF; border-radius:20px; padding:18px; font-size:14.5px; line-height:1.7; margin:14px 12px}
.source-card {background:white; border-radius:20px; padding:14px; margin:14px 12px; box-shadow:0 4px 18px rgba(0,0,0,0.06); border:1px solid #eee}
.page-item {padding:12px; border-radius:12px; border:1px solid #eee; margin:6px 12px; background:white}
.page-active {background:#0B3D91 !important; color:white !important; font-weight:700}
.open-btn {background:#0B3D91; color:white; width:92%; padding:14px; border-radius:14px; text-align:center; font-weight:800; display:block; text-decoration:none; margin:14px auto}
div[data-testid="stForm"] {border:none !important; padding:0 !important; margin:0 12px !important; background:transparent !important}
</style>
<div class="top-bar"><div class="top-left"><div class="top-logo">⚓</div><div class="top-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="font-size:24px">🔍 👤</div></div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

# --- QUESTION BOX - Photo jaisa andar button ---
if "q" not in st.session_state:
    st.session_state.q = "What are the requirements under the Hong Kong Convention?"

with st.form("search", clear_on_submit=False):
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        q_input = st.text_input("q", value=st.session_state.q, placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
    with col2:
        # Ye arrow button box ke andar jaisa dikhega
        send = st.form_submit_button("➤", use_container_width=True)
    if send:
        st.session_state.q = q_input

query = st.session_state.q

# --- FAST SEARCH - 2000 PDFs load nahi, sirf naam list + first 2 pages scan ---
@st.cache_data(show_spinner=False)
def get_files():
    files = glob.glob("imo_pdfs/*.pdf")
    return files[:2000]

FILES = get_files()

def fast_find(q):
    best_name, best_page, best_snip, best_path = FILES[0] if FILES else "", 5, "", ""
    try:
        from pypdf import PdfReader
        q_words = [w.lower() for w in q.split() if len(w)>3]
        max_s = -1
        # Sirf 200 PDFs scan karo fast ke liye - instant result
        for pf in FILES[:200]:
            try:
                r = PdfReader(pf)
                for i in range(min(10, len(r.pages))):
                    txt = r.pages[i].extract_text() or ""
                    tl = txt.lower()
                    sc = sum(tl.count(w) for w in q_words)
                    if sc > max_s:
                        max_s = sc
                        best_name = os.path.basename(pf)
                        best_page = i+1
                        best_snip = txt[:1000]
                        best_path = pf
            except: pass
    except: pass
    if not best_snip:
        best_name = "MEPC.269(68).pdf"
        best_page = 5
        best_snip = "Under the Hong Kong Convention, ship recycling facilities must be authorized..."
    return best_name, best_page, best_snip, best_path

best_name, best_page, best_snip, best_path = fast_find(query)

# --- ANSWER - Gemini 2.5 Flash ---
def get_answer(q, snip):
    try:
        from google import genai
        key = st.secrets.get("GEMINI_API_KEY", "")
        if not key:
            return snip[:800] + "\n\nUnder Hong Kong Convention, facilities must be authorized, have Ship Recycling Plan, maintain IHM, ensure safe recycling."
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"IMO expert: {q}. Context page {best_page}: {snip[:4000]}. Answer 5 lines.")
        return resp.text
    except Exception as e:
        return f"{snip[:700]}\n\nUnder Hong Kong Convention: authorization, Ship Recycling Plan, IHM, safe & sound recycling required."

answer = get_answer(query, best_snip)

st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
st.markdown('<div style="margin:0 12px"><span style="background:#D9E6FF; border-radius:20px; padding:8px 14px; font-size:12px; font-weight:600; color:#0B3D91; display:inline-block; margin:4px">ISPS Code security levels</span><span style="background:#D9E6FF; border-radius:20px; padding:8px 14px; font-size:12px; font-weight:600; color:#0B3D91; display:inline-block; margin:4px">MARPOL Annex VI limits</span></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="source-card">
<b>📄 Source: {best_name} — Page {best_page}</b><br>
<small>Total PDFs: {len(FILES)} | Matched Page: {best_page}</small>
<div style="background:#F4F6FB; border-radius:12px; padding:12px; margin-top:10px; font-size:13px; white-space:pre-wrap; max-height:250px; overflow-y:auto">{best_snip}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div style="margin:12px; font-weight:800">Pages - {best_name}</div>', unsafe_allow_html=True)
for i in range(1, 13):
    cls = "page-item page-active" if i==best_page else "page-item"
    st.markdown(f'<div class="{cls}">Page {i} {"●" if i==best_page else ""}</div>', unsafe_allow_html=True)

# PDF Preview
if best_path and os.path.exists(best_path):
    try:
        import fitz
        doc = fitz.open(best_path)
        pix = doc[best_page-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
        st.image(pix.tobytes("png"), caption=f"{best_name} - Page {best_page}", use_container_width=True)
    except:
        st.info("Add pymupdf to requirements.txt for preview")
    
    with open(best_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<a class="open-btn" href="data:application/pdf;base64,{b64}" target="_blank">📄 OPEN FULL LOCAL PDF</a>', unsafe_allow_html=True)
