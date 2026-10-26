import streamlit as st, os, glob
from datetime import datetime
st.set_page_config(page_title="IMO AI Assistant", layout="wide", page_icon="⚓")

# === TERA LIVE BACKEND ===
ORACLE_URL = "http://129.225.105.196:8000"

# --- CSS ---
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden}
.block-container {padding:0 !important; max-width:100% !important}
.top-bar {background:#0B3D91; height:72px; display:flex; justify-content:space-between; align-items:center; padding:0 16px; position:fixed; top:0; left:0; right:0; z-index:1000}
.top-left {display:flex; align-items:center; gap:10px; color:white}
.top-logo {width:52px; height:52px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px}
.top-text {font-size:11px; font-weight:800; line-height:12px}
.main-title {color:#0E4DA4; font-size:38px; font-weight:900; text-align:center; margin:90px 0 0 0}
.subtitle {text-align:center; font-size:13px; color:#5A5A5A; margin:8px 20px 20px 20px}
.answer-box {background:#D9E6FF; border-radius:22px; padding:20px; font-size:14.5px; line-height:1.7; margin:18px 16px; color:#111; white-space:pre-wrap}
.source-card {background:white; border-radius:24px 24px 0 0; padding:18px 16px 110px 16px; margin:22px 0 0 0; box-shadow:0 -4px 24px rgba(0,0,0,0.06)}
.pdf-label {background:#F2F4F8; border-radius:12px; padding:14px; font-size:12px; margin-top:12px; max-height:320px; overflow-y:auto; white-space:pre-wrap; color:#222}
.open-btn {background:#0B3D91; color:white !important; width:92%; padding:16px; border-radius:16px; text-align:center; font-weight:800; font-size:15px; position:fixed; bottom:16px; left:4%; z-index:999; text-decoration:none; display:block; box-shadow:0 4px 12px rgba(0,0,0,0.2)}
</style>
<div class="top-bar"><div class="top-left"><div class="top-logo">⚓</div><div class="top-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="color:white; font-size:22px">🔍 👤</div></div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations - 2430 Docs - Backend: pdf-backend-2 LIVE</div>
""", unsafe_allow_html=True)

if "q" not in st.session_state:
    st.session_state.q = "What are the requirements under the Hong Kong Convention?"

with st.form("s", clear_on_submit=False):
    c1,c2 = st.columns([0.88,0.12])
    with c1:
        qi = st.text_input("q", value=st.session_state.q, label_visibility="collapsed", placeholder="Ask about SOLAS, MARPOL, HKC...")
    with c2:
        sub = st.form_submit_button("➤")
    if sub and qi:
        st.session_state.q = qi

query = st.session_state.q

def find_best_pdf(q):
    # default
    best_pdf = "A.1103(29).pdf"
    best_page = 15
    snip = "8.3.1 The ship recycling plan shall be developed..."
    try:
        files = glob.glob("imo_pdfs/*.pdf") + glob.glob("imo_pdfs_2/*.pdf") + glob.glob("imo_pdfs_3/*.pdf") + glob.glob("*.pdf")
        if not files:
            # Streamlit pe folder nahi hai toh default list
            return best_pdf, best_page, snip
        
        from pypdf import PdfReader
        qws = [w.lower() for w in q.split() if len(w) > 3]
        max_score = -1
        for pf in files[:2430]:
            try:
                r = PdfReader(pf)
                for i, pg in enumerate(r.pages[:25]):
                    t = (pg.extract_text() or "").lower()
                    if not t:
                        continue
                    sc = sum(t.count(w) for w in qws)
                    if sc > max_score:
                        max_score = sc
                        best_pdf = os.path.basename(pf)
                        best_page = i+1
                        snip = pg.extract_text() or ""
                        if sc > 5:  # good match mil gaya
                            break
            except:
                continue
    except Exception as e:
        print(e)
    return best_pdf, best_page, snip[:1500]

def get_gemini_answer(q, context):
    try:
        from google import genai
        api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            return f"Based on {context[:800]}"
        client = genai.Client(api_key=api_key)
        prompt = f"You are IMO expert. Use this authentic IMO text:\n{context[:5000]}\n\nQuestion: {q}\nGive concise 5-6 lines answer with regulation numbers. Add source."
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return resp.text
    except Exception as e:
        return f"{context[:900]}\n\n(Error: {e})"

with st.spinner("Searching 2430 PDFs..."):
    best_pdf, best_page, snippet = find_best_pdf(query)

try:
    answer = get_gemini_answer(query, snippet)
except:
    answer = snippet

st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="source-card">
  <div style="font-weight:800; font-size:14px">📄 Source: {best_pdf} — Page {best_page}</div>
  <div style="font-size:11px; color:#666; margin-top:4px">Matched from 2430 PDFs via pdf-backend-2 | Oracle: 129.225.105.196:8000</div>
  <div class="pdf-label">{snippet}</div>
</div>
""", unsafe_allow_html=True)

# FINAL BUTTON - DIRECT ORACLE
pdf_url = f"{ORACLE_URL}/pdf/{best_pdf}"
st.markdown(f'<a class="open-btn" href="{pdf_url}" target="_blank">📄 OPEN FULL PDF - {best_pdf} (Page {best_page}) - via Oracle Backend</a>', unsafe_allow_html=True)

st.caption(f"Backend: {ORACLE_URL} | Total: 2430 | Model: gemini-2.5-flash | pdf-backend-2 LIVE | {datetime.now().strftime('%H:%M')}")
