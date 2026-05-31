import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ============================================
# DATABASE SETUP
# ============================================
def init_db():
    """Inicializo databazën dhe krijo tabelat"""
    conn = sqlite3.connect("saas.db")
    cursor = conn.cursor()
    
    # Tabela e përdoruesve
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perdoruesit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            fjalekalimi TEXT NOT NULL,
            data_regjistrimit TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela e detyrave
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detyrat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perdoruesi_id INTEGER,
            titulli TEXT NOT NULL,
            pershkrimi TEXT,
            prioriteti TEXT DEFAULT 'Mesatar',
            statusi TEXT DEFAULT 'Aktive',
            data_krijimit TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (perdoruesi_id) REFERENCES perdoruesit(id)
        )
    """)
    
    conn.commit()
    conn.close()

# ============================================
# FUNKSIONET E AUTENTIFIKIMIT
# ============================================
def hash_password(fjalekalimi):
    """Enkripto fjalëkalimin"""
    return hashlib.sha256(fjalekalimi.encode()).hexdigest()

def regjistro_perdorues(emri, email, fjalekalimi):
    """Regjistro përdorues të ri"""
    try:
        conn = sqlite3.connect("saas.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO perdoruesit (emri, email, fjalekalimi) VALUES (?, ?, ?)",
            (emri, email, hash_password(fjalekalimi))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def kycu_perdorues(email, fjalekalimi):
    """Kyç përdoruesin"""
    conn = sqlite3.connect("saas.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM perdoruesit WHERE email=? AND fjalekalimi=?",
        (email, hash_password(fjalekalimi))
    )
    perdoruesi = cursor.fetchone()
    conn.close()
    return perdoruesi

# ============================================
# FUNKSIONET E DETYRAVE
# ============================================
def shto_detyre(perdoruesi_id, titulli, pershkrimi, prioriteti):
    """Shto detyrë të re"""
    conn = sqlite3.connect("saas.db")
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO detyrat 
        (perdoruesi_id, titulli, pershkrimi, prioriteti) 
        VALUES (?, ?, ?, ?)""",
        (perdoruesi_id, titulli, pershkrimi, prioriteti)
    )
    conn.commit()
    conn.close()

def merr_detyrat(perdoruesi_id):
    """Merr të gjitha detyrat e përdoruesit"""
    conn = sqlite3.connect("saas.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM detyrat WHERE perdoruesi_id=? ORDER BY data_krijimit DESC",
        (perdoruesi_id,)
    )
    detyrat = cursor.fetchall()
    conn.close()
    return detyrat

def ndrysho_status(detyre_id, statusi_ri):
    """Ndrysho statusin e detyrës"""
    conn = sqlite3.connect("saas.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE detyrat SET statusi=? WHERE id=?",
        (statusi_ri, detyre_id)
    )
    conn.commit()
    conn.close()

def fshi_detyre(detyre_id):
    """Fshi detyrën"""
    conn = sqlite3.connect("saas.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detyrat WHERE id=?", (detyre_id,))
    conn.commit()
    conn.close()

# ============================================
# AI ASSISTANT PËR DETYRAT
# ============================================
def ai_prioritizo(detyrat):
    """AI analizon dhe prioritizon detyrat"""
    if not detyrat:
        return "Nuk ka detyra për të analizuar."
    
    lista = "\n".join([f"- {d[2]} ({d[4]})" for d in detyrat])
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analizoji këto detyra dhe më jep këshilla se cilat duhen bërë fillimisht dhe pse:
            
{lista}

