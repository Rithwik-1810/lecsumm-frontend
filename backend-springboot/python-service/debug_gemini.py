import os
import google.generativeai as genai
from dotenv import load_dotenv
import traceback

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Available model: {m.name}")
    
    # Try the one I picked
    model_name = 'gemini-3.1-pro-preview'
    print(f"\nTesting model: {model_name}")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say test")
    print(f"Response: {response.text}")
    print("SUCCESS")
except Exception as e:
    print(f"ERROR with {model_name}: {e}")
    traceback.print_exc()
