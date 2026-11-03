import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="IMO AI Assistant", page_icon="🚢", layout="wide")

API_URL = "http://129.225.105.196:8001"

# --- EXACT PHOTO DESIGN CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background-color: #F5F7FB; }
header {visibility: hidden;}

/* Blue Header like Photo */
.imo-header {
    background: #0D3FA8;
    margin: -80px -100px 20px -100px;
    padding: 18px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.imo-header-left { display: flex; align-items: center; gap: 12px; color: white; font-weight: 700; font-size: 14px; line-height: 1.1; }
.imo-header-right { display: flex; gap: 20px; color: white; font-size: 24px; }

/* Title */
.imo-title { color: #0D3FA8; font-size: 38px; font-weight: 800; text-align: center; margin-top: 10px; }
.imo-subtitle { color: #555; text-align: center; margin-bottom: 25px; font-size: 15px; }

/* Question Box - Full Visible + Send Button */
.q-box {
    background: #E8EDF5;
    border: 1.5px solid #D0D9E8;
    border-radius: 18px;
    padding: 16px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}
.q-box input { border: none !important; background: transparent !important; width: 100%; font-size: 15px; }
.send-btn {
    background: #0D3FA8;
    color: white;
    border-radius: 14px;
    padding: 12px 18px;
    border: none;
    font-size: 20px;
    cursor: pointer;
}

/* Answer Box - Big, Photo like */
.a-box {
    background: #D6E2FA;
    border-radius: 20px;
    padding: 20px 22px;
    color: #1A2B4D;
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 18px;
}

/* Chips */
.chip { background: #D6E2FA; border-radius: 20px; padding: 8px 16px; font-size: 13px; color: #0D3FA8; font-weight: 600; display: inline-block; margin-right: 8px; margin-bottom: 10px; }

/* Source Card - Like Photo */
.source-card {
    background: white;
    border-radius: 24px 24px 0 0;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.08);
    padding: 22px;
    margin-top: 30px;
    border-top: 1px solid #E5E7EB;
}
.source-title { font-weight: 700; color: #1A2B4D; font-size: 16px; }
.pdf-snippet { background: #F0F2F5; border-radius: 14px; padding: 16px; font-family: serif; margin: 12px 0; color: #333; font-size: 13px; }
.open-btn { background: #0D3FA8; color: white; border-radius: 14px; padding: 14px; width: 100%; text-align: center; font-weight: 700; font-size: 16px; border: none; }
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="imo-header">
    <div class="imo-header-left">
        <div style="font-size:32px">🌐</div>
        <div>INTERNATIONAL<br>MARITIME<br>ORGANIZATION</div>
    </div>
    <div class="imo-header-right">🔍 👤</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="imo-title">#IMO AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="imo-subtitle">Your trusted assistant for IMO regulations, guidelines, and maritime safety</div>', unsafe_allow_html=True)

# QUESTION INPUT - FULL VISIBLE WITH SEND
with st.form("search_form", clear_on_submit=False):
    col1, col2 = st.columns([5,1])
    with col1:
        query = st.text_input("Q", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")
    with col2:
        submitted = st.form_submit_button("➤", use_container_width=True)
    
    if submitted and query:
        st.session_state['last_q'] = query

# Show last question as in photo
if 'last_q' in st.session_state:
    q = st.session_state['last_q']
    st.markdown(f"""
    <div class="q-box">
        <div style="font-size:20px">🔍</div>
        <div style="flex:1">{q}</div>
        <div class="send-btn">➤</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Searching IMO official docs..."):
        try:
            resp = requests.post(f"{API_URL}/ask", json={"query": q}, timeout=90)
            data = resp.json()
            ans = data.get("answer","No answer")
            sources = data.get("sources", [])

            # ANSWER BOX - BIG
            st.markdown(f'<div class="a-box">{ans}</div>', unsafe_allow_html=True)
            
            # Chips like photo
            st.markdown('<div><span class="chip">ISPS Code security levels</span><span class="chip">MARPOL Annex VI limits</span></div>', unsafe_allow_html=True)

            # SOURCE CARD - EXACT LIKE PHOTO
            if sources:
                s = sources[0]  # First source like photo
                if isinstance(s, str):
                    src_name = "IMO Document"
                    txt = s[:500]
                else:
                    src_name = s.get("source","IMO Resolution MEPC.269(68)")
                    txt = s.get("text","")[:500]

                # Extract page number if available
                page_no = "15"
                if "Page" in txt or "PAGE" in txt:
                    import re
                    m = re.search(r'PAGE\s+(\d+)', txt, re.I)
                    if m: page_no = m.group(1)

                clean_name = src_name.split("/")[-1]
                safe_name = urllib.parse.quote(clean_name)
                pdf_url = f"{API_URL}/pdf/{safe_name}"

                st.markdown(f"""
                <div class="source-card">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px">
                        <div style="background:#0D3FA8; color:white; padding:6px 10px; border-radius:6px; font-weight:800">PDF</div>
                        <div class="source-title">Source: {clean_name} — Page {page_no}</div>
                    </div>
                    <div style="color:#666; font-size:13px; margin-bottom:10px">Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
                    <div class="pdf-snippet">
                        MEPC 68/21/Add.1 — ANNEX 7 — PAGE {page_no}<br><br>
                        8.3.1 The ship recycling plan shall be developed.<br>
                        {txt[:300]}...
                    </div>
                    <a href="{pdf_url}" target="_blank" style="text-decoration:none">
                        <div class="open-btn">📄 Open</div>
                    </a>
                    <div style="text-align:center; margin-top:10px; font-size:12px; color:#888">View full document on IMO website →</div>
                </div>
                """, unsafe_allow_html=True)

                # More sources if available
                if len(sources) > 1:
                    st.divider()
                    st.write(f"**{len(sources)-1} more related IMO pages found:**")
                    for i, extra in enumerate(sources[1:4], 2):
                        if isinstance(extra, str): name = f"Doc-{i}.pdf"
                        else: name = extra.get("source", f"Doc-{i}.pdf")
                        safe = urllib.parse.quote(name.split("/")[-1])
                        st.link_button(f"📄 {name} - Open Page {i}", f"{API_URL}/pdf/{safe}")

        except Exception as e:
            st.error(f"Error: {e}")
