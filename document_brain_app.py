import streamlit as st
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import tempfile
import os

load_dotenv()

# ================================
# SETUP
# ================================
st.set_page_config(page_title="Document Brain", page_icon="🧠", layout="wide")
st.title("🧠 Document Brain")
st.caption("Upload çdo PDF dhe chat me të!")

# ================================
# INITIALIZE — ruaj në session
# ================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "db" not in st.session_state:
    st.session_state.db = None
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None

# ================================
# SIDEBAR — Upload PDF
# ================================
with st.sidebar:
    st.header("📄 Ngarko Dokumentin")
    uploaded_file = st.file_uploader("Zgjidh PDF", type="pdf")
    
    if uploaded_file and uploaded_file.name != st.session_state.doc_name:
        with st.spinner("🔄 Duke procesuar PDF..."):
            
            # Ruaj PDF përkohësisht
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            
            # Ngarko dhe proceso
            loader = PyPDFLoader(tmp_path)
            dokumentet = loader.load()
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500, 
                chunk_overlap=50
            )
            chunks = splitter.split_documents(dokumentet)
            
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            st.session_state.db = Chroma.from_documents(chunks, embeddings)
            st.session_state.doc_name = uploaded_file.name
            st.session_state.chat_history = []
            
            os.unlink(tmp_path)
        
        st.success(f"✅ {uploaded_file.name} u ngarkua!")
        st.info(f"📊 {len(chunks)} pjesë të analizuara")
    
    if st.session_state.doc_name:
        st.divider()
        st.markdown(f"**Dokumenti aktiv:**\n{st.session_state.doc_name}")

# ================================
# CHAT INTERFACE
# ================================
if st.session_state.db is None:
    st.info("👈 Ngarko një PDF nga sidebar për të filluar!")
    
else:
    # Shfaq historinë e chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Input pyetja
    pyetja = st.chat_input("Pyet diçka për dokumentin...")
    
    if pyetja:
        # Shfaq pyetjen
        with st.chat_message("user"):
            st.write(pyetja)
        st.session_state.chat_history.append({
            "role": "user", 
            "content": pyetja
        })
        
        # Gjej përgjigjen
        with st.chat_message("assistant"):
            with st.spinner("🧠 Duke menduar..."):
                
                # Kërko në PDF
                rezultatet = st.session_state.db.similarity_search(pyetja, k=3)
                konteksti = "\n".join([r.page_content for r in rezultatet])
                
                # AI përgjigjet
                llm = ChatGroq(model="llama-3.1-8b-instant")
                prompt = f"""Bazuar në dokumentin:

{konteksti}

Përgjigju pyetjes: {pyetja}
Përgjigju shkurt, saktë dhe në shqip."""

                pergjigje = llm.invoke(prompt)
                rezultati = pergjigje.content
                
            st.write(rezultati)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": rezultati
        })