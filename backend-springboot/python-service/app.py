from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import subprocess
import json
import logging
import time
from werkzeug.utils import secure_filename
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

from speech_to_text import SpeechToText
from summarizer import Summarizer
from task_extractor import TaskExtractor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Use local 'uploads' directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'flac', 'mp4', 'avi', 'mov'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize global Gemini configuration
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    logger.info("Gemini API configured globally.")
else:
    logger.warning("GEMINI_API_KEY IS MISSING! AI features will fail.")

# Shared model instance to save resources
try:
    # whisper fallback instance
    stt_fallback = SpeechToText() 
    summarizer = Summarizer()
    task_extractor = TaskExtractor()
    ai_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    logger.exception("Failed to initialize AI models: %s", str(e))
    stt_fallback = summarizer = task_extractor = ai_model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_audio_duration(filepath):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', filepath],
            capture_output=True, text=True, check=True, timeout=15
        )
        return float(json.loads(result.stdout)['format']['duration'])
    except:
        return 0.0

def wait_for_files_active(files):
    """Waits for Gemini files to be processed and active."""
    logger.info("Waiting for Gemini to process large audio file...")
    for f in files:
        file = genai.get_file(f.name)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(f.name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {f.name} failed to process: {file.state.name}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "api_key_set": bool(os.getenv("GEMINI_API_KEY"))})

@app.route('/process', methods=['POST'])
def process_lecture():
    temp_files = []
    gemini_files = []
    try:
        logger.info("Received /process request")
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        language = request.form.get('language', 'english')
        
        # Save locally
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        temp_files.append(filepath)
        
        file_size = os.path.getsize(filepath)
        logger.info(f"Processing file: {filename}, size: {file_size / (1024*1024):.2f} MB")

        duration = get_audio_duration(filepath)
        
        # 1. OPTIMIZATION: Use Direct Bytes for small files (< 20MB)
        # Use Gemini File API ONLY for large files (> 20MB)
        audio_content = None
        import mimetypes
        mimetypes.init()
        # Ensure m4a is recognized as mp4 which gemini likes
        mimetypes.add_type('audio/mp4', '.m4a')
        guessed_type, _ = mimetypes.guess_type(filename)
        mime_type = guessed_type if guessed_type or not filename.endswith('.m4a') else 'audio/mp4'
        
        if file_size < 20 * 1024 * 1024:
            logger.info(f"Using direct bytes for small file optimization ({mime_type})")
            with open(filepath, "rb") as f:
                audio_content = {
                    "mime_type": mime_type, 
                    "data": f.read()
                }
        else:
            logger.info("Using Gemini File API for large file processing.")
            g_file = genai.upload_file(path=filepath, display_name=filename)
            gemini_files.append(g_file)
            wait_for_files_active([g_file])
            audio_content = g_file

        # Safety configuration
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # ROBUST MODEL FALLBACK CHAIN
        def generate_with_fallback(prompt_list):
            # Prioritize 1.5 Flash as it is most stable for free tier
            models = ['gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-flash-latest']
            last_err = None
            for m_name in models:
                try:
                    logger.info(f"Attempting generation with model: {m_name}")
                    m = genai.GenerativeModel(m_name)
                    return m.generate_content(prompt_list, safety_settings=safety_settings)
                except Exception as e:
                    last_err = e
                    err_msg = str(e).lower()
                    if "quota" in err_msg or "429" in err_msg or "404" in err_msg:
                        logger.warning(f"Model {m_name} failed (quota/not found), trying next...")
                        continue
                    raise e
            raise last_err

        # 1. Summary
        logger.info("Generating summary...")
        summary_prompt = summarizer._get_prompt(language)
        s_response = generate_with_fallback([summary_prompt, audio_content])
        summary_text, key_points, topics = summarizer._parse_response(s_response.text)
        
        # 2. Tasks
        logger.info("Extracting tasks...")
        task_prompt = task_extractor._get_prompt()
        t_response = generate_with_fallback([task_prompt, audio_content])
        tasks = task_extractor._parse_tasks(t_response.text)

        # 3. Transcript
        logger.info("Generating transcript...")
        transcript = ""
        try:
            transcript_prompt = f"Provide a full, verbatim transcript of this audio in {language.capitalize()}. Return ONLY the transcript text."
            tr_response = generate_with_fallback([transcript_prompt, audio_content])
            transcript = tr_response.text
        except:
            logger.warning("Gemini transcript generation failed, falling back to local STT.")
            transcript = stt_fallback.transcribe(filepath, language[:2]) or "Summary generated successfully, but the full transcript was unavailable."

        return jsonify({
            "transcript": transcript,
            "summary": {
                "content": summary_text,
                "keyPoints": key_points,
                "topics": topics,
                "confidence": 95
            },
            "tasks": tasks,
            "durationSeconds": duration
        })

    except Exception as e:
        logger.exception("AI Process crash")
        err_msg = str(e).lower()
        if "quota" in err_msg or "429" in err_msg:
            return jsonify({
                "error": "AI_QUOTA_EXHAUSTED",
                "message": "The AI is currently at capacity (Free Tier limits reached). Please try again in 1-2 minutes."
            }), 429
        
        return jsonify({
            "error": "AI_INTERNAL_ERROR",
            "message": str(e)
        }), 500
    finally:
        for f in temp_files:
            try: os.remove(f)
            except: pass
        for f in gemini_files:
            try: genai.delete_file(f.name)
            except: pass

if __name__ == '__main__':
    print(f"GenAI SDK Version: {genai.__version__}")
    app.run(host='0.0.0.0', port=5000, debug=True)