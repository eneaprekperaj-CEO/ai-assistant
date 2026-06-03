import streamlit as st
import hashlib
import os
from datetime import datetime
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# ============================================
# KLIENTËT
# ============================================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ============================================
# FUNKSIONET E AUTENTIFIKIMIT
# ============================================
def hash_password(fjalekalimi):
    return hashlib.sha256(fjalekalimi.encode()).hexdigest()

def regjistro_perdorues(emri, email, fjalekalimi):
    try:
        result = supabase.table("perdoruesit").insert({
            "emri": emri,
            "email": email,
            "fjalekalimi": hash_password(fjalekalimi)
        }).execute()
        return True
    except:
        return False

def kycu_perdorues(email, fjalekalimi):
    result = supabase.table("perdoruesit").select("*").eq(
        "email", email
    ).eq(
        "fjalekalimi", hash_password(fjalekalimi)
    ).execute()
    
    if result.data:
        return result.data[0]
    return None

# ============================================
# FUNKSIONET E DETYRAVE
# ============================================
def shto_detyre(perdoruesi_id, titulli, pershkrimi, prioriteti):
    supabase.table("detyrat").insert({
        "perdoruesi_id": perdoruesi_id,
        "titulli": titulli,
        "pershkrimi": pershkrimi,
        "prioriteti": prioriteti
    }).execute()

def merr_detyrat(perdoruesi_id):
    result = supabase.table("detyrat").select("*").eq(
        "perdoruesi_id", perdoruesi_id
    ).order("data_krijimit", desc=True).execute()
    return result.data

def ndrysho_status(detyre_id, statusi_ri):
    supabase.table("detyrat").update({
        "statusi": statusi_ri
    }).eq("id", detyre_id).execute()

def fshi_detyre(detyre_id):
    supabase.table("detyrat").delete().eq("id", detyre_id).execute()

# ============================================
# AI ASSISTANT
# ============================================
def ai_prioritizo(detyrat):
    if not detyrat:
        return "Nuk ka detyra për të analizuar."
    
    lista = "\n".join([f"- {d['titulli']} ({d['prioriteti']})" for d in detyrat])
    
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
# INTERFACE
# ============================================
st.set_page_config(
    page_title="TaskAI — Task Manager",
    page_icon="✅",
    layout="wide"
)

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
# DASHBOARD
# ============================================
else:
    perdoruesi = st.session_state.perdoruesi
    
    with st.sidebar:
        st.success(f"👋 {perdoruesi['emri']}")
        st.markdown("---")
        
        st.subheader("➕ Detyrë e Re")
        titulli = st.text_input("Titulli")
        pershkrimi = st.text_area("Përshkrimi", height=100)
        prioriteti = st.selectbox(
            "Prioriteti",
            ["🔴 I Lartë", "🟡 Mesatar", "🟢 I Ulët"]
        )
        
        if st.button("Shto Detyrën", type="primary"):
            if titulli:
                shto_detyre(perdoruesi['id'], titulli, pershkrimi, prioriteti)
                st.success("✅ Detyra u shtua!")
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Dil"):
            st.session_state.perdoruesi = None
            st.rerun()
    
    st.title("✅ TaskAI Dashboard")
    
    detyrat = merr_detyrat(perdoruesi['id'])
    
    col1, col2, col3 = st.columns(3)
    aktive = [d for d in detyrat if d['statusi'] == "Aktive"]
    perfunduara = [d for d in detyrat if d['statusi'] == "Përfunduar"]
    
    with col1:
        st.metric("📋 Gjithsej", len(detyrat))
    with col2:
        st.metric("⚡ Aktive", len(aktive))
    with col3:
        st.metric("✅ Përfunduara", len(perfunduara))
    
    st.markdown("---")
    
    if st.button("🤖 AI — Prioritizo Detyrat"):
        with st.spinner("AI po analizon..."):
            analiza = ai_prioritizo(detyrat)
            st.info(f"🤖 **AI Këshilla:**\n\n{analiza}")
    
    st.markdown("---")
    st.subheader("📋 Detyrat e Mia")
    
    if not detyrat:
        st.info("Nuk ke detyra ende. Shto një nga sidebar!")
    else:
        for detyre in detyrat:
            with st.expander(f"{detyre['prioriteti']} {detyre['titulli']} — {detyre['statusi']}"):
                st.write(f"**Përshkrimi:** {detyre['pershkrimi'] or 'Pa përshkrim'}")
                st.write(f"**Krijuar:** {detyre['data_krijimit']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if detyre['statusi'] == "Aktive":
                        if st.button("✅ Përfundo", key=f"done_{detyre['id']}"):
                            ndrysho_status(detyre['id'], "Përfunduar")
                            st.rerun()
                    else:
                        if st.button("🔄 Rihap", key=f"reopen_{detyre['id']}"):
                            ndrysho_status(detyre['id'], "Aktive")
                            st.rerun()
                with col2:
                    if st.button("🗑️ Fshi", key=f"delete_{detyre['id']}"):
                        fshi_detyre(detyre['id'])
                        st.rerun()