import google.generativeai as genai
import json
import re
import os
from datetime import datetime

class TaskExtractor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not found in environment variables.")

    def extract_tasks(self, text):
        """Extract tasks and deadlines from text using Gemini 1.5 Flash"""
        if not self.model:
            return self._fallback_extraction(text)

        prompt = self._get_prompt(text)

        try:
            response = self.model.generate_content(prompt)
            return self._parse_tasks(response.text)
        except Exception as e:
            print(f"Error extracting tasks with Gemini: {e}")
            return self._fallback_extraction(text)

    def extract_tasks_from_audio(self, audio_file):
        """Extract tasks directly from audio using Gemini Multimodal"""
        if not self.model:
            return []

        prompt = self._get_prompt()

        try:
            response = self.model.generate_content([prompt, audio_file])
            return self._parse_tasks(response.text)
        except Exception as e:
            print(f"Error extracting audio tasks with Gemini: {e}")
            return []

    def _get_prompt(self, text=None):
        prompt = f"""
        You are an intelligent task extraction assistant. Analyze the following lecture { 'transcript' if text else 'audio' } and extract actionable tasks and assignments.
        
        CRITICAL INSTRUCTIONS:
        - BE DIRECT: Extract ONLY what is explicitly mentioned. Do not add meta-commentary.
        - CONCISE TITLES: Generate very brief, 2-4 word titles (e.g., "Neural Networks Assignment").
        - SIMPLE DESCRIPTIONS: Limit descriptions to one clear, actionable sentence.
        - AUTOMATED DEADLINE EXTRACTION: Deduce the exact deadline from the context.
          - Current Date: {datetime.now().strftime("%Y-%m-%d")}.
          - Default time to 18:00:00 if no specific time is mentioned.
        - ZERO HALLUCINATION: If a detail isn't clear, don't guess.

        For each task, provide:
        1. "title": Short, unique name.
        2. "description": One simple sentence summary.
        3. "priority": "High", "Medium", or "Low".
        4. "deadline": ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

        Return the result ONLY as a JSON array of objects. If no tasks are found, return [].
        """
        if text:
            prompt += f"\n\nTranscript:\n\"\"\"{text}\"\"\""
        return prompt

    def _parse_tasks(self, text):
        try:
            # Remove markdown code formatting if present
            clean_json = re.sub(r'```(?:json)?\s*|\s*```', '', text).strip()
            # Extract the array part specifically
            match = re.search(r'\[.*\]', clean_json, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []
        except Exception as e:
            print(f"Parsing error: {e}")
            return []

    def _fallback_extraction(self, text):
        """Simple rule-based fallback if Gemini is unavailable"""
        tasks = []
        keywords = ['assignment', 'homework', 'project', 'quiz', 'exam', 'submit', 'due']
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(kw in sentence.lower() for kw in keywords):
                tasks.append({
                    "title": sentence[:50] + "...",
                    "description": sentence,
                    "priority": "Medium",
                    "deadline": None
                })
        return tasks[:5]