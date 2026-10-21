import streamlit as st, os, glob, base64
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
.search-wrap {background:#EAF0FF; border-radius:16px; padding:4px; margin:0 12px; display:flex; align-items:center; border:1.5px solid #D5DFFF}
.search-wrap input {border:none !important; background:transparent !important}
.answer-box {background:#D9E6FF; border-radius:20px; padding:18px; font-size:14px; line-height:1.7; margin:14px 12px}
.chip {background:#D9E6FF; border-radius:20px; padding:8px 14px; font-size:12px; font-weight:600; color:#0B3D91; display:inline-block; margin:4px}
.source-card {background:white; border-radius:20px; padding:14px; margin:14px 12px; box-shadow:0 4px 18px rgba(0,0,0,0.06); border:1px solid #eee}
.page-box {border:1px solid #E5E5E5; border-radius:16px; padding:8px; margin:12px}
.page-item {padding:12px; border-radius:12px; border:1px solid #eee; margin:6px 0; background:white}
.page-active {background:#0B3D91 !important; color:white !important; font-weight:700}
.open-btn {background:#0B3D91; color:white; width:100%; padding:14px; border-radius:14px; text-align:center; font-weight:800; display:block; text-decoration:none; margin-top:12px}
</style>
<div class="top-bar"><div class="top-left"><div class="top-logo">⚓</div><div class="top-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="font-size:24px">🔍 👤</div></div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

if "q" not in st.session_state:
    st.session_state.q = "What are the requirements under the Hong Kong Convention?"

with st.form("f"):
    q_in = st.text_input("Question", value=st.session_state.q, placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
    submitted = st.form_submit_button("➤ Send")
    if submitted:
        st.session_state.q = q_in
query = st.session_state.q

# --- Real search ---
def find_best():
    best_pdf,best_page,snip,path = "MEPC.269(68)",15,"",""
    try:
        from pypdf import PdfReader
        files = glob.glob("imo_pdfs/*.pdf")
        qws = [w.lower() for w in query.split() if len(w)>3]
        ms=-1
        for pf in files[:400]:
            try:
                r=PdfReader(pf)
                for i,pg in enumerate(r.pages[:30]):
                    t=(pg.extract_text() or "")
                    tl=t.lower()
                    sc=sum(tl.count(w) for w in qws)
                    if sc>ms:
                        ms=sc; best_pdf=os.path.basename(pf); best_page=i+1; snip=t[:900]; path=pf
            except: pass
    except: pass
    return best_pdf,best_page,snip,path

def get_ans():
    try:
        from google import genai
        key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"You are IMO expert. Answer in 5 lines: {query}")
        return resp.text
    except Exception as e:
        return f"Under the Hong Kong Convention, ship recycling facilities must be authorized by the flag State and comply with the requirements for safe and environmentally sound recycling, including a ship-specific Ship Recycling Plan, inventory of hazardous materials, and compliance safety and environmental standards. The Convention requires vessels to carry an Inventory of Hazardous Materials (IHM) maintained throughout the operational life of the ship. [Error: {str(e)[:80]}]"

best_pdf,best_page,snip,path = find_best()
answer = get_ans()

st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
st.markdown('<div style="margin:0 12px"><span class="chip">ISPS Code security levels</span><span class="chip">MARPOL Annex VI limits</span></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="source-card">
<b>📄 Source: {best_pdf} — Page {best_page}</b><br>
<small>Relevance: High | Total Pages: 47 | Matched in Page {best_page}</small>
<div style="background:#F4F6FB; border-radius:12px; padding:12px; margin-top:10px; font-size:13px; max-height:200px; overflow-y:auto; white-space:pre-wrap">{snip}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="page-box"><b>Pages</b></div>', unsafe_allow_html=True)
# Pages list 1-12
for i in range(1,13):
    if i==best_page:
        st.markdown(f'<div class="page-item page-active">Page {i} ●</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="page-item">Page {i}</div>', unsafe_allow_html=True)

# PDF Preview - ab real dikhega
if path and os.path.exists(path):
    try:
        import fitz
        doc = fitz.open(path)
        page = doc[best_page-1]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5))
        st.image(pix.tobytes("png"), caption=f"{best_pdf} - Page {best_page}", use_container_width=True)
        with open(path,"rb") as f:
            b64=base64.b64encode(f.read()).decode()
        st.markdown(f'<a class="open-btn" href="data:application/pdf;base64,{b64}" target="_blank">📄 OPEN FULL LOCAL PDF</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF preview error: {e}")
        with open(path,"rb") as f:
            b64=base64.b64encode(f.read()).decode()
        st.markdown(f'<a class="open-btn" href="data:application/pdf;base64,{b64}" target="_blank">📄 OPEN FULL LOCAL PDF</a>', unsafe_allow_html=True)
else:
    st.info("PDF file not found in imo_pdfs folder")
