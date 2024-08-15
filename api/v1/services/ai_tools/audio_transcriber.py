import whisper
import torch
from deep_translator import GoogleTranslator
import io

def check_device():
    """Check CUDA availability."""
    return "cuda" if torch.cuda.is_available() else "cpu"

def transcribe_audio(audio_content: bytes):
    """Transcribe audio content using Whisper and include timestamps in the specified format."""
    model_name = "base" 
    model = whisper.load_model(model_name, device=check_device())
    
    # Use BytesIO to handle the audio content in memory
    audio_file = io.BytesIO(audio_content)
    
    # Transcribe the audio content
    result = model.transcribe(audio_file, verbose=True)
    
    segments = result["segments"]
    transcription_with_timestamps = []
    for segment in segments:
        start_time = segment["start"]
        end_time = segment["end"]
        text = segment["text"].strip()

        formatted_start_time = f"{int(start_time // 60):02}:{int(start_time % 60):02}"
        formatted_end_time = f"{int(end_time // 60):02}:{int(end_time % 60):02}"

        transcription_with_timestamps.append(f"{formatted_start_time} - {formatted_end_time}\n{text}")

    return "\n\n".join(transcription_with_timestamps)


def translate_text(text: str, target_language: str) -> str:
    """Translate text using Deep Translator with Google Translator."""
    translation = GoogleTranslator(target=target_language).translate(text)
    return translation