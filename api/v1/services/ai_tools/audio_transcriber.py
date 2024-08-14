import whisper
import torch
from deep_translator import GoogleTranslator

def check_device():
    """Check CUDA availability."""
    return "cuda" if torch.cuda.is_available() else "cpu"

def transcribe_audio(file_path: str):
    """Transcribe audio file using Whisper and include timestamps in the specified format."""
    model_name = "base" 
    model = whisper.load_model(model_name, device=check_device())
    result = model.transcribe(file_path, verbose=True)

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