import streamlit as st
import glob, os, base64, json
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

st.set_page_config(page_title="Assistant IMO Bot", page_icon="🚢", layout="wide")

# ---------- STORAGE ----------
try:
    from streamlit_local_storage import LocalStorage
    localS = LocalStorage()
    HAS_STORAGE = True
except:
    HAS_STORAGE = False
    localS = None

# ---------- SIDEBAR (hidden but for clear) ----------
with st.sidebar:
    st.markdown("### IMO RAG Files")
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    if not files:
        files = glob.glob("master_*.txt")
    st.write(f"Total: {len(files)}")
    if st.button("🗑️ Clear Chat (Sidebar)"):
        st.session_state.messages = [{"role": "assistant", "content": "Good Day i am assistant imo bot.. how can i help you", "time": datetime.now().strftime("%H:%M")}]
        if HAS_STORAGE:
            try: localS.setItem("imo_chat_v2", None)
            except: pass
        st.rerun()

# ---------- LOGO ----------
def get_logo_base64():
    for name in ["bot_logo.png", "bot.png", "image_20261016_021908.webp", "/mnt/data/image_20261016_021908.webp"]:
        if os.path.exists(name):
            try:
                with open(name, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except: pass
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:38px;height:38px;border-radius:50%;background:white;padding:2px;">' if logo_b64 else '<div style="background:white;color:#0b2a5b;font-weight:900;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;">BOT</div>'

# ---------- CSS + HEADER + 3 DOT MENU ----------
# Note: IMO logo extreme right, 3 dots left to it
st.markdown(f"""
<style>
header, footer {{visibility: hidden;}}
.stApp {{ background: #e5ddd5; }}
/* Hide Streamlit Manage App Bottom Bar */
div[data-testid="stBottom"]{{display:none!important;}}
iframe[title="streamlitAppDeploymentButton"]{{display:none!important;}}
div[data-testid="stAppDeployButton"]{{display:none!important;}}
[data-testid="stStatusWidget"]{{display:none!important;}}

.imo-header{{background:#0b2a5b;padding:12px 16px;color:white;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:1000;height:60px;}}
.imo-logo-right{{background:white;color:#0b2a5b;font-weight:900;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;position:fixed!important;right:10px!important;top:11px!important;z-index:10002!important;}}
.dots-btn{{position:fixed!important;right:56px!important;top:12px!important;z-index:10003!important;background:transparent;border:none;color:white;font-size:26px;cursor:pointer;width:32px;height:32px;}}
.dropdown{{position:fixed;right:8px;top:64px;background:white;color:#111;width:260px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.3);z-index:10004;display:none;overflow:hidden;border:1px solid #e0e0e0;}}
.dropdown-item{{padding:13px 16px;border-bottom:1px solid #f0f0f0;cursor:pointer;font-size:14px;display:flex;align-items:center;gap:12px;color:#111;}}
.dropdown-item:hover{{background:#f5f5f5;}}
.dropdown-item.red{{color:#d32f2f;}}

.chat-wrap{{margin-top:75px;margin-bottom:95px;max-width:800px;margin-left:auto;margin-right:auto;}}
.msg-user{{background:#dcf8c6;color:#000!important;padding:10px 14px;border-radius:12px 0px 12px 12px;margin:8px 0 8px auto;max-width:82%;float:right;clear:both;box-shadow:0 1px 1px rgba(0,0,0,0.15);font-size:15px;}}
.msg-bot{{background:#ffffff;color:#000!important;padding:10px 14px;border-radius:0px 12px 12px 12px;margin:8px auto 8px 0;max-width:85%;float:left;clear:both;box-shadow:0 1px 1px rgba(0,0,0,0.15);font-size:14px;border:1px solid #e0e0e0;white-space:pre-wrap;}}
.msg-bot *{{color:#000!important;}}
.msg-time{{font-size:10px;color:#667781!important;margin-top:5px;text-align:right;}}
div[data-testid="stChatInput"]{{position:fixed!important;bottom:8px!important;left:8px!important;right:8px!important;background:#f0f0f0!important;padding:8px!important;z-index:1001!important;border-radius:25px!important;max-width:800px;margin:0 auto;}}
</style>

<div class="imo-header">
    <div style="display:flex; align-items:center; gap:12px;">{logo_html}</div>
    <div style="flex:1; text-align:center;">
        <div style="font-weight:700; font-size:17px; letter-spacing:0.5px;">Assistant IMO Bot</div>
        <div style="font-size:11px; opacity:0.9;">IMO RAG - Online</div>
    </div>
    <div class="imo-logo-right">IMO</div>
    <button class="dots-btn" onclick="var d=document.getElementById('drop'); d.style.display=d.style.display==='block'?'none':'block'">⋮</button>
</div>
""", unsafe_allow_html=True)

# Dropdown HTML (with JS actions)
dropdown_html = """
<div id="drop" class="dropdown">
    <div class="dropdown-item" onclick="document.getElementById('media-info').style.display='block';">📁 Media, links, and docs</div>
    <div class="dropdown-item">🔕 Notifications</div>
    <div class="dropdown-item">🖼️ Media visibility</div>
    <div class="dropdown-item">⭐ Add to Favorites</div>
    <div class="dropdown-item">📋 Add to list</div>
    <div class="dropdown-item red" onclick="localStorage.removeItem('imo_chat_backup'); localStorage.removeItem('imo_chat_v2'); window.location.reload();">🚫 Clear chat</div>
    <div class="dropdown-item" style="font-size:11px; color:#888; justify-content:center;">Meta AI app - IMO Bot</div>
</div>
<div id="media-info" style="display:none; position:fixed; top:70px; left:10px; right:10px; background:white; padding:16px; border-radius:12px; z-index:10005; box-shadow:0 4px 12px rgba(0,0,0,0.3);">
    <b>Media, links and docs</b><br><br>
    <span id="media-count"></span><br><br>
    <button onclick="document.getElementById('media-info').style.display='none'" style="padding:8px 16px; background:#0b2a5b; color:white; border:none; border-radius:8px;">Close</button>
</div>
<script>
document.addEventListener('click', function(e){
  var drop=document.getElementById('drop');
  var btn=document.querySelector('.dots-btn');
  if(drop && btn &&!drop.contains(e.target) &&!btn.contains(e.target)){ drop.style.display='none'; }
});
var mc=document.getElementById('media-count');
if(mc){ var saved=localStorage.getItem('imo_chat_backup'); mc.innerText = saved? (JSON.parse(saved).length + ' messages stored') : 'No media yet'; }
</script>
"""
st.markdown(dropdown_html, unsafe_allow_html=True)

# ---------- GEMINI ----------
@st.cache_resource
def get_gemini_client():
    try:
        from google import genai
        api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key: return None, False
        client = genai.Client(api_key=api_key)
        return client, True
    except: return None, False

gemini_client, gemini_ok = get_gemini_client()

# ---------- RAG LOAD ----------
@st.cache_resource
def load_chunks():
    files = sorted(glob.glob("master_imo_all_public_part*.txt"))
    if not files: files = glob.glob("master_*.txt")
    txt = ""
    for f in files:
        try: txt += open(f, 'r', encoding='utf-8', errors='ignore').read() + "\n"
        except: pass
    chunks = [c.strip() for c in txt.split("---CHUNK---") if len(c.strip())>80]
    return chunks

chunks = load_chunks()

@st.cache_resource
def build_tfidf(_chunks):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000, ngram_range=(1,2))
    tfidf_matrix = vectorizer.fit_transform(_chunks)
    return vectorizer, tfidf_matrix

