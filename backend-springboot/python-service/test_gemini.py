import os
import google.generativeai as genai
from dotenv import load_dotenv
import pydantic
import inspect

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"GenAI version: {genai.__version__}")
print(f"Pydantic version: {pydantic.__version__}")
print(f"GenAI file: {genai.__file__}")

try:
    # Inspect GenerativeModel constructor
    sig = inspect.signature(genai.GenerativeModel)
    print(f"GenerativeModel signature: {sig}")
    
    genai.configure(api_key=api_key)
    
    # Try different initialization styles
    styles = [
        {"model_name": "gemini-1.5-flash-latest"},
        {"model_name": "models/gemini-1.5-flash-latest"},
        # Add 'model' if it's actually looking for a field named 'model'
        {"model": "gemini-1.5-flash-latest"} 
    ]
    
    for style in styles:
        print(f"\nTrying style: {style}")
        try:
            model = genai.GenerativeModel(**style)
            print(f"SUCCESS with {style}!")
            # Try a quick test
            res = model.generate_content("test")
            print("Generation test passed.")
            break
        except Exception as e:
            print(f"FAILED style {style}: {e}")
            
except Exception as e:
    print(f"Global Error: {e}")
    import traceback
    traceback.print_exc()
Line 18: pass
