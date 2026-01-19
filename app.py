import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# --- LIBRARIES ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader

# --- REPORTING ---
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# --- LOCAL MODULES ---
from rag_pipeline import get_retriever, load_and_vectorize

# --- CONFIG ---
load_dotenv()
st.set_page_config(page_title="Vibeguard Pro", page_icon="⚖️", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .header-style { font-size:24px; font-weight:bold; color:#2c3e50; margin-bottom:10px; }
    .metric-box {
        background-color: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center;
        border-top: 4px solid #004aad;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF REPORT GENERATOR (HOLISTIC) ---
def generate_holistic_report(client_name, url, scores, findings):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # 1. Letterhead
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, 750, "Vibeguard Pro - 360° Compliance Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, 730, f"Generated for: {client_name}")
    c.drawString(50, 715, f"Date: {datetime.now().strftime('%d-%b-%Y')}")
    c.line(50, 700, 550, 700)
    
    # 2. Executive Summary
    total_score = sum(scores.values()) // 4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 670, f"Overall Compliance Score: {total_score}/100")
    
    # 3. Category Breakdown
    y = 640
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Domain Breakdown:")
    y -= 25
    c.setFont("Helvetica", 12)
    for domain, score in scores.items():
        c.drawString(70, y, f"• {domain}: {score}/100")
        y -= 20
        
    # 4. Detailed Findings
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Critical Gaps & Recommendations:")
    y -= 25
    c.setFont("Helvetica", 10)
    
    if not findings:
        c.drawString(70, y, "No critical gaps detected via web scan.")
    else:
        for item in findings:
            if y < 100: # New page if full
                c.showPage()
                y = 750
            c.drawString(70, y, f"- {item}")
            y -= 15
            
    # 5. Advocate Signature
    c.line(50, 150, 550, 150)
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 135, "Digitally Audited by Vibeguard Pro Engine.")
    c.drawString(50, 115, "Advocate Signature: __________________________")
    
    c.save()
    buffer.seek(0)
    return buffer

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Vibeguard Pro")
    st.caption("Holistic Compliance | v3.0")
    
    st.info("💡 **Advocate's Tip:**\nUpload specific Acts (Env Protection, Export Control list) to the 'documents' folder to train the AI on new domains.")
    
    if st.button("🔄 Sync All Acts"):
        with st.spinner("Indexing Legal Library..."):
            if load_and_vectorize():
                st.success("Knowledge Base Updated!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("No PDFs found.")

# --- MAIN APP ---
if "messages" not in st.session_state: st.session_state.messages = []
if "scores" not in st.session_state: 
    st.session_state.scores = {"Data Privacy": 0, "Environment": 0, "Export/Trade": 0, "PSU/MSME": 0}
if "findings" not in st.session_state: st.session_state.findings = []

tab1, tab2, tab3 = st.tabs(["🌐 360° Web Audit", "📄 Report Generation", "🤖 Multi-Law Consultant"])

# === TAB 1: HOLISTIC SCANNER (FIXED) ===
with tab1:
    st.markdown('<p class="header-style">🌐 360° Regulatory Scanner</p>', unsafe_allow_html=True)
    target_url = st.text_input("Enter MSME Website URL", placeholder="https://example-msme.com")
    
    if st.button("🚀 Run Holistic Scan"):
        if target_url:
            with st.spinner("Auditing Data, Environment, Export & PSU parameters..."):
                try:
                    # 1. SETUP: Disguise as a Browser & Ignore SSL Errors
                    # This header makes the website think a human is visiting via Chrome
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                    }
                    
                    # 2. INITIALIZE LOADER WITH OPTIONS
                    loader = WebBaseLoader(target_url)
                    
                    # Apply the disguise and settings
                    loader.session.headers.update(headers)
                    loader.session.verify = False       # Ignore SSL certificate errors (common in MSMEs)
                    loader.requests_kwargs = {"timeout": 10} # Prevent freezing if site is slow
                    
                    # 3. LOAD DATA
                    docs = loader.load()
                    text = docs[0].page_content.lower()[:10000]
                    
                    # --- DOMAIN 1: DATA PRIVACY ---
                    dp_score = 0
                    if "privacy" in text: dp_score += 50
                    if "terms" in text: dp_score += 50
                    
                    # --- DOMAIN 2: ENVIRONMENT ---
                    env_score = 0
                    if "iso 14001" in text or "environment" in text: env_score += 50
                    if "waste" in text or "sustainability" in text: env_score += 50
                    
                    # --- DOMAIN 3: EXPORT / TRADE ---
                    ex_score = 0
                    if "iec" in text or "import" in text: ex_score += 50 # IEC Code check
                    if "export" in text: ex_score += 50
                    
                    # --- DOMAIN 4: PSU / MSME RESERVATION ---
                    psu_score = 0
                    # Checks if they display Udyam to claim PSU benefits
                    if "udyam" in text or "msme" in text: psu_score += 100 
                    
                    # Findings Log
                    findings = []
                    if dp_score < 100: findings.append("Data Privacy: Missing Policy or Terms.")
                    if env_score < 50: findings.append("Environment: No mention of ISO 14001 or Sustainability.")
                    if ex_score < 50: findings.append("Trade: IEC Code or Export declarations missing.")
                    if psu_score < 100: findings.append("PSU Benefits: Udyam Registration number not displayed (Risk of losing PSU tenders).")

                    # Update State
                    st.session_state.scores = {
                        "Data Privacy": dp_score,
                        "Environment": env_score,
                        "Export/Trade": ex_score,
                        "PSU/MSME": psu_score
                    }
                    st.session_state.findings = findings
                    st.success("Audit Complete!")
                    
                except Exception as e:
                    st.error(f"Scan failed: {e}")

    # Display Live Results
    c1, c2, c3, c4 = st.columns(4)
    scores = st.session_state.scores
    
    c1.markdown(f'<div class="metric-box"><h5>Data Privacy</h5><h2>{scores["Data Privacy"]}%</h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><h5>Environment</h5><h2>{scores["Environment"]}%</h2></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><h5>Export/Trade</h5><h2>{scores["Export/Trade"]}%</h2></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-box"><h5>PSU/MSME</h5><h2>{scores["PSU/MSME"]}%</h2></div>', unsafe_allow_html=True)

# === TAB 2: ADVOCATE REPORT ===
with tab2:
    st.markdown('<p class="header-style">📄 Advocate Audit Report</p>', unsafe_allow_html=True)
    st.info("Generate a signed compliance report for your client.")
    
    client_name = st.text_input("Client Name", "Client Corp")
    
    if st.button("Generate & Download PDF"):
        pdf = generate_holistic_report(client_name, "Scanned URL", st.session_state.scores, st.session_state.findings)
        st.download_button(
            label="⬇️ Download Signed Report",
            data=pdf,
            file_name="Vibeguard_Holistic_Audit.pdf",
            mime="application/pdf"
        )

# === TAB 3: AI CONSULTANT ===
with tab3:
    st.subheader("💬 Multi-Law Consultant")
    st.caption("Answers based on ALL uploaded Acts (Env, Export, DPDPA, etc.)")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask: 'Does the Environment Act apply to my factory?'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            retriever = get_retriever()
            if not retriever:
                st.warning("⚠️ Database empty.")
            else:
                try:
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
                    
                    # Template adjusted for multiple laws
                    template = """You are Vibeguard, a Multi-Domain Legal Compliance Expert.
                    Answer based ONLY on the context below. If the context covers Environmental, Export, or Data laws, use them.
                    
                    Context:
                    {context}
                    
                    Question: {input}
                    """
                    prompt_template = ChatPromptTemplate.from_template(template)
                    
                    chain = (
                        RunnablePassthrough.assign(context=lambda x: retriever.invoke(x["input"]))
                        | prompt_template
                        | llm
                        | StrOutputParser()
                    )
                    response = chain.invoke({"input": prompt})
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {e}")