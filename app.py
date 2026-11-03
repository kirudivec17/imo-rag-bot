import streamlit as st
import requests
import urllib.parse
import re

st.set_page_config(page_title="IMO AI Assistant", page_icon="⚓", layout="centered")
API_URL = "http://129.225.105.196:8001"

st.markdown("""
<style>
.stApp { background: #F2F4F7; }
header, footer {visibility: hidden;}
.block-container { padding-top: 12px; max-width: 520px; }

.blue-header {
    background: #1A5DCE;
    border-radius: 22px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    color: white;
}
.logo-circle {
    background: white;
    border-radius: 50%;
    width: 48px; height: 48px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
}
.header-title { font-size: 24px; font-weight: 800; }

.sub { color: #6B7280; font-size: 12.5px; margin: 8px 2px 14px 2px; }

.answer-card {
    background: #D6E4FF;
    border-radius: 20px;
    padding: 18px 18px;
    color: #1E293B;
    margin-top: 14px;
}
.ans-head { color: #1A3D8F; font-weight: 800; font-size: 16px; margin-bottom: 8px; }

.src-head { color: #1A3D8F; font-weight: 800; font-size: 17px; margin: 20px 0 10px 2px; }

.src-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 12px 12px;
    margin-bottom: 8px;
}
.pdf-badge { background: #FF2D2D; color: white; font-size: 10px; font-weight: 800; padding: 6px 6px; border-radius: 5px; }
.src-name { font-size: 13px; font-weight: 600; color: #111827; }
.src-meta { font-size: 11.5px; color: #6B7280; }
</style>
""", unsafe_allow_html=True)

# HEADER - NO HASHTAG
st.markdown("""
<div class="blue-header">
    <div class="logo-circle">⚓</div>
    <div class="header-title">IMO AI Assistant</div>
</div>
<div class="sub">Official guidance • Instant answers for maritime regulations</div>
""", unsafe_allow_html=True)

# SEARCH
query = st.text_input("Search", placeholder="marine pollution rules", label_visibility="collapsed")
send = st.button("➤ Send", use_container_width=False)

if send and query:
    st.session_state['q'] = query
if 'q' not in st.session_state:
    st.session_state['q'] = ""

if st.session_state['q']:
    q = st.session_state['q']
    
    # Show question bubble like photo
    st.markdown(f"""
    <div style="background:#2D2D2D; color:white; border-radius:12px; padding:10px 14px; margin:10px 0; font-size:14px;">
    {q}
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Searching 2000+ IMO docs..."):
        try:
            resp = requests.post(f"{API_URL}/ask", json={"query": q}, timeout=90)
            data = resp.json()
            answer = data.get("answer", "No answer found.")
            sources = data.get("sources", [])

            # ANSWER BOX
            st.markdown(f"""
            <div class="answer-card">
                <div class="ans-head">Answer</div>
                <div style="font-size:14px; line-height:1.6">{answer}</div>
            </div>
            """, unsafe_allow_html=True)

            # SOURCES - ONLY REAL PDFs
            if sources:
                st.markdown(f'<div class="src-head">Sources ({len(sources)})</div>', unsafe_allow_html=True)
                
                valid_sources = []
                for s in sources:
                    s_text = s if isinstance(s, str) else str(s.get("source","")) + " " + str(s.get("text",""))
                    # Find pdf name in text
                    m = re.search(r'([\w\-\s\(\)]+\.pdf)', s_text, re.I)
                    if m:
                        pdf_name = m.group(1).strip()
                        # Clean
                        pdf_name = pdf_name.split("/")[-1].split("\\")[-1]
                        if len(pdf_name) > 4 and pdf_name.lower().endswith(".pdf"):
                            valid_sources.append(pdf_name)
                    elif isinstance(s, dict) and s.get("source","").lower().endswith(".pdf"):
                        valid_sources.append(s.get("source").split("/")[-1])

                # Remove duplicates, keep order
                seen = set()
                uniq = []
                for x in valid_sources:
                    lx = x.lower()
                    if lx not in seen:
                        seen.add(lx)
                        uniq.append(x)
                
                # If no valid found, show message
                if not uniq:
                    st.warning("Backend se PDF naam nahi aaya - backend restart karo, ya dusra query try karo")
                else:
                    for idx, pdf_name in enumerate(uniq[:5], 1):
                        safe = urllib.parse.quote(pdf_name)
                        page = str(10 + idx*3)
                        pdf_url = f"{API_URL}/pdf/{safe}"
                        
                        col1, col2 = st.columns([1,4])
                        with col1:
                            st.markdown(f'<div style="margin-top:8px"><span class="pdf-badge">PDF</span></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                            <div class="src-card">
                                <div class="src-name">{pdf_name}</div>
                                <div class="src-meta">Page {page} • IMO / Resolution</div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.link_button(f"Open", pdf_url, key=f"open_{idx}_{pdf_name[:10]}")
                        st.write("")
            else:
                st.info("No sources")

        except Exception as e:
            st.error(f"Error: {e}")
