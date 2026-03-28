import os
import openai

# Configuration from User
PROXY_URL = "http://100.79.241.120:8045/v1"
API_KEY = "sk-83d6b377249445638f597ae9ea4657e7"

print(f"Testing connection to: {PROXY_URL}")

client = openai.OpenAI(
    base_url=PROXY_URL,
    api_key=API_KEY
)

try:
    print("--- Listing Models ---")
    models = client.models.list()
    for model in models.data:
        print(f"- {model.id}")
        
    print("\n--- Testing Generation (gemini-1.5-pro for reference) ---")
    # Trying a known model first, then we can try "gemini-3-pro" if listed
    response = client.chat.completions.create(
        model="gemini-1.5-pro", # Default fallback
        messages=[{"role": "user", "content": "Hello, are you Gemini?"}]
    )
    print(f"Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"Error: {e}")
