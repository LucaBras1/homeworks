import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Načtení environment variables
load_dotenv()

# Inicializace OpenAI klienta
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_bitcoin_price():
    """Získá aktuální cenu Bitcoinu z CoinGecko API"""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        data = response.json()
        price = data["bitcoin"]["usd"]
        return {"bitcoin_price_usd": price}
    except Exception as e:
        return {"error": f"Nepodařilo se získat cenu Bitcoinu: {str(e)}"}

# Definice nástroje pro OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_bitcoin_price",
            "description": "Získá aktuální cenu Bitcoinu v USD",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    }
]

# Mapování funkcí
available_functions = {
    "get_bitcoin_price": get_bitcoin_price,
}

def chat_with_tools(user_message):
    """Hlavní funkce pro chat s nástroji"""
    messages = [
        {"role": "system", "content": "Jsi specialista na kryptoměny. Když se uživatel zeptá na aktuální cenu Bitcoinu, použij nástroj get_bitcoin_price."},
        {"role": "user", "content": user_message}
    ]
    
    # První volání LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    # Pokud LLM chce použít nástroj
    if response_message.tool_calls:
        messages.append({
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": response_message.tool_calls
        })
        
        # Zavolání nástroje
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_response = available_functions[function_name]()
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response),
            })
        
        # Druhé volání LLM s výsledkem nástroje
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        return final_response.choices[0].message.content
    
    return response_message.content

if __name__ == "__main__":
    print("🚀 Bitcoin Price Agent")
    print("Zeptej se na cenu Bitcoinu!")
    
    while True:
        user_input = input("\nTvůj dotaz (nebo 'quit' pro ukončení): ")
        
        if user_input.lower() in ['quit', 'exit', 'konec']:
            break
            
        try:
            response = chat_with_tools(user_input)
            print(f"\n🤖 Odpověď: {response}")
        except Exception as e:
            print(f"❌ Chyba: {e}")
    
    print("Nashledanou!")
