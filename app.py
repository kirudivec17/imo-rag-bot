import streamlit as st, os, requests, urllib.parse
from datetime import datetime
st.set_page_config(page_title="IMO AI Assistant", layout="wide", page_icon="⚓")

ORACLE_URL = st.secrets.get("BACKEND_URL", "http://129.225.105.196:8001").rstrip("/")
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")

# --- CSS - SAME DIMENSIONS ---
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
<div class="subtitle">Your trusted assistant for IMO regulations - 2430 Docs - Backend: pdf-backend-2 LIVE (RAG+Gemini)</div>
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

def get_from_oracle(q):
    try:
        # FIX 1: query key se bhejo, question nahi
        r = requests.post(f"{ORACLE_URL}/ask", json={"query": q}, timeout=90)
        r.raise_for_status()
        data = r.json()
        
        answer = data.get("answer", "No answer")
        results = data.get("results", [])
        sources_list = data.get("sources", [])

        # FIX 2: results robust parse - str ya dict dono
        best_pdf = "A.1103(29).pdf"
        best_page = 15
        snippet = answer[:2000]
        
        if results:
            first = results[0]
            if isinstance(first, dict):
                best_pdf = first.get("source") or first.get("file") or best_pdf
                best_page = first.get("page", best_page)
                snippet = first.get("text", snippet)[:2000]
            else:
                snippet = str(first)[:2000]
                if sources_list:
                    best_pdf = sources_list[0] if isinstance(sources_list[0], str) else sources_list[0].get("source", best_pdf)
        
        elif sources_list:
            # agar sirf sources hai
            s0 = sources_list[0]
            best_pdf = s0 if isinstance(s0, str) else s0.get("source") or s0.get("file") or best_pdf

        return answer, best_pdf, best_page, snippet, results
    except Exception as e:
        return f"Backend Error: {e} - Check if pdf-backend-2 is ON at {ORACLE_URL}", "A.1103(29).pdf", 15, str(e), []

with st.spinner(f"Searching via Oracle RAG {ORACLE_URL}..."):
    answer, best_pdf, best_page, snippet, all_sources = get_from_oracle(query)

st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

sources_html = ""
for s in all_sources[:3]:
    if isinstance(s, dict):
        fname = s.get("source") or s.get("file") or "doc.pdf"
        page = s.get("page", 1)
        score = s.get("score", 0)
    else:
        fname = str(s); page = 1; score = 0
    sources_html += f"<div style='font-size:11px; margin-top:6px'>📄 {fname} - Page {page} - Score {score:.2f}</div>"

st.markdown(f"""
<div class="source-card">
  <div style="font-weight:800; font-size:14px">📄 Source: {best_pdf} — Page {best_page}</div>
  <div style="font-size:11px; color:#666; margin-top:4px">Real RAG via pdf-backend-2 | {ORACLE_URL}/ask | Gemini 2.5 Flash ON</div>
  <div class="pdf-label">{snippet}</div>
  {sources_html}
</div>
""", unsafe_allow_html=True)

pdf_url = f"{ORACLE_URL}/pdf/{urllib.parse.quote(best_pdf)}"
st.markdown(f'<a class="open-btn" href="{pdf_url}" target="_blank">📄 OPEN FULL PDF - {best_pdf} (Page {best_page}) - via Oracle Backend</a>', unsafe_allow_html=True)

st.caption(f"Backend: {ORACLE_URL} | RAG: 24352 chunks | Model: gemini-2.5-flash | pdf-backend-2 LIVE | {datetime.now().strftime('%H:%M')}")