Ji konciz dhe praktik. Përgjigju në shqip."""
        }]
    )
    return response.choices[0].message.content

# ============================================
# INTERFACE KRYESORE
# ============================================
st.set_page_config(
    page_title="TaskAI — Task Manager",
    page_icon="✅",
    layout="wide"
)

# Inicializo databazën
init_db()

# Inicializo session state
if "perdoruesi" not in st.session_state:
    st.session_state.perdoruesi = None

# ============================================
# LOGIN / SIGNUP
# ============================================
if not st.session_state.perdoruesi:
    st.title("✅ TaskAI")
    st.subheader("Task Manager me AI")
    
    tab1, tab2 = st.tabs(["🔑 Kyçu", "📝 Regjistrohu"])
    
    with tab1:
        st.subheader("Kyçu në llogari")
        email = st.text_input("Email", key="login_email")
        fjalekalimi = st.text_input("Fjalëkalimi", type="password", key="login_pass")
        
        if st.button("Kyçu", type="primary"):
            perdoruesi = kycu_perdorues(email, fjalekalimi)
            if perdoruesi:
                st.session_state.perdoruesi = perdoruesi
                st.rerun()
            else:
                st.error("❌ Email ose fjalëkalim i gabuar!")
    
    with tab2:
        st.subheader("Krijo llogari të re")
        emri_i_ri = st.text_input("Emri", key="reg_emri")
        email_i_ri = st.text_input("Email", key="reg_email")
        fjalekalimi_i_ri = st.text_input("Fjalëkalimi", type="password", key="reg_pass")
        
        if st.button("Regjistrohu", type="primary"):
            if emri_i_ri and email_i_ri and fjalekalimi_i_ri:
                if regjistro_perdorues(emri_i_ri, email_i_ri, fjalekalimi_i_ri):
                    st.success("✅ Llogaria u krijua! Kyçu tani.")
                else:
                    st.error("❌ Email ekziston tashmë!")
            else:
                st.warning("⚠️ Plotëso të gjitha fushat!")

# ============================================
# DASHBOARD KRYESORE
# ============================================
else:
    perdoruesi = st.session_state.perdoruesi
    
    # Sidebar
    with st.sidebar:
        st.success(f"👋 {perdoruesi[1]}")
        st.markdown("---")
        
        # Shto detyrë të re
        st.subheader("➕ Detyrë e Re")
        titulli = st.text_input("Titulli")
        pershkrimi = st.text_area("Përshkrimi", height=100)
        prioriteti = st.selectbox(
            "Prioriteti",
            ["🔴 I Lartë", "🟡 Mesatar", "🟢 I Ulët"]
        )
        
        if st.button("Shto Detyrën", type="primary"):
            if titulli:
                shto_detyre(perdoruesi[0], titulli, pershkrimi, prioriteti)
                st.success("✅ Detyra u shtua!")
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Dil"):
            st.session_state.perdoruesi = None
            st.rerun()
    
    # Dashboard kryesore
    st.title(f"✅ TaskAI Dashboard")
    
    detyrat = merr_detyrat(perdoruesi[0])
    
    # Statistikat
    col1, col2, col3 = st.columns(3)
    aktive = [d for d in detyrat if d[6] == "Aktive"]
    perfunduara = [d for d in detyrat if d[6] == "Përfunduar"]
    
    with col1:
        st.metric("📋 Gjithsej", len(detyrat))
    with col2:
        st.metric("⚡ Aktive", len(aktive))
    with col3:
        st.metric("✅ Përfunduara", len(perfunduara))
    
    st.markdown("---")
    
    # AI Analiza
    if st.button("🤖 AI — Prioritizo Detyrat"):
        with st.spinner("AI po analizon..."):
            analiza = ai_prioritizo(detyrat)
            st.info(f"🤖 **AI Këshilla:**\n\n{analiza}")
    
    st.markdown("---")
    
    # Lista e detyrave
    st.subheader("📋 Detyrat e Mia")
    
    if not detyrat:
        st.info("Nuk ke detyra ende. Shto një nga sidebar!")
    else:
        for detyre in detyrat:
            with st.expander(f"{detyre[4]} {detyre[2]} — {detyre[6]}"):
                st.write(f"**Përshkrimi:** {detyre[3] or 'Pa përshkrim'}")
                st.write(f"**Krijuar:** {detyre[6]}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if detyre[6] == "Aktive":
                        if st.button("✅ Përfundo", key=f"done_{detyre[0]}"):
                            ndrysho_status(detyre[0], "Përfunduar")
                            st.rerun()
                    else:
                        if st.button("🔄 Rihap", key=f"reopen_{detyre[0]}"):
                            ndrysho_status(detyre[0], "Aktive")
                            st.rerun()
                with col2:
                    if st.button("🗑️ Fshi", key=f"delete_{detyre[0]}"):
                        fshi_detyre(detyre[0])
                        st.rerun()