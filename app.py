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
.answer-box {background:#D9E6FF; border-radius:20px; padding:18px; font-size:14.5px; line-height:1.7; margin:14px 12px}
.source-card {background:white; border-radius:20px; padding:14px; margin:14px 12px; box-shadow:0 4px 18px rgba(0,0,0,0.06); border:1px solid #eee}
.page-item {padding:12px; border-radius:12px; border:1px solid #eee; margin:6px 12px; background:white}
.page-active {background:#0B3D91 !important; color:white !important; font-weight:700}
.open-btn {background:#0B3D91; color:white; width:92%; padding:14px; border-radius:14px; text-align:center; font-weight:800; display:block; text-decoration:none; margin:14px auto}
</style>
<div class="top-bar"><div class="top-left"><div class="top-logo">⚓</div><div class="top-text">INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div></div><div style="font-size:24px">🔍 👤</div></div>
<div class="main-title">IMO AI ASISTANT</div>
<div class="subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>
""", unsafe_allow_html=True)

# --- FIX: Send button ka 100% kaam karne wala system ---
if "q" not in st.session_state:
    st.session_state.q = "What are the requirements under the Hong Kong Convention?"

# Question box + Send button - NO FORM, direct columns
c1, c2 = st.columns([0.82, 0.18])
with c1:
    user_input = st.text_input("q", value=st.session_state.q, placeholder="Type your question...", label_visibility="collapsed", key="input_box")
with c2:
    send_clicked = st.button("➤", use_container_width=True, type="primary")

# Jab button press ho ya Enter press ho to query update
if send_clicked:
    st.session_state.q = user_input
    st.rerun()

# Enter key se bhi kaam kare - agar user ne text change kiya
if user_input != st.session_state.q and user_input.strip() != "":
    # Mobile me Enter dabate hi ye chalega
    if len(user_input) > 5 and user_input != st.session_state.q:
        pass  # Wait for button

query = st.session_state.q
st.caption(f"You asked: {query}")

# --- FAST SEARCH ---
FILES = glob.glob("imo_pdfs/*.pdf")[:2000]

def fast_find(q):
    best_name, best_page, best_snip, best_path = (os.path.basename(FILES[0]) if FILES else "MEPC.269(68).pdf"), 5, "", (FILES[0] if FILES else "")
    try:
        from pypdf import PdfReader
        q_words = [w.lower() for w in q.split() if len(w)>3]
        max_s = -1
        for pf in FILES[:150]:
            try:
                r = PdfReader(pf)
                for i in range(min(10, len(r.pages))):
                    txt = r.pages[i].extract_text() or ""
                    sc = sum(txt.lower().count(w) for w in q_words)
                    if sc > max_s:
                        max_s = sc; best_name = os.path.basename(pf); best_page = i+1; best_snip = txt[:1000]; best_path = pf
            except: pass
    except: pass
    return best_name, best_page, best_snip, best_path

best_name, best_page, best_snip, best_path = fast_find(query)

def get_answer(q, snip):
    try:
        from google import genai
        key = st.secrets.get("GEMINI_API_KEY")
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"IMO expert: {q}. Context: {snip[:4000]}. Answer 5 lines.")
        return resp.text
    except Exception as e:
        return f"{snip[:700]}\n\nUnder Hong Kong Convention: Authorization, Ship Recycling Plan, IHM, safe & environmentally sound recycling required. (Gemini Error: {str(e)[:100]})"

answer = get_answer(query, best_snip)

st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="source-card">
<b>📄 Source: {best_name} — Page {best_page}</b><br>
<small>Total PDFs: {len(FILES)} | Page {best_page}</small>
<div style="background:#F4F6FB; border-radius:12px; padding:12px; margin-top:10px; font-size:13px; white-space:pre-wrap">{best_snip[:900]}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div style="margin:12px; font-weight:800">Pages</div>', unsafe_allow_html=True)
for i in range(1, 13):
    cls = "page-item page-active" if i==best_page else "page-item"
    st.markdown(f'<div class="{cls}">Page {i} {"●" if i==best_page else ""}</div>', unsafe_allow_html=True)

if best_path and os.path.exists(best_path):
    try:
        import fitz
        doc = fitz.open(best_path)
        pix = doc[best_page-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
        st.image(pix.tobytes("png"), caption=f"{best_name} - Page {best_page}", use_container_width=True)
    except:
        pass
    with open(best_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<a class="open-btn" href="data:application/pdf;base64,{b64}" target="_blank">📄 OPEN FULL LOCAL PDF</a>', unsafe_allow_html=True)
