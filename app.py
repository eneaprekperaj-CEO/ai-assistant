import streamlit as st
from groq import Groq
import requests
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
WEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

# ============================================
# KONFIGURIMI I FAQES
# ============================================
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Assistant Personal")
st.markdown("---")

# ============================================
# SIDEBAR — Menyja anësore
# ============================================
with st.sidebar:
    st.header("⚙️ Opsionet")
    
    mode = st.selectbox(
        "Zgjidh modalitetin:",
        ["💬 Chatbot", "🌤️ Moti"]
    )
    
    st.markdown("---")
    st.markdown("**Ndërtuar me:**")
    st.markdown("- Python 🐍")
    st.markdown("- Streamlit 🌊")
    st.markdown("- Groq AI ⚡")

# ============================================
# MODALITETI 1 — CHATBOT
# ============================================
if mode == "💬 Chatbot":
    st.header("💬 Chatbot AI")
    
    if "mesazhet" not in st.session_state:
        st.session_state.mesazhet = []
    
    for mesazh in st.session_state.mesazhet:
        with st.chat_message(mesazh["role"]):
            st.write(mesazh["content"])
    
    if pyetja := st.chat_input("Shkruaj diçka..."):
        st.session_state.mesazhet.append({
            "role": "user",
            "content": pyetja
        })
        
        with st.chat_message("user"):
            st.write(pyetja)
        
        with st.chat_message("assistant"):
            with st.spinner("Duke menduar..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Ti je asistent personal i zgjuar. Përgjigju shkurt dhe qartë."},
                        *st.session_state.mesazhet
                    ]
                )
                pergjigja = response.choices[0].message.content
                st.write(pergjigja)
        
        st.session_state.mesazhet.append({
            "role": "assistant",
            "content": pergjigja
        })

# ============================================
# MODALITETI 2 — MOTI
# ============================================
elif mode == "🌤️ Moti":
    st.header("🌤️ Weather App")
    
    qyteti = st.text_input("Shkruaj qytetin:", placeholder="p.sh. Paris, London, Tirana")
    
    if st.button("🔍 Kërko Motin"):
        if qyteti:
            with st.spinner("Duke kërkuar..."):
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "q": qyteti,
                    "appid": WEATHER_KEY,
                    "units": "metric"
                }
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "🌡️ Temperatura",
                            f"{data['main']['temp']}°C",
                            f"Ndijimi: {data['main']['feels_like']}°C"
                        )
                    
                    with col2:
                        st.metric(
                            "💧 Lagështia",
                            f"{data['main']['humidity']}%"
                        )
                    
                    with col3:
                        st.metric(
                            "💨 Era",
                            f"{data['wind']['speed']} m/s"
                        )
                    
                    st.info(f"☁️ Përshkrimi: {data['weather'][0]['description'].capitalize()}")
                    
                else:
                    st.error(f"❌ Qyteti '{qyteti}' nuk u gjet!")
        else:
            st.warning("⚠️ Shkruaj një qytet!")