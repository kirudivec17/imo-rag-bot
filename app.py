import streamlit as st, os, glob, base64, requests
st.set_page_config(page_title="IMO AI Assistant", layout="wide")

# TERA ORACLE BACKEND-2 IP - yaha daal
ORACLE_BACKEND_URL = "http://129.225.105.196:8000"  # agar backend-2 ka IP alag hai toh yaha change kar

st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden}
.block-container {padding:0 !important; max-width:100% !important}
.top-bar {background:#0B3D91; height:72px; display:flex; justify-content:space-between; align-items:center; padding:0 16px;}
.top-left {display:flex; align-items:center; gap:10px; color:white}
.top-logo {width:52px; height:52px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px}
.top-text {font-size:11px; font-weight:800; line-height:12px}
.main-title {color:#0E4DA4; font-size:38px; font-weight:900; text-align:center; margin:24px 0 0 0}
.subtitle {text-align:center; font-size:14px; color:#5A5A5A; margin:8px 20px 20px 20px}
.answer-box {background:#D9E6FF; border-radius:22px; padding:20px; font-size:14.5px; line-height:1.7; margin:18px 16px; color:#111}
.chip-row {display:flex; gap:10px; margin:0 16px}
.chip {background:#D9E6FF; border-radius:22px; padding:10px 16px; font-size:13px; font-weight:600; color:#0B3D91}
.source-card {background:white; border-radius:24px 24px 0 0; padding:18px 16px 100px 16px; margin:22px 0 0 0; box-shadow:0 -4px 24px rgba(0,0,0,0.06)}
.pdf-label {background:#F2F4F8; border-radius:12px; padding:14px; font-size:13px; margin-top:12px; max-height:320px; overflow-y:auto; white-space:pre-wrap}
.open-btn {background:#0B3D91; color:white; width:92%; padding:16px; border-radius:16px; text-align:center; font-weight:800; font-size:16px; position:fixed; bottom:16px; left:4%; z-index:999; text-decoration:none; display:block}
</style>
<div class="top-bar"><div class="top-left"><div class="top-logo">⚓</div><div class="top-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="font-size:26px">🔍 👤</div></div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety - 2430 Docs</div>
""", unsafe_allow_html=True)

if "q" not in st.session_state:
    st.session_state.q = "What are the requirements under the Hong Kong Convention?"

with st.form("s", clear_on_submit=False):
    c1,c2 = st.columns([0.85,0.15])
    with c1: qi = st.text_input("q", value=st.session_state.q, label_visibility="collapsed")
    with c2: sub = st.form_submit_button("➤")
    if sub: st.session_state.q = qi
query = st.session_state.q

# --- 3 FOLDER SE 2430 PDFs ---
def get_real():
    best_pdf,best_page,snip,best_path = "IMO Resolution MEPC.269(68)",15,"8.3.1 The ship recycling plan shall be developed.",""
    try:
        from pypdf import PdfReader
        # YAHI FIX HAI - 3 FOLDER
        files = glob.glob("imo_pdfs/*.pdf") + glob.glob("imo_pdfs_2/*.pdf") + glob.glob("imo_pdfs_3/*.pdf")
        qws = [w.lower() for w in query.split() if len(w)>3]
        ms=-1
        for pf in files[:2430]:
            try:
                r=PdfReader(pf)
                for i,pg in enumerate(r.pages[:30]):
                    t=(pg.extract_text() or "").lower()
                    sc=sum(t.count(w) for w in qws)
                    if sc>ms:
                        ms=sc; best_pdf=os.path.basename(pf); best_page=i+1; snip=(pg.extract_text() or "")[:1200]; best_path=pf
            except: pass
    except: pass
    return best_pdf,best_page,snip,best_path

def get_ans(q, context):
    from google import genai
    key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"You are IMO expert. Use context: {context[:6000]}. Question: {q}. Answer 6-7 lines with HKC requirements.")
    return resp.text

best_pdf,best_page,snip,best_path = get_real()
try:
    ans = get_ans(query, snip)
except Exception as e:
    ans = f"Based on {best_pdf} Page {best_page}: {snip[:800]}"

st.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
st.markdown('<div class="chip-row"><div class="chip">ISPS Code security levels</div><div class="chip">MARPOL Annex VI limits</div></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="source-card">
  <div style="font-weight:800">📄 Source: {best_pdf} — Page {best_page}</div>
  <div style="font-size:12px; color:#666; margin-top:6px">Matched from 2430 PDFs | HKC - Ship Recycling Plan</div>
  <div class="pdf-label">{snip}</div>
</div>
""", unsafe_allow_html=True)

# --- ORACLE BACKEND SE OPEN ---
# Agar Oracle backend chal raha hai toh waha se open hoga, nahi toh base64 fallback
oracle_pdf_url = f"{ORACLE_BACKEND_URL}/pdf/{best_pdf}"
try:
    # check backend alive
    requests.get(ORACLE_BACKEND_URL, timeout=2)
    st.markdown(f'<a class="open-btn" href="{oracle_pdf_url}" target="_blank">📄 OPEN FULL PDF - {best_pdf} (Page {best_page}) via Oracle</a>', unsafe_allow_html=True)
except:
    if best_path and os.path.exists(best_path):
        with open(best_path,"rb") as f:
            b64=base64.b64encode(f.read()).decode()
        st.markdown(f'<a class="open-btn" href="data:application/pdf;base64,{b64}" target="_blank">📄 OPEN FULL LOCAL PDF - {best_pdf}</a>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="open-btn">📄 OPEN FULL LOCAL PDF</div>', unsafe_allow_html=True)

st.caption(f"2430 PDFs | Oracle: {ORACLE_BACKEND_URL} | Model: gemini-2.5-flash")
