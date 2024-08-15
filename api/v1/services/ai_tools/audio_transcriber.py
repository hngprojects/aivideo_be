
from deep_translator import GoogleTranslator
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
from typing import Dict
from pydub.exceptions import CouldntDecodeError


def format_time(ms):
    """Convert milliseconds to mm:ss format."""
    seconds = ms / 1000
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def transcribe_audio_file_with_timestamps(audio_data: bytes) -> Dict[str, str]:
    recognizer = sr.Recognizer()
    audio_file = BytesIO(audio_data)
    
    try:
        audio_segment = AudioSegment.from_file(audio_file)
    except CouldntDecodeError as e:
        raise ValueError(f"Error decoding audio file: {str(e)}")
    
    audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)  # Convert to mono and 16kHz

    chunk_length_ms = 10000  # 10 seconds
    chunks = [audio_segment[i:i + chunk_length_ms] for i in range(0, len(audio_segment), chunk_length_ms)]

    transcriptions = {}
    start_time = 0

    for chunk in chunks:
        wav_audio = BytesIO()
        chunk.export(wav_audio, format="wav")
        wav_audio.seek(0)

        try:
            with sr.AudioFile(wav_audio) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            text = "Could not understand audio."
        except sr.RequestError as e:
            text = f"Error with Google API: {str(e)}"

        end_time = start_time + chunk_length_ms
        formatted_start_time = format_time(start_time)
        transcriptions[formatted_start_time] = text

        start_time = end_time

    return transcriptions

def translate_text(text: str, target_language: str) -> str:
    """Translate text using Deep Translator with Google Translator."""
    translation = GoogleTranslator(target=target_language).translate(text)
    return translation