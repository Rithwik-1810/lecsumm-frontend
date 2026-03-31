import google.generativeai as genai
import os
import json
import re
import time

class Summarizer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not found in environment variables.")

    def summarize(self, text, language='english'):
        """Generate summary, key points, and topics using Gemini 1.5 Flash"""
        if not text or len(text) < 50:
            return text, [], []

        if not self.model:
            return "AI Summarization unavailable (API Key missing).", [], []

        prompt = self._get_prompt(language, text)

        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Error generating summary with Gemini: {e}")
            return "Failed to generate summary.", [], []

    def summarize_audio(self, audio_file, language='english'):
        """Generate summary directly from audio file using Gemini Multimodal"""
        if not self.model:
            return "AI Summarization unavailable (API Key missing).", [], []

        prompt = self._get_prompt(language)
        
        try:
            # Generate content using the audio file and prompt
            response = self.model.generate_content([prompt, audio_file])
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Error generating audio summary with Gemini: {e}")
            return f"Failed to generate summary from audio: {str(e)}", [], []

    def _get_prompt(self, language, text=None):
        prompt = f"""
        Analyze the following lecture { 'transcript' if text else 'audio' } and provide a concise, direct summary in {language.capitalize()}.
        
        CRITICAL INSTRUCTIONS:
        - BE CONCISE: Scale the summary length to match the context.
        - ZERO FLUFF: Avoid introductory phrases ("This transcript handles...", "The speaker discusses..."). 
        - STUDENT-FIRST: Provide only the essential facts, actionable information, and core concepts. 
        - NO META-DESCRIPTION: Do not explain what is missing or analyzed; just summarize what IS there.
        
        Provide the following structured JSON response:
        1. "summary": A brief, professional summary (direct and factual).
        2. "keyPoints": A list of the most important takeaways (max 5 items, brief).
        3. "topics": A list of the main subject areas (max 3 items).

        Return ONLY the raw JSON object with these three keys.
        """
        if text:
            prompt += f"\n\nTranscript:\n\"\"\"{text}\"\"\""
        return prompt

    def _parse_response(self, text):
        try:
            # Remove markdown code formatting if present
            clean_json = re.sub(r'```(?:json)?\s*|\s*```', '', text).strip()
            match = re.search(r'\{.*\}', clean_json, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return data.get("summary", ""), data.get("keyPoints", []), data.get("topics", [])
            else:
                return text[:500] + "...", [], []
        except Exception as e:
            print(f"Parsing error: {e}")
            return text[:500] + "...", [], []