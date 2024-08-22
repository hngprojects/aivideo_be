
from deep_translator import GoogleTranslator
import subprocess
import speech_recognition as sr
from io import BytesIO
from pydub import AudioSegment
from typing import Union
import json

def format_time(ms):
    """Convert milliseconds to mm:ss format."""
    seconds = ms / 1000
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def preprocess_audio_with_ffmpeg(audio_file_path):
    try:
        process = subprocess.Popen(
            ['ffmpeg', '-i', audio_file_path, '-f', 'wav', 'pipe:1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        wav_audio, error = process.communicate()

        if process.returncode != 0:
            raise Exception(f"ffmpeg failed with error code {process.returncode}: {error.decode()}")

        return wav_audio
    except Exception as e:
        print(f"Error in preprocess_audio_with_ffmpeg: {e}")
        raise

def transcribe_audio_file_with_timestamps(audio_file_path):
    recognizer = sr.Recognizer()
    transcriptions = {}
    
    try:
        wav_audio = preprocess_audio_with_ffmpeg(audio_file_path)
        
        audio_file = BytesIO(wav_audio)
        audio_segment = AudioSegment.from_file(audio_file)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

        chunk_length_ms = 10000
        chunks = [audio_segment[i:i + chunk_length_ms] for i in range(0, len(audio_segment), chunk_length_ms)]

        start_time = 0

        for chunk in chunks:
            wav_chunk_audio = BytesIO()
            try:
                chunk.export(wav_chunk_audio, format="wav")
            except Exception as e:
                continue

            wav_chunk_audio.seek(0)

            try:
                with sr.AudioFile(wav_chunk_audio) as source:
                    audio = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        text = "[Unintelligible]"
                    except sr.RequestError as e:
                        text = f"[Error: {str(e)}]"
            except Exception as e:
                text = f"[Error: {str(e)}]"

            formatted_start_time = format_time(start_time)
            transcriptions[formatted_start_time] = text

            start_time += chunk_length_ms

    except Exception as e:
        raise Exception(f"An error occurred while processing the audio: {e}")

    return transcriptions



def translate_text(text: Union[str, dict], target_language: str) -> str:
    """Translate text or JSON using Google Translator."""
    if isinstance(text, dict):
        # Recursively translate JSON objects
        def translate_json(obj):
            if isinstance(obj, dict):
                return {k: translate_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [translate_json(i) for i in obj]
            elif isinstance(obj, str):
                return GoogleTranslator(target=target_language).translate(obj)
            else:
                return obj
        
        translated_text = translate_json(text)
        return json.dumps(translated_text)
    else:
        # Translate plain text
        translated_text = GoogleTranslator(target=target_language).translate(text)
        return translated_text