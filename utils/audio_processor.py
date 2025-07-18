import os
import requests
import tempfile
import librosa
import numpy as np
from scipy.io import wavfile
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv('SARVAM_API_KEY')
SARVAM_API_ENDPOINT = 'https://api.sarvam.ai/speech-to-text'
CHUNK_DURATION = 30  # seconds

if not SARVAM_API_KEY:
    raise ValueError("SARVAM_API_KEY is not set in environment variables!")

def split_audio(audio_path):
    """Split audio into 30-second chunks using librosa and save with scipy."""
    y, sr = librosa.load(audio_path, sr=None)
    total_samples = len(y)
    samples_per_chunk = sr * CHUNK_DURATION

    chunks = []
    for start_sample in range(0, total_samples, samples_per_chunk):
        end_sample = min(start_sample + samples_per_chunk, total_samples)
        chunk = y[start_sample:end_sample]

        # Scale to 16-bit PCM for API compatibility
        chunk_pcm = np.int16(chunk / np.max(np.abs(chunk)) * 32767)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            wavfile.write(temp_file.name, sr, chunk_pcm)
            chunks.append(temp_file.name)
    
    return chunks

def transcribe_chunk(chunk_path, language):
    """Send chunk to Sarvam API."""
    headers = {
        'api-subscription-key': SARVAM_API_KEY
    }

    with open(chunk_path, 'rb') as audio_file:
        files = {'file': ('audio.wav', audio_file, 'audio/wav')}
        data = {
            'model': 'saarika:v2'
        }
        if language != 'unknown':
            data['language_code'] = language

        response = requests.post(SARVAM_API_ENDPOINT, headers=headers, files=files, data=data)

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}, {response.text}")

        return response.json().get('transcript', '')

def process_audio_file(audio_path, language):
    """Process full audio file and return final transcript."""
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)

    print(f"\n=== Audio File Info ===")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Sample Rate: {sr} Hz")
    print(f"========================\n")

    if duration <= CHUNK_DURATION:
        return transcribe_chunk(audio_path, language)

    # Else split & process chunks
    transcript = ""
    chunks = split_audio(audio_path)
    for chunk_path in chunks:
        try:
            chunk_transcript = transcribe_chunk(chunk_path, language)
            transcript += " " + chunk_transcript
        finally:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

    return transcript.strip()

# Example usage
if __name__ == "__main__":
    audio_path = "path_to_audio_file.wav"
    language = "en"
    
    try:
        full_transcript = process_audio_file(audio_path, language)
        print("\nTranscript:\n")
        print(full_transcript)
    except Exception as e:
        print(f"Error: {e}")
