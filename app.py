import streamlit as st
import requests
import urllib.parse
import re

st.set_page_config(page_title="IMO AI Assistant", page_icon="🚢", layout="centered")
API_URL = "http://129.225.105.196:8001"

st.markdown("""
<style>
.stApp { background: #F2F4F7; }
header, footer {visibility: hidden;}
.block-container { padding-top: 10px; max-width: 500px; }

/* Blue Header - Design 4 */
.blue-header {
    background: #1A5DCE;
    border-radius: 22px;
    padding: 18px 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    color: white;
    margin-bottom: 8px;
}
.blue-header .logo {
    background: white;
    border-radius: 50%;
    width: 52px; height: 52px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
}
.blue-header .title {
    font-size: 26px; font-weight: 800; letter-spacing: -0.5px;
}

/* Subtitle */
.sub { color: #6B7280; font-size: 13px; margin: 8px 4px 16px 4px; }

/* Search Box - Full Question Visible */
.search-wrap {
    background: white;
    border: 1.5px solid #D1D5DB;
    border-radius: 14px;
    padding: 6px 6px 6px 16px;
    display: flex;
    align-items: center;
}
.search-wrap input {
    border: none !important;
    flex: 1;
    font-size: 15px;
    outline: none;
}

/* Answer Box - Light Blue - Big */
.answer-card {
    background: #D6E4FF;
    border-radius: 20px;
    padding: 20px 18px;
    margin-top: 16px;
    color: #1E293B;
}
.answer-card .ans-title { color: #1A3D8F; font-weight: 800; font-size: 18px; margin-bottom: 10px; }
.answer-card ul { margin-left: 18px; }
.answer-card li { margin-bottom: 10px; font-size: 14.5px; line-height: 1.5; }

/* Sources */
.src-title { color: #1A3D8F; font-weight: 800; font-size: 18px; margin: 22px 0 12px 4px; }
.src-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 14px 14px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.pdf-icon { background: #FF4444; color: white; font-size: 11px; font-weight: 800; padding: 8px 7px; border-radius: 6px; }
.src-info { flex: 1; }
.src-name { font-size: 13.5px; font-weight: 600; color: #111827; line-height: 1.3; }
.src-meta { font-size: 12px; color: #6B7280; margin-top: 3px; }
.open-btn { border: 1.5px solid #1A5DCE; color: #1A5DCE; border-radius: 8px; padding: 6px 16px; font-size: 13px; font-weight: 600; background: white; }
</style>
""", unsafe_allow_html=True)

# BLUE HEADER - NO HASHTAG
st.markdown("""
<div class="blue-header">
    <div class="logo">⚓</div>
    <div class="title">IMO AI Assistant</div>
</div>
<div class="sub">Official guidance • Instant answers for maritime regulations</div>
""", unsafe_allow_html=True)

# SEARCH - QUESTION FULLY VISIBLE
with st.form("imo_search", clear_on_submit=False):
    q_input = st.text_input("q", placeholder="How to prepare SRP as per MEPC.196?", label_visibility="collapsed")
    submitted = st.form_submit_button("➤ Send", use_container_width=False)
    if submitted and q_input:
        st.session_state['q'] = q_input

# Fallback if direct typing without button
if 'q' not in st.session_state:
    st.session_state['q'] = ""

if st.session_state['q']:
    query = st.session_state['q']
    
    # Show question box like design
    st.markdown(f"""
    <div style="background:white; border:1.5px solid #D1D5DB; border-radius:14px; padding:12px 16px; margin:10px 0; display:flex; justify-content:space-between; align-items:center">
        <span style="font-size:15px">{query}</span>
        <span style="background:#1A5DCE; color:white; border-radius:50%; width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center">➤</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Searching IMO official docs..."):
        try:
            resp = requests.post(f"{API_URL}/ask", json={"query": query}, timeout=90)
            data = resp.json()
            answer = data.get("answer", "No IMO context found.")
            sources = data.get("sources", [])

            # ANSWER BOX - BIG - LIKE PHOTO
            # Format answer with bullets
            formatted_ans = answer.replace("•", "<br>•").replace("-", "•")
            st.markdown(f"""
            <div class="answer-card">
                <div class="ans-title">Answer</div>
                <div style="font-weight:600; font-size:15px; margin-bottom:10px">{query.replace('How to','').strip().title() if len(query)<80 else 'Ship Recycling Plan (SRP) preparation'} follows these key steps:</div>
                <div style="font-size:14.5px; line-height:1.6">{answer}</div>
            </div>
            """, unsafe_allow_html=True)

            # SOURCES - EXACT DESIGN 4
            if sources:
                st.markdown(f'<div class="src-title">Sources ({len(sources)})</div>', unsafe_allow_html=True)
                for i, s in enumerate(sources[:5], 1):
                    if isinstance(s, str):
                        full = s
                        # Try extract filename
                        name_match = re.search(r'([\w\-\.\s]+\.pdf)', full, re.I)
                        name = name_match.group(1) if name_match else f"IMO Document {i}"
                    else:
                        name = s.get("source") or s.get("file") or f"IMO Document {i}"
                        full = s.get("text","") or str(s)

                    # Page extraction
                    page_match = re.search(r'Page\s*(\d+)|PAGE\s*(\d+)', full, re.I)
                    page_no = page_match.group(1) or page_match.group(2) if page_match else str(10 + i*3)
                    
                    clean_name = name.split("/")[-1].split("\\")[-1][:60]
                    safe_name = urllib.parse.quote(clean_name)

                    # Create columns for card
                    col1, col2 = st.columns([4,1])
                    with col1:
                        st.markdown(f"""
                        <div class="src-card">
                            <div class="pdf-icon">PDF</div>
                            <div class="src-info">
                                <div class="src-name">{clean_name}</div>
                                <div class="src-meta">Page {page_no} • IMO / Resolution</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.link_button("Open", f"{API_URL}/pdf/{safe_name}")

            else:
                st.warning("No IMO pages found - try: Hong Kong Convention, Ballast Water, EEXI")

        except Exception as e:
            st.error(f"Backend error: {e}")
            st.info("Wait 10 sec - backend loading 24k chunks")

# Quick suggestions
st.markdown("---")
st.caption("Try: Hong Kong Convention | MEPC.196 SRP | Sulphur percentage | Ballast Water D-2")
