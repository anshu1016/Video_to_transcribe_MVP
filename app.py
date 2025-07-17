import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from moviepy import VideoFileClip
from dotenv import load_dotenv

from utils.audio_processor import process_audio_file
from utils.cloudinary_utils import upload_to_cloudinary
from utils.airtable_utils import sync_to_airtable

# Load env variables
load_dotenv()

app = Flask(__name__)
BASE_FOLDER = 'media'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024

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

    # Unique session
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    uid = str(uuid.uuid4())[:6]
    base_filename = f"{timestamp}_{uid}"
    session_folder = os.path.join(BASE_FOLDER, base_filename)
    os.makedirs(session_folder, exist_ok=True)
    cloudinary_folder = f"video_pipeline/{base_filename}"

    # Save video
    ext = os.path.splitext(file.filename)[1]
    video_filename = f"{base_filename}{ext}"
    video_path = os.path.join(session_folder, video_filename)
    file.save(video_path)

    # Convert to audio
    audio_filename = f"{base_filename}.wav"
    audio_path = os.path.join(session_folder, audio_filename)
    try:
        convert_video_to_audio(video_path, audio_path)
    except Exception as e:
        return jsonify({"error": f"Audio extraction failed: {str(e)}"}), 500

    # Transcribe
    transcript_filename = f"{base_filename}.txt"
    transcript_path = os.path.join(session_folder, transcript_filename)
    try:
        transcript = process_audio_file(audio_path, language)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    # Upload to Cloudinary
    try:
        video_url = upload_to_cloudinary(video_path, cloudinary_folder, base_filename, resource_type="video")
        audio_url = upload_to_cloudinary(audio_path, cloudinary_folder, base_filename + "_audio", resource_type="video")
        transcript_url = upload_to_cloudinary(transcript_path, cloudinary_folder, base_filename + "_transcript", resource_type="raw")
    except Exception as e:
        return jsonify({"error": f"Cloudinary upload failed: {str(e)}"}), 500

    # Sync to Airtable ✅ CORRECT CALL HERE
    try:
        airtable_record = sync_to_airtable(
            video_url=video_url,
            audio_url=audio_url,
            transcript_url=transcript_url,
            transcript_text=transcript
        )
    except Exception as e:
        return jsonify({"error": f"Airtable sync failed: {str(e)}"}), 500

    return jsonify({
        "message": "Transcription completed successfully",
        "session_id": base_filename,
        "video_url": video_url,
        "audio_url": audio_url,
        "transcribe_url": transcript_url,
        "transcript_text": transcript,
        "airtable_record_id": airtable_record.get("id", "unknown")
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
