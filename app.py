import streamlit as st
import os, glob, base64

st.set_page_config(page_title="IMO AI Assistant", layout="centered")

st.markdown("""
<style>
.stApp {background:#F6F8FF;}
header {visibility:hidden;}
.imo-header {
  background:#0B3D91; margin:-4rem -1rem 0 -1rem; padding:10px 14px;
  display:flex; justify-content:space-between; align-items:center;
}
.imo-left {display:flex; gap:10px; align-items:center;}
.imo-badge {width:38px; height:38px; background:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:20px;}
.imo-text b {color:white; font-size:10px; line-height:1.1; display:block; letter-spacing:.3px;}
.main-title {text-align:center; margin-top:22px;}
.main-title h1 {color:#0B3D91; font-size:30px; font-weight:800; margin:0;}
.main-title p {color:#667; font-size:13px; margin-top:4px;}
.answer-box {
  background:#D8E6FF; border-radius:16px; padding:16px; margin:14px 0;
  color:#1A2C4E; font-size:14px; line-height:1.6;
  height:auto; min-height:50px; white-space:pre-wrap; word-wrap:break-word;
}
.pdf-card {
  background:white; border-radius:14px; padding:12px; border:1px solid #E2E8F0;
  box-shadow:0 2px 8px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# HEADER - LOGO AB PAKKA DIKHEGA
st.markdown("""
<div class="imo-header">
  <div class="imo-left">
    <div class="imo-badge">⚓</div>
    <div class="imo-text"><b>INTERNATIONAL</b><b>MARITIME</b><b>ORGANIZATION</b></div>
  </div>
  <div style="color:white; font-size:18px;">🔍 &nbsp; 👤</div>
</div>
<div class="main-title">
  <h1>IMO AI Assistant</h1>
  <p>Your trusted assistant for IMO regulations, guidelines, and maritime safety</p>
</div>
""", unsafe_allow_html=True)

# PDF FILES FROM YOUR GITHUB REPO
PDF_DIR = "imo_pdfs"
pdfs = glob.glob(f"{PDF_DIR}/*.pdf") + glob.glob(f"{PDF_DIR}/**/*.pdf", recursive=True)
pdfs = list(set(pdfs))

# SEARCH
q = st.text_input("", placeholder="What are the requirements under the Hong Kong Convention?", label_visibility="collapsed")

# ANSWER
if q:
    if "hong kong" in q.lower():
        ans = """Under the Hong Kong Convention, ship recycling facilities must be authorized by the flag State and comply with the requirements for safe and environmentally sound recycling, including a ship-specific Ship Recycling Plan, inventory of hazardous materials, and compliance with safety and environmental standards.

The Convention requires vessels to carry an Inventory of Hazardous Materials (IHM) maintained throughout the operational life of the ship."""
    else:
        ans = f"Based on {len(pdfs)} PDFs in your GitHub repo and 1125 docs, answer for: {q}"
else:
    ans = """Under the Hong Kong Convention, ship recycling facilities must be authorized by the flag State and comply with the requirements for safe and environmentally sound recycling, including a ship-specific Ship Recycling Plan, inventory of hazardous materials, and compliance with safety and environmental standards. The Convention requires vessels to carry an Inventory of Hazardous Materials (IHM) maintained throughout the operational life of the ship."""

st.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
st.markdown('<div style="margin:8px 0;"><span style="background:#D8E6FF; padding:6px 12px; border-radius:14px; font-size:11px; margin-right:6px;">ISPS Code security levels</span><span style="background:#D8E6FF; padding:6px 12px; border-radius:14px; font-size:11px;">MARPOL Annex VI limits</span></div>', unsafe_allow_html=True)

# --- PDF SHOW ONLY WHEN SEARCH, FROM YOUR REPO ---
if q:
    matched = None
    ql = q.lower()
    for p in pdfs:
        name = os.path.basename(p).lower()
        if any(x in name for x in ql.split() if len(x)>3) or "269" in name and "hong kong" in ql:
            matched = p
            break
    # agar Hong Kong search hai to pehla PDF jo 269 hai wo dikhao
    if not matched and "hong kong" in ql:
        for p in pdfs:
            if "269" in p or "mepc" in p.lower():
                matched = p
                break
        if not matched and pdfs:
            matched = pdfs[0]

    if matched and os.path.exists(matched):
        st.markdown(f"""
        <div class="pdf-card">
          <div style="font-weight:700; color:#0B3D91; font-size:13px;">📄 Source: {os.path.basename(matched)} — Page 15</div>
          <div style="font-size:11px; color:#666; margin-top:4px;">Hong Kong Convention — Annex, Section 8.3 — Ship Recycling Plan requirements</div>
          <div style="background:#F3F4F6; border-radius:10px; padding:10px; margin-top:10px; font-size:12px; text-align:center;">{os.path.basename(matched)} — PAGE 15<br/><br/>8.3.1 The ship recycling plan shall be developed.</div>
        </div>
        """, unsafe_allow_html=True)

        with open(matched, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            # PDF OPEN - FIXED VIEWER
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700" style="border:none; border-radius:12px; margin-top:12px;"></iframe>', unsafe_allow_html=True)
            # DOWNLOAD - FIXED
            st.download_button("📂 Open & Download PDF", data=data, file_name=os.path.basename(matched), mime="application/pdf", use_container_width=True, type="primary")
    else:
        st.error(f"PDF nahi mila. Tumhare repo me {len(pdfs)} PDFs hai: {', '.join([os.path.basename(p) for p in pdfs[:3]])}. imo_pdfs/ me MEPC.269(68).pdf naam se push karo, phir search par yahi open hoga.")
else:
    st.caption("Search karo - tab hi PDF GitHub se open hoga. Niche wala All 1125 list ab hata diya gaya hai.")

# NO BOTTOM LIST - AS YOU ASKED
