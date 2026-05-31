from groq import Groq
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

# ============================================
# KLIENTËT
# ============================================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
WEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

# ============================================
# TOOLS — Çfarë mund të bëjë Agenti
# ============================================
def merr_motin(qyteti: str) -> str:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": qyteti,
        "appid": WEATHER_KEY,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return json.dumps({
            "qyteti": qyteti,
            "temperatura": data["main"]["temp"],
            "ndjesia": data["main"]["feels_like"],
            "pershkrimi": data["weather"][0]["description"],
            "lagështia": data["main"]["humidity"],
            "era": data["wind"]["speed"]
        })
    return json.dumps({"gabim": f"Qyteti '{qyteti}' nuk u gjet"})

def kalkulato(shprehja: str) -> str:
    try:
        rezultati = eval(shprehja)
        return json.dumps({"shprehja": shprehja, "rezultati": rezultati})
    except:
        return json.dumps({"gabim": "Shprehje e pavlefshme"})

# ============================================
# DEFINIMI I TOOLS PËR AI
# ============================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "merr_motin",
            "description": "Merr të dhënat e motit për një qytet",
            "parameters": {
                "type": "object",
                "properties": {
                    "qyteti": {
                        "type": "string",
                        "description": "Emri i qytetit"
                    }
                },
                "required": ["qyteti"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kalkulato",
            "description": "Kryen llogaritje matematikore",
            "parameters": {
                "type": "object",
                "properties": {
                    "shprehja": {
                        "type": "string",
                        "description": "Shprehja matematikore, p.sh. '15 * 24'"
                    }
                },
                "required": ["shprehja"]
            }
        }
    }
]

# ============================================
# MAPA E TOOLS
# ============================================
tools_mapa = {
    "merr_motin": merr_motin,
    "kalkulato": kalkulato
}

# ============================================
# FUNKSIONI KRYESOR I AGENTIT
# ============================================
def agent(pyetja: str) -> str:
    print(f"\n🤔 Duke menduar...")
    
    mesazhet = [
        {
            "role": "system",
            "content": """Ti je një asistent inteligjent me akses në tools.
Kur të pyesin për motin, përdor tool-in merr_motin.
Kur të pyesin për llogaritje, përdor tool-in kalkulato.
Përgjigju gjithmonë në shqip."""
        },
        {
            "role": "user", 
            "content": pyetja
        }
    ]
    
    # Hapi 1: AI mendon dhe vendos çfarë tool të përdorë
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=mesazhet,
        tools=tools,
        tool_choice="auto"
    )
    
    mesazh = response.choices[0].message
    
    # Hapi 2: Nëse AI dëshiron të përdorë tool
    if mesazh.tool_calls:
        # Shto përgjigjen e AI në histori
        mesazhet.append({
            "role": "assistant",
            "content": mesazh.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in mesazh.tool_calls
            ]
        })
        
        # Hapi 3: Ekzekuto çdo tool që kërkoi AI
        for tool_call in mesazh.tool_calls:
            emri_tool = tool_call.function.name
            argumentet = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Duke përdorur tool: {emri_tool}")
            print(f"   Argumentet: {argumentet}")
            
            # Thirr funksionin e duhur
            funksioni = tools_mapa[emri_tool]
            rezultati = funksioni(**argumentet)
            
            print(f"   Rezultati: {rezultati}")
            
            # Shto rezultatin e tool-it në histori
            mesazhet.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": rezultati
            })
        
        # Hapi 4: AI analizon rezultatin dhe përgjigjet
        print(f"💭 Duke formuluar përgjigjen...")
        
        response_final = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mesazhet
        )
        
        return response_final.choices[0].message.content
    
    # Nëse nuk ka nevojë për tool
    return mesazh.content

# ============================================
# LOOPI KRYESOR
# ============================================
def main():
    print("=" * 50)
    print("  🤖 AI AGENT — Me Weather & Kalkulator")
    print("  Shkruaj 'exit' për të dalë")
    print("=" * 50)
    print("\nMund të më pyesësh për:")
    print("  • Motin në çdo qytet")
    print("  • Llogaritje matematikore")
    print("  • Kombinime të të dyjave!")
    
    while True:
        pyetja = input("\nTi: ").strip()
        
        if not pyetja:
            continue
            
        if pyetja.lower() == "exit":
            print("Mirupafshim! 👋")
            break
        
        try:
            pergjigja = agent(pyetja)
            print(f"\n🤖 Agent: {pergjigja}")
        except Exception as e:
            print(f"❌ Gabim: {e}")

if __name__ == "__main__":
    main()