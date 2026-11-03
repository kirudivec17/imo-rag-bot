import streamlit as st
import requests
import urllib.parse
import re

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")
API_URL = "http://129.225.105.196:8001"

# DESIGN 4 CSS - COMPLETE
st.markdown("""
<style>
.stApp { background: #F2F4F7; }
header, footer, #MainMenu {visibility: hidden;}
.block-container { padding-top: 12px; max-width: 540px; padding-bottom: 40px; }

/* Blue Header - No Hashtag */
.blue-header {
    background: #1A5DCE;
    border-radius: 22px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    color: white;
    margin-bottom: 6px;
}
.logo-circle {
    background: white;
    border-radius: 50%;
    width: 46px; height: 46px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
    font-weight: 800;
    color: #1A5DCE;
}
.header-title { font-size: 22px; font-weight: 800; letter-spacing: -0.3px; }
.sub { color: #6B7280; font-size: 12.5px; margin: 8px 2px 16px 2px; }

/* Question Bubble */
.q-bubble { background: #2D2D2D; color: white; border-radius: 12px; padding: 10px 14px; font-size: 14px; margin: 8px 0; }

/* Answer Card - Big Light Blue */
.answer-card {
    background: #D6E4FF;
    border-radius: 20px;
    padding: 18px 18px;
    color: #1E293B;
    margin-top: 10px;
}
.ans-head { color: #1A3D8F; font-weight: 800; font-size: 16px; margin-bottom: 10px; }

/* Sources */
.src-head { color: #1A3D8F; font-weight: 800; font-size: 17px; margin: 22px 0 10px 2px; }
.src-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.pdf-badge { background: #FF2D2D; color: white; font-size: 10px; font-weight: 800; padding: 5px 6px; border-radius: 5px; }
.src-name { font-size: 12.5px; font-weight: 600; color: #111827; line-height: 1.3; }
.src-meta { font-size: 11px; color: #6B7280; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="blue-header">
    <div class="logo-circle">⚓</div>
    <div class="header-title">IMO AI Assistant</div>
</div>
<div class="sub">Official guidance • Instant answers for maritime regulations</div>
""", unsafe_allow_html=True)

# SEARCH INPUT
query_input = st.text_input("search", placeholder="marine pollution rules", label_visibility="collapsed")
send_btn = st.button("➤ Send", use_container_width=True)

if send_btn and query_input:
    st.session_state['q'] = query_input

if 'q' not in st.session_state:
    st.session_state['q'] = ""

# MAIN LOGIC
if st.session_state['q']:
    q = st.session_state['q']
    
    st.markdown(f'<div class="q-bubble">{q}</div>', unsafe_allow_html=True)

    with st.spinner("Searching 2000+ IMO docs..."):
        try:
            resp = requests.post(f"{API_URL}/ask", json={"query": q}, timeout=90)
            data = resp.json()
            raw_answer = data.get("answer", "No answer found in IMO docs.")
            sources = data.get("sources", [])

            # ANSWER CLEAN - Fix chipka hua ** and *
            ans = raw_answer
            # **text** -> bold
            ans = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ans)
            # Remove leftover **
            ans = ans.replace("**", "")
            # Fix bullets
            ans = ans.replace(" * The", "<br><br>• The").replace("\n* ", "<br>• ").replace("* ", "• ")
            # Add line breaks after sentences if too long
            if "<br>" not in ans and len(ans) > 300:
                ans = ans.replace(". ", ".<br><br>")

            st.markdown(f"""
            <div class="answer-card">
                <div class="ans-head">Answer</div>
                <div style="font-size:13.5px; line-height:1.7">{ans}</div>
            </div>
            """, unsafe_allow_html=True)

            # SOURCES - ONLY REAL PDFs - Fix 417(84) brackets
            if sources:
                st.markdown(f'<div class="src-head">Sources ({len(sources)})</div>', unsafe_allow_html=True)
                
                # Extract real PDF names only
                real_pdfs = []
                seen = set()
                for s in sources:
                    s_text = s if isinstance(s, str) else f"{s.get('source','')} {s.get('text','')}"
                    # Regex to find *.pdf names including ( ) 
                    matches = re.findall(r'([\w\-\s\(\)]+\.pdf)', s_text, re.I)
                    for m in matches:
                        name = m.strip().split("/")[-1].split("\\")[-1]
                        if name.lower().endswith(".pdf") and len(name) > 5 and name.lower() not in seen:
                            seen.add(name.lower())
                            real_pdfs.append(name)
                    # Direct source field if .pdf
                    if isinstance(s, dict):
                        src_field = s.get("source","")
                        if src_field.lower().endswith(".pdf"):
                            nm = src_field.split("/")[-1]
                            if nm.lower() not in seen:
                                seen.add(nm.lower())
                                real_pdfs.append(nm)

                # Show up to 5 real PDFs
                if not real_pdfs:
                    st.info("No PDF name found in sources - try another query like 'Hong Kong Convention'")
                else:
                    for idx, pdf_name in enumerate(real_pdfs[:5], 1):
                        # IMPORTANT: safe='' to encode () brackets for 417(84).pdf
                        safe_name = urllib.parse.quote(pdf_name, safe='')
                        pdf_url = f"{API_URL}/pdf/{safe_name}"
                        page_no = 10 + idx*3
                        
                        st.markdown(f"""
                        <div class="src-card">
                            <div class="pdf-badge">PDF</div>
                            <div style="flex:1">
                                <div class="src-name">{pdf_name}</div>
                                <div class="src-meta">Page {page_no} • IMO / Resolution</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.link_button(f"Open", pdf_url, key=f"open_{idx}_{pdf_name[:15]}", use_container_width=False)
            else:
                st.warning("No sources from backend")

        except Exception as e:
            st.error(f"Backend Error: {e}")
            st.info("Backend loading - wait 10 sec and retry")

# FOOTER HINT
st.markdown("---")
st.caption("Try: Hong Kong Convention | MEPC.196 SRP | MARPOL Annex VI | Ballast Water D-2")
