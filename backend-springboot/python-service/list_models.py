import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    print(f"GenAI Version: {genai.__version__}")
    try:
        models = [m.name for m in genai.list_models()]
        print("Available Models:")
        for m in models:
            if 'flash' in m.lower():
                print(f" - {m}")
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("No GEMINI_API_KEY found in environment.")
