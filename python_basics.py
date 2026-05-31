import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def merr_motin(qyteti):
    url = f"https://api.openweathermap.org/data/2.5/weather"
    
    parametrat = {
        "q": qyteti,
        "appid": API_KEY,
        "units": "metric",
        "lang": "al"
    }
    
    response = requests.get(url, params=parametrat)
    
    if response.status_code == 200:
        data = response.json()
        
        temperatura = data["main"]["temp"]
        ndjesia = data["main"]["feels_like"]
        pershkrimi = data["weather"][0]["description"]
        lagështia = data["main"]["humidity"]
        era = data["wind"]["speed"]
        
        print(f"\n🌍 Moti në {qyteti.upper()}")
        print(f"{'='*30}")
        print(f"🌡️  Temperatura:  {temperatura}°C")
        print(f"🤔 Ndijimi:      {ndjesia}°C")
        print(f"☁️  Përshkrimi:   {pershkrimi}")
        print(f"💧 Lagështia:    {lagështia}%")
        print(f"💨 Era:          {era} m/s")
        
    elif response.status_code == 401:
        print("❌ API key jo e vlefshme — prit 10 minuta!")
    elif response.status_code == 404:
        print(f"❌ Qyteti '{qyteti}' nuk u gjet!")
    else:
        print(f"❌ Gabim: {response.status_code}")

def main():
    print("🌤️  WEATHER APP")
    print("="*30)
    
    while True:
        qyteti = input("\nShkruaj qytetin (ose 'exit'): ").strip()
        
        if qyteti.lower() == "exit":
            print("Mirupafshim! 👋")
            break
            
        if qyteti:
            merr_motin(qyteti)

if __name__ == "__main__":
    main()