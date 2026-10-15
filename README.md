# 🚢 IMO RAG Bot - Hong Kong Convention & ISPS Assistant | 30 Docs | 7500+ Chunks

An open-source AI assistant for **Safe & Environmentally Sound Ship Recycling** and **Maritime Security** (SOLAS XI-2 / ISPS).

Built with **ChromaDB + Gemini + LangChain**. Uses only free public IMO Resolutions & Circulars.
**30 Docs | 7500+ Chunks | 100% Legal | BYOD Model | 1000% Bulletproof**

Ask in Hinglish: "Cybutryne ka limit?", "PFOS kab se banned?", "SRP me kya chahiye?", "Flag ko kab notify karna hai ISPS pe?", "DASR ka format?"

### 📚 Data Source - 100% Legal & Public (30 Docs Complete)
This repo DOES NOT contain copyrighted IMO books. We use only free IMO Resolutions & Circulars from imo.org. Your `data/` folder is private via `.gitignore` - 30 PDFs never go to GitHub.

**Hong Kong Convention - 17 Core (COMPLETE):**
- MEPC.196(62) SRP, MEPC.210(63) Safe Recycling, MEPC.211(63) Facility Authorization
- MEPC.222(64) Survey & Certification, MEPC.223(64) Inspection (PSC)
- MEPC.269(68) + MEPC.335(76) + MEPC.338(76) IHM Amendments
- MEPC.379(80) IHM Guidelines, MEPC.405(83) - Cybutryne 200mg/kg + IHM Update 2023
- MEPC.392(82) + MEPC.396(82) - HKC Entry into Force & Transitional Measures
- HKSRC.2/Circ.1 (2024) - Basel & HKC Transboundary Movement
- TM11 - Thresholds & Sampling (Asbestos, PFOS, Cybutryne, HBCDD, Lead etc)

**Maritime Security & Safety - 13 Docs:**
- SOLAS Chapter XI-2 - Special Measures for Maritime Security
- ISPS Code Part A (Mandatory) + Part B (Guidance)
- MSC.1/Circ.1191 + MSC/Circ.1097 - Company & Ship Security Officer Guidance
- ILO/IMO Code - Port Area Security, MSC.1/Circ.1305 - Security Risk Assessment
- A.1118(30) + A.741(18) - ISM & Flag State Audit
- MEPC.1/Circ.850 - EU SRR & HKC Overlap, AFS Convention + BWM Convention Overlap
- Total: 30 Docs | 7500+ Chunks

### How it Works? - BYOD Model
Code is mine, Data is yours. Put 30 PDFs in data/ folder..gitignore ensures they NEVER go to GitHub. Code chunks with LangChain 1000/200 and searches with ChromaDB + Gemini with source.

### Mobile GitHub Workflow
Upload 30 PDFs to data/ via GitHub App. app.py auto builds embeddings in chroma_db/ (also gitignored). Streamlit Cloud deploys public code only.

### Legal Note
For official rules always refer to imo.org. This is an educational RAG project.

Built with: Python, Streamlit, LangChain, ChromaDB, Google Gemini
