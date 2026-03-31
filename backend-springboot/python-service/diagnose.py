"""
Run this script to diagnose why the Gemini summary generation is failing.
Usage: python diagnose.py path/to/your/audio.m4a
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"[1] API Key loaded: {bool(api_key)} ({api_key[:8] + '...' if api_key else 'MISSING'})")

import google.generativeai as genai

genai.configure(api_key=api_key)
print("[2] Gemini configured.")

# Test 1: list available models
print("\n[3] Listing available models for generateContent...")
try:
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for m in models:
        print(f"    - {m}")
except Exception as e:
    print(f"    ERROR listing models: {e}")

# Test 2: try a simple text generation with gemini-1.5-pro
print("\n[4] Testing text generation with gemini-1.5-pro...")
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
    resp = model.generate_content("Say hello in one word.")
    print(f"    SUCCESS: {resp.text}")
except Exception as e:
    print(f"    ERROR: {e}")

# Test 3: if audio file provided, test audio summarization
if len(sys.argv) > 1:
    audio_path = sys.argv[1]
    print(f"\n[5] Testing audio summarization with: {audio_path}")
    if not os.path.exists(audio_path):
        print("    ERROR: File not found!")
    else:
        import mimetypes
        mimetypes.add_type('audio/mp4', '.m4a')
        mime, _ = mimetypes.guess_type(audio_path)
        print(f"    Detected MIME type: {mime}")
        
        file_size = os.path.getsize(audio_path)
        print(f"    File size: {file_size / (1024*1024):.2f} MB")
        
        try:
            with open(audio_path, "rb") as f:
                data = f.read()
            
            audio_content = {"mime_type": mime or "audio/mp4", "data": data}
            model = genai.GenerativeModel('gemini-1.5-pro')
            print("    Calling generate_content with audio...")
            resp = model.generate_content([
                "Summarize this audio in 2-3 sentences.",
                audio_content
            ])
            print(f"    SUCCESS: {resp.text[:300]}")
        except Exception as e:
            print(f"    ERROR during audio call: {e}")
            print(f"    Type: {type(e).__name__}")
else:
    print("\n[5] No audio file provided. Run with: python diagnose.py your_audio.m4a")
    print("    Skipping audio test.")

print("\n=== Diagnosis complete ===")
