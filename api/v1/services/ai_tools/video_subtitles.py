import os
import json
from datetime import timedelta
from typing import List, Dict
from deep_translator import GoogleTranslator
from api.utils.video_subtitles import save_subtitles_to_file, delete_file
from api.utils.files import convert_video_to_audio
from api.v1.services.ai_tools.summary_audio import summary_service

def translate_text(text: str, target_language: str) -> str:
    """Translate text using Deep Translator with Google Translator"""
    try:
        translation = GoogleTranslator(target=target_language).translate(text)
        return translation
    except Exception as e:
        raise Exception(f"Error during translation: {str(e)}")

def generate_subtitles(video_url: str, interval_seconds: int = 10) -> dict:
    """Generate subtitles for a video by dynamically creating timestamps every few seconds."""
    try:
        # Convert video to audio
        audio_file_path = convert_video_to_audio(video_url)
        video_filename = os.path.splitext(os.path.basename(video_url))[0]
        subtitle_file_path = f"{video_filename}.srt"
        
        # Transcribe audio to text
        transcription = summary_service.transcribe_audio(audio_file_path)['transcription']
        
        # Generate dynamic timestamps
        duration_seconds = len(transcription.split())  # Assuming one word per second
        timestamps = generate_timestamps(transcription, duration_seconds, interval_seconds)
        
        # Generate subtitles with dynamically generated timestamps
        subtitles = generate_subtitles_from_transcription(transcription, timestamps)
        
        # Save subtitles to file
        save_subtitles_to_file(subtitles, subtitle_file_path)
        
        # Clean up the audio file
        delete_file(audio_file_path)
        
        return {"subtitles": subtitle_file_path}
    except Exception as e:
        raise Exception(f"Error generating subtitles: {str(e)}")

def generate_timestamps(transcription: str, duration: int, interval_seconds: int) -> List[Dict[str, str]]:
    """Generate timestamps every few seconds"""
    timestamps = []
    start_time = 0
    words = transcription.split()

    for i in range(0, len(words), interval_seconds):
        end_time = min(start_time + interval_seconds, duration)
        timestamps.append({
            "start_time": str(start_time),
            "end_time": str(end_time),
            "paragraph": " ".join(words[start_time:end_time])
        })
        start_time = end_time
    
    return timestamps

def generate_subtitles_from_transcription(transcription: str, timestamps: List[Dict[str, str]]) -> str:
    """Generate SRT formatted subtitles from transcription text with timestamps"""
    
    def format_timedelta(td: timedelta) -> str:
        """Format timedelta as SRT timecode"""
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    srt_content = []
    
    for idx, item in enumerate(timestamps):
        start_time = timedelta(seconds=float(item["start_time"]))
        end_time = timedelta(seconds=float(item["end_time"]))
        text = item["paragraph"]
        
        srt_content.append(f"{idx + 1}")
        srt_content.append(f"{format_timedelta(start_time)} --> {format_timedelta(end_time)}")
        srt_content.append(text)
        srt_content.append("")  # Blank line after each subtitle block

    return "\n".join(srt_content)
