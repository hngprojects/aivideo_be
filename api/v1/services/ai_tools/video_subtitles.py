import logging
import subprocess
import os
import uuid
from api.utils.settings import settings
from datetime import timedelta
from typing import List, Dict, Optional
from deep_translator import GoogleTranslator
import ffmpeg
from api.utils.files import delete_file
from openai import OpenAI
import time

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def convert_video_to_audio(video_path: str) -> str:
    """
    Convert video file to audio file using ffmpeg.

    Args:
        video_path (str): Path to the input video file.

    Returns:
        str: Path to the output audio file.

    Raises:
        Exception: If conversion fails.
    """
    try:
        audio_filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(settings.TEMP_DIR, audio_filename)

        command = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            audio_path,
            "-y"  # Overwrite output files without asking
        ]

        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        return audio_path

    except subprocess.CalledProcessError as e:
        raise Exception(f"Error converting video to audio: {e}")

def transcribe_audio(file_path: str) -> list:
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        list: List of transcription segments with text and timestamps.

    Raises:
        Exception: If transcription fails.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                language="en"  # Specify language if known; otherwise, auto-detect
            )
            # print(transcript)

            # Correctly access the segments attribute or method
            segments = transcript.segments  # Access the segments attribute
            # print(segments)
            
            if not segments:
                raise Exception("No transcription segments received from OpenAI Whisper API.")

            return segments

    except Exception as e:
        raise Exception(f"Error during transcription: {e}")

def save_subtitles_to_file(subtitles: str, file_path: str) -> None:
    """Saves subtitles to a file.
    
    Args:
        subtitles (str): The subtitle content to be saved.
        file_path (str): The path where the subtitle file should be saved.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(subtitles)
    except Exception as e:
        raise Exception(f"Error saving subtitles to file: {str(e)}")
    

def translate_text(text: str, target_language: str) -> str:
    """Translate text using Deep Translator with Google Translator"""
    try:
        translation = GoogleTranslator(target=target_language).translate(text)
        return translation
    except Exception as e:
        raise Exception(f"Error during translation: {str(e)}")


def generate_srt_subtitles(transcription_segments: list) -> str:
    """
    Generate SRT formatted subtitles from transcription segments.

    Args:
        transcription_segments (list): List of transcription segments with timestamps.

    Returns:
        str: SRT formatted subtitle content.
    """
    srt_entries = []

    for idx, segment in enumerate(transcription_segments, start=1):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()

        srt_entry = f"{idx}\n{start_time} --> {end_time}\n{text}\n"
        srt_entries.append(srt_entry)

    return "\n".join(srt_entries)

def format_timestamp(seconds: float) -> str:
    """
    Format timestamp in seconds to SRT time format.

    Args:
        seconds (float): Time in seconds.

    Returns:
        str: Formatted time string in 'HH:MM:SS,mmm' format.
    """
    milliseconds = int((seconds - int(seconds)) * 1000)
    time_struct = time.gmtime(seconds)
    time_formatted = time.strftime("%H:%M:%S", time_struct)
    return f"{time_formatted},{milliseconds:03d}"


def save_subtitles_to_file(srt_content: str, output_path: str) -> None:
    """
    Save SRT content to a file.

    Args:
        srt_content (str): SRT formatted subtitle content.
        output_path (str): Path to save the SRT file.

    Raises:
        Exception: If saving fails.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as srt_file:
            srt_file.write(srt_content)
    except Exception as e:
        raise Exception(f"Error saving subtitles to file: {e}")


def generate_subtitles(video_path: str) -> dict:
    """
    Generate subtitles for a video file.

    Args:
        video_path (str): Path to the input video file.

    Returns:
        dict: Dictionary containing the path to the generated SRT file.

    Raises:
        Exception: If any step fails.
    """
    try:
        # Convert video to audio
        audio_path = convert_video_to_audio(video_path)

        # Transcribe audio to get segments with timestamps
        transcription_segments = transcribe_audio(audio_path)

        # Ensure segments is a list of dictionaries
        if isinstance(transcription_segments, dict):
            transcription_segments = transcription_segments.get('segments', [])

        # Generate SRT formatted subtitles
        srt_content = generate_srt_subtitles(transcription_segments)

        # Define SRT file path
        base_filename = os.path.splitext(os.path.basename(video_path))[0]
        srt_filename = f"{base_filename}_{uuid.uuid4()}.srt"
        srt_path = os.path.join(settings.STORAGE_DIR, 'subtitles', srt_filename)

        # Save SRT content to file
        save_subtitles_to_file(srt_content, srt_path)

        # Clean up intermediate audio file
        delete_file(audio_path)

        return {"srt_file_path": srt_path}

    except Exception as e:
        raise Exception(f"Error generating subtitles: {e}")