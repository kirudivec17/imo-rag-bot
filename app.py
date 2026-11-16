import streamlit as st
import requests
import urllib.parse
import re

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")

API_URL = "http://129.225.105.196:8001"
PDF_URL = "http://129.225.105.196:8001"

# --- V3 FIX: SIMPLE + PAKKA DEDUP ---
def clean_answer(raw):
    if not raw:
        return ""
    text = raw.strip()
    # Upar ki "Based on IMO documents:" line hatao
    text = re.sub(r'Based on IMO documents:?', '', text, flags=re.I).strip()

    # Step 1: Pehle \n se lines me todo
    lines = re.split(r'\n+', text)
    cleaned = []
    seen = set()

    for line in lines:
        s = line.strip()
        # Aage laga number hatao: "1." / "1)" / "1" sab
        s = re.sub(r'^\d+[\.\)]\s*', '', s).strip()
        s = re.sub(r'^\d+\s+', '', s).strip()
        if len(s) < 20:
            continue
        # Key banao - number, space, punctuation sab hatake
        key = re.sub(r'[^a-z0-9]', '', s.lower())
        if key in seen:
            continue
        # Fuzzy check: shuru ke 80 char same hai to duplicate
        dup = False
        for old in seen:
            if key[:80] and (key[:80] in old or old[:80] in key):
                dup = True
                break
        if dup:
            continue
        seen.add(key)
        cleaned.append(s)

    # Step 2: Fallback - agar lines se kuch nahi mila to sentence se todo
    if not cleaned:
        parts = re.split(r'(?<=[.!])\s+', text)
        for p in parts:
            p = re.sub(r'^\d+[\.\)]\s*', '', p.strip()).strip()
            if len(p) > 20 and p not in cleaned:
                cleaned.append(p)

    # Step 3: Saaf numbered list banao
    out = ""
    for i, c in enumerate(cleaned, 1):
        out += f"{i}. {c}\n\n"
    return out[:4500]

st.markdown("""
<style>
.stApp { background: #F2F4F7; }
header, footer, #MainMenu {visibility: hidden;}
.block-container { padding-top: 12px; max-width: 540px; padding-bottom: 40px; }
.blue-header { background: #1A5DCE; border-radius: 22px; padding: 16px 20px; display: flex; align-items: center; gap: 14px; color: white; margin-bottom: 6px; }
.logo-circle { background: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: #1A5DCE; }
.header-title { font-size: 22px; font-weight: 800; letter-spacing: -0.3px; }
.sub { color: #6B7280; font-size: 12.5px; margin: 8px 2px 16px 2px; }
.q-bubble { background: #2D2D2D; color: white; border-radius: 12px; padding: 10px 14px; font-size: 14px; margin: 8px 0; }
.answer-card { background: #D6E4FF; border-radius: 20px; padding: 18px 18px; color: #1E293B; margin-top: 10px; }
.ans-head { color: #1A3D8F; font-weight: 800; font-size: 16px; margin-bottom: 10px; }
.src-head { color: #1A3D8F; font-weight: 800; font-size: 17px; margin: 22px 0 10px 2px; }
.src-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 10px 12px; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; }
.pdf-badge { background: #FF2D2D; color: white; font-size: 10px; font-weight: 800; padding: 5px 6px; border-radius: 5px; }
.src-name { font-size: 12.5px; font-weight: 600; color: #111827; line-height: 1.3; }
.src-meta { font-size: 11px; color: #6B7280; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="blue-header">
    <div class="logo-circle">⚓</div>
    <div class="header-title">IMO AI Assistant</div>
</div>
<div class="sub">Official guidance • Instant answers for maritime regulations</div>
""", unsafe_allow_html=True)

query_input = st.text_input("search", placeholder="marine pollution rules", label_visibility="collapsed")
send_btn = st.button("➤ Send", use_container_width=True)

if send_btn and query_input:
    st.session_state['q'] = query_input

if 'q' not in st.session_state:
    st.session_state['q'] = ""

if st.session_state['q']:
    q = st.session_state['q']
    st.markdown(f'<div class="q-bubble">{q}</div>', unsafe_allow_html=True)

    with st.spinner("Searching IMO docs..."):
        try:
            resp = requests.post(f"{API_URL}/ask", json={"q": q}, timeout=90)
            data = resp.json()
            raw_answer = data.get("answer", "")
            sources = data.get("sources") or data.get("results") or []

            if not raw_answer:
                st.warning("No answer from backend. Try again.")
                st.stop()

            ans = clean_answer(raw_answer)
            ans = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ans)
            ans = ans.replace("**", "").replace("\n", "<br>")

            st.markdown(f"""
            <div class="answer-card">
                <div class="ans-head">Answer</div>
                <div style="font-size:13.5px; line-height:1.7">{ans}</div>
            </div>
            """, unsafe_allow_html=True)

            if sources:
                st.markdown('<div class="src-head">Sources</div>', unsafe_allow_html=True)
                seen_pdfs = set()
                shown = 0
                for s in sources:
                    if isinstance(s, str):
                        m = re.findall(r'([\w\-\s\(\)]+\.pdf)', s, re.I)
                        pdf_name = m[0].strip().split("/")[-1] if m else ""
                        snippet = s[:300]
                        page = None
                    else:
                        pdf_name = (s.get("source") or s.get("pdf_name") or s.get("file") or "").split("/")[-1].split("\\")[-1]
                        snippet = s.get("text") or s.get("snippet") or ""
                        page = s.get("page") or s.get("page_no") or None

                    if not pdf_name:
                        continue
                    pdf_key = pdf_name.lower().strip()
                    if pdf_key in seen_pdfs:
                        continue
                    seen_pdfs.add(pdf_key)
                    shown += 1
                    if shown > 5:
                        break

                    safe_name = urllib.parse.quote(pdf_name, safe='')
                    pdf_url = f"{PDF_URL}/download/{safe_name}"
                    meta_text = f"Page {page}" if page else "Source from IMO docs"

                    st.markdown(f"""
                    <div class="src-card">
                        <div class="pdf-badge">PDF</div>
                        <div style="flex:1">
                            <div class="src-name">{pdf_name}</div>
                            <div class="src-meta">{meta_text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if snippet:
                        st.caption(snippet[:300])
                    st.link_button("Open", pdf_url, key=f"open_{shown}_{pdf_name[:20]}", use_container_width=False)
            else:
                st.info("Answer mil gaya, par backend ne sources nahi bheje.")

        except Exception as e:
            st.error(f"Backend Error: {e}")
            st.info("Backend loading - wait 10 sec and retry")

st.markdown("---")
st.caption("Try: Hong Kong Convention | MARPOL Annex VI | Ballast Water D-2")
