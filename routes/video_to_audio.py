# import os
# import uuid
# from flask import Flask, request, jsonify
# from werkzeug.utils import secure_filename
# from moviepy import VideoFileClip  # ✅ FIXED
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configuration
# UPLOAD_FOLDER = 'uploads'
# AUDIO_OUTPUT_FOLDER = 'audio_outputs'
# ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

# # Ensure folders exist
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(AUDIO_OUTPUT_FOLDER, exist_ok=True)

# # Initialize Flask
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['AUDIO_OUTPUT_FOLDER'] = AUDIO_OUTPUT_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB

# # Helpers
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def convert_to_audio(video_path, output_format='mp3'):
#     filename = os.path.basename(video_path).rsplit('.', 1)[0]
#     audio_filename = f"{filename}_{uuid.uuid4().hex[:6]}.{output_format}"
#     audio_path = os.path.join(AUDIO_OUTPUT_FOLDER, audio_filename)

#     clip = VideoFileClip(video_path)
#     clip.audio.write_audiofile(audio_path)

#     return audio_path

# # Routes
# @app.route('/')
# def index():
#     return jsonify({"message": "Welcome to the Video to Audio Converter API"}), 200
# @app.route('/upload', methods=['POST'])
# def upload_video():
#     if 'video' not in request.files:
#         return jsonify({"error": "No video file part in the request"}), 400

#     file = request.files['video']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(video_path)

#         try:
#             audio_path = convert_to_audio(video_path, output_format='mp3')
#             return jsonify({
#                 "message": "Video converted successfully",
#                 "audio_path": audio_path
#             }), 200
#         except Exception as e:
#             return jsonify({"error": str(e)}), 500
#     else:
#         return jsonify({"error": "Unsupported file format"}), 400

# # Entry point
# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0', port=5000)


import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from moviepy import VideoFileClip
from werkzeug.utils import secure_filename
from utils.audio_processor import process_audio_file

video_audio_bp = Blueprint('video_audio', __name__)

MEDIA_FOLDER = 'media'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

os.makedirs(MEDIA_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@video_audio_bp.route('/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    language = request.form.get('language', 'en-IN')

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid or missing video file'}), 400

    # Unique directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:6]
    session_dir = os.path.join(MEDIA_FOLDER, f"{timestamp}_{unique_id}")
    os.makedirs(session_dir, exist_ok=True)

    # Save video
    video_filename = 'original_video.mp4'
    video_path = os.path.join(session_dir, video_filename)
    file.save(video_path)

    try:
        # Convert to audio
        audio_path = os.path.join(session_dir, 'output_audio.wav')
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path)

        # Transcribe audio
        transcript = process_audio_file(audio_path, language)
        transcript_path = os.path.join(session_dir, 'transcript.txt')

        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)

        return jsonify({
            'message': 'Video processed successfully',
            'media_folder': session_dir,
            'audio_file': 'output_audio.wav',
            'transcript_file': 'transcript.txt'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
