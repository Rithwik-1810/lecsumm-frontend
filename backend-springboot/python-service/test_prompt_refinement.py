import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.1-pro-preview')

test_text = "good evening students i am here to announce about the assignment which is to submitted on 18th feb 2026 by 6pm the topic is based on neural networks"

prompt = f"""
Analyze the following lecture transcript and provide a concise, direct summary in English.

CRITICAL INSTRUCTIONS:
- BE CONCISE: Scale the summary length to match the transcript. If the transcript is very short, the summary MUST be 1-2 sentences maximum.
- ZERO FLUFF: Avoid introductory phrases ("This transcript handles...", "The speaker discusses..."). 
- STUDENT-FIRST: Provide only the essential facts, actionable information, and core concepts. 
- NO META-DESCRIPTION: Do not explain what is missing or analyzed; just summarize what IS there.

Provide the following structured JSON response:
1. "summary": A brief, professional summary (direct and factual).
2. "keyPoints": A list of the most important takeaways (max 5 items, brief).
3. "topics": A list of the main subject areas (max 3 items).

Return ONLY the raw JSON object with these three keys.

Transcript:
\"\"\"{test_text}\"\"\"
"""

try:
    response = model.generate_content(prompt)
    print("AI RESPONSE:")
    print(response.text)
except Exception as e:
    print(f"ERROR: {e}")
