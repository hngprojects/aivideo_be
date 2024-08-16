
from deep_translator import GoogleTranslator
from io import BytesIO
import logging
from typing import Dict, Union
import speech_recognition as sr
from pydub import AudioSegment



logger = logging.getLogger(__name__)

def format_time(milliseconds):
    seconds = (milliseconds / 1000) % 60
    minutes = (milliseconds / (1000 * 60)) % 60
    hours = (milliseconds / (1000 * 60 * 60)) % 24
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def transcribe_audio_file_with_timestamps(audio_data: bytes) -> Dict[str, Union[str, Dict[str, str]]]:
    recognizer = sr.Recognizer()
    try:
        audio_file = BytesIO(audio_data)
        audio_segment = AudioSegment.from_file(audio_file)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)  # Convert to mono and 16kHz

        chunk_length_ms = 10000  # 10 seconds
        chunks = [audio_segment[i:i + chunk_length_ms] for i in range(0, len(audio_segment), chunk_length_ms)]

        transcriptions = {}
        start_time = 0

        for i, chunk in enumerate(chunks):
            wav_audio = BytesIO()
            chunk.export(wav_audio, format="wav")
            wav_audio.seek(0)

            with sr.AudioFile(wav_audio) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)

            # Add timestamp information
            end_time = start_time + chunk_length_ms
            formatted_start_time = format_time(start_time)
            transcriptions[formatted_start_time] = text

            # Update start time for next chunk
            start_time = end_time

        return {"transcriptions": transcriptions}

    except sr.RequestError:
        return {"error": "Could not request results from Google API."}
    except sr.UnknownValueError:
        return {"error": "Google API could not understand the audio."}
    except Exception as e:
        return {"error": str(e)}



def translate_text(text: str, target_language: str) -> str:
    """Translate text using Deep Translator with Google Translator."""
    translation = GoogleTranslator(target=target_language).translate(text)
    return translation