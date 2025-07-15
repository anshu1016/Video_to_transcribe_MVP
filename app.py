import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from moviepy import VideoFileClip
from dotenv import load_dotenv
from utils.audio_processor import process_audio_file

load_dotenv()

app = Flask(__name__)

# Configuration
BASE_FOLDER = 'media'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(BASE_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_video_to_audio(video_path, output_audio_path):
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(output_audio_path)
    return output_audio_path

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Video-to-Audio Transcription API"}), 200

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    file = request.files['video']
    language = request.form.get('language', 'en-IN')

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Create unique folder per request
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    uid = str(uuid.uuid4())[:6]
    session_folder = os.path.join(BASE_FOLDER, f"{timestamp}_{uid}")
    os.makedirs(session_folder, exist_ok=True)

    # Save video
    filename = secure_filename(file.filename)
    video_path = os.path.join(session_folder, filename)
    file.save(video_path)

    # Convert to audio
    audio_filename = "output_audio.wav"
    audio_path = os.path.join(session_folder, audio_filename)
    try:
        convert_video_to_audio(video_path, audio_path)
    except Exception as e:
        return jsonify({"error": f"Audio extraction failed: {str(e)}"}), 500

    # Transcribe audio
    try:
        transcript = process_audio_file(audio_path, language)
        transcript_path = os.path.join(session_folder, "transcript.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    return jsonify({
        "message": "Transcription completed successfully",
        "session_folder": session_folder,
        "video": filename,
        "audio": audio_filename,
        "transcript_file": "transcript.txt"
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
