import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import json
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Use safe characters for Windows terminal
def test_task_extraction(text):
    print(f"\n--- Testing Task Extraction ---\nInput: {text}")
    prompt = f"""
    Analyze the following lecture transcript and extract actionable tasks.
    DEADLINE EXTRACTION: You must deduce the exact deadline from the context.
    Current Date: {datetime.now().strftime("%Y-%m-%d")}.
    Return JSON array with: "title", "description", "priority", "deadline" (ISO 8601).
    Transcript: \"\"\"{text}\"\"\"
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            tasks = json.loads(match.group(0))
            print(f"SUCCESS: Extracted {len(tasks)} tasks:")
            print(json.dumps(tasks, indent=2))
        else:
            print("ERROR: No JSON found in response")
            print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

def test_summarization(text):
    print(f"\n--- Testing Summarization ---\nInput: {text}")
    prompt = f"""
    Summarize this transcript. Return JSON with: "summary", "keyPoints", "topics".
    Transcript: \"\"\"{text}\"\"\"
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            print("SUCCESS: Summary generated:")
            print(f"Summary length: {len(data['summary'])} chars")
            print(f"Key Points: {len(data['keyPoints'])}")
            print(f"Topics: {data['topics']}")
        else:
            print("ERROR: No JSON found in response")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    sample_text = """
    I am here to tell you about an assignment which is to be computed by 18th February 2026 up to 6 p.m. 
    The assignment is on neural networks. I repeat, 18th Feb 2026, 6:00 PM is the last date.
    """
    test_task_extraction(sample_text)
    test_summarization(sample_text)