vectorizer, tfidf_matrix = build_tfidf(chunks)

def get_best_chunks_smart(question, chunks, vectorizer, tfidf_matrix, top_k=2):
    good_idx = []
    for i, c in enumerate(chunks):
        if c.lower().count("annex") > 10 and len(c) < 3000: continue
        if c.lower().count("what is") > 5 and len(c) < 1000: continue
        good_idx.append(i)
    if not good_idx: good_idx = list(range(len(chunks)))
    sub_chunks = [chunks[i] for i in good_idx]
    sub_matrix = vectorizer.transform(sub_chunks)
    q_vec = vectorizer.transform([question])
    scores = (sub_matrix * q_vec.T).toarray().ravel()
    top = np.argsort(scores)[-top_k:][::-1]
    return [sub_chunks[i] for i in top]

# ---------- CHAT STATE WITH TIME ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Good Day i am assistant imo bot.. how can i help you", "time": datetime.now().strftime("%H:%M")}]
    # Try load from localStorage backup via JS injection (will be restored on next rerun if library present)
    if HAS_STORAGE:
        try:
            saved = localS.getItem("imo_chat_v2")
            if saved and isinstance(saved, list) and len(saved) > 1:
                st.session_state.messages = saved
        except: pass

# ---------- DISPLAY ----------
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in st.session_state.messages:
    role_class = "msg-user" if m["role"]=="user" else "msg-bot"
    t = m.get("time", datetime.now().strftime("%H:%M"))
    # Safe content
    content = m["content"].replace("<", "&lt;").replace(">", "&gt;")
    st.markdown(f'<div class="{role_class}">{content}<div class="msg-time">{t} ✓✓</div></div><div style="clear:both;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- GENERATION ----------
ALL_FLASH_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-1.5-flash-001", "gemini-flash-latest"]
def generate_with_fallback(client, prompt):
    for model_name in ALL_FLASH_MODELS:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response.text: return response.text
        except: continue
    return None

if prompt := st.chat_input("Type a message..."):
    now = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "content": prompt, "time": now})

    results = get_best_chunks_smart(prompt, chunks, vectorizer, tfidf_matrix, top_k=2)
    context = "\n\n---\n\n".join(results)[:5000]

    if gemini_ok and gemini_client:
        final_prompt = f"User asked: {prompt}\nContext: {context}\nINSTRUCTION: Give 3-5 lines specific answer only, no long index list. If only one Annex asked, give only that.\nAnswer:"
        ans = generate_with_fallback(gemini_client, final_prompt)
        answer = ans if ans else context[:2000]
    else:
        answer = context[:2000]

    now2 = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "assistant", "content": answer, "time": now2})

    # Save to storage
    if HAS_STORAGE:
        try: localS.setItem("imo_chat_v2", st.session_state.messages)
        except: pass

    st.rerun()

# ---------- JS BACKUP SAVE ----------
# This saves every render to browser localStorage so refresh pe backup rahe
st.components.v1.html(f"""
<script>
try {{
  const data = {json.dumps(st.session_state.messages)};
  localStorage.setItem('imo_chat_backup', JSON.stringify(data));
  localStorage.setItem('imo_chat_backup_time', new Date().toISOString());
}} catch(e) {{ console.log(e); }}
</script>
""", height=0)
