import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.getcwd())

from task_extractor import TaskExtractor
from summarizer import Summarizer

def test():
    load_dotenv()
    print(f"API Key present: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
    
    extractor = TaskExtractor()
    summ = Summarizer()
    
    transcript = """
    I am here to tell you about an assignment which is to be computed by 18th February 2026 up to 6 p.m. 
    Thank you. So, assignment is on the assignment it is based on when you run into a key.
    The assignment is specifically about neural networks and their applications in modern AI.
    I repeat, the deadline is February 18th, 2026, at 6:00 PM.
    """
    
    print("\n--- Testing Task Extraction ---")
    tasks = extractor.extract_tasks(transcript)
    import json
    print(json.dumps(tasks, indent=2))
    
    print("\n--- Testing Summarization ---")
    # We'll see if summarizer.py is still using Flan-T5
    summary, points, topics = summ.summarize(transcript)
    print(f"Summary: {summary}")
    print(f"Key Points: {points}")
    print(f"Topics: {topics}")

if __name__ == "__main__":
    test()
