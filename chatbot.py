from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

conversation_history = []

system_prompt = "Ti je asistent personal i zgjuar. Përgjigju shkurt dhe qartë."

def chat(user_message):
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation_history
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    assistant_message = response.choices[0].message.content
    
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message

def main():
    print("=" * 40)
    print("AI Assistant Personal - Groq")
    print("Shkruaj 'exit' per te dale")
    print("=" * 40)
    
    while True:
        user_input = input("Ti: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() == "exit":
            print("Mirupafshim!")
            break
        
        try:
            response = chat(user_input)
            print(f"AI: {response}\n")
        except Exception as e:
            print(f"Gabim: {e}\n")

if __name__ == "__main__":
    main()