from api.utils.logger import logging
import ffmpeg
import os
from typing import List, Optional, Union
from secrets import token_hex
from fastapi import HTTPException, status
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


async def upload_file(file, allowed_extensions: Optional[list], upload_folder: str, save_extension: str = 'pdf'):
    '''Function to upload a file'''

    # Check against invalid extensions
    file_name = file.filename.lower()
    file_extension = file_name.split('.')[-1]
    name = file_name.split('.')[0]

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='File cannot be blank')

    if allowed_extensions:
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid file format')

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'media', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Create file storage path
    DOWNLOAD_DIR = os.path.join(UPLOAD_FOLDER, upload_folder)
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Generate a new file name
    new_filename = f'{name}-{token_hex(5)}.{save_extension}'
    SAVE_FILE_DIR = os.path.join(DOWNLOAD_DIR, new_filename)
    with open(SAVE_FILE_DIR, 'wb') as f:
        content = await file.read()
        f.write(content)

    return SAVE_FILE_DIR


async def download_file(file, download_folder: str, save_extension: str = 'pdf'):
    '''Function to upload a file'''

    # Check against invalid extensions
    file_name = file.filename.lower()
    file_extension = file_name.split('.')[-1]
    name = file_name.split('.')[0]

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='File cannot be blank')

    DOWNLOAD_ROLDER = os.path.join(BASE_DIR, 'media', 'downloads')
    if not os.path.exists(DOWNLOAD_ROLDER):
        os.makedirs(DOWNLOAD_ROLDER)

    # Create file storage path
    UPLOAD_DIR = os.path.join(DOWNLOAD_ROLDER, download_folder)
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Generate a new file name
    new_filename = f'{name}-{token_hex(5)}.{save_extension}'
    SAVE_FILE_DIR = os.path.join(UPLOAD_DIR, new_filename)
    with open(SAVE_FILE_DIR, 'wb') as f:
        content = await file.read()
        f.write(content)

    return SAVE_FILE_DIR


def convert_video_to_audio(
    input_path: str,
    output_path: Optional[str] = None,
    audio_format: str = 'mp3',
    audio_bitrate: str = '192k'
) -> str:
    """
    Convert a video file to an audio file using FFmpeg.

    Args:
    input_path (str): Path to the input video file.
    output_path (Optional[str]): Path for the output audio file. If not
                                 provided, it will be derived from the
                                 input path.
    audio_format (str): Output audio format (default is 'mp3').
    audio_bitrate (str): Output audio bitrate (default is '192k').

    Returns:
    str: Path to the output audio file.

    Raises:
    FileNotFoundError: If the input file doesn't exist.
    ffmpeg.Error: If FFmpeg encounters an error during conversion.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.{audio_format}"

    try:
        stream = ffmpeg.input(input_path)

        stream = ffmpeg.output(
            stream,
            output_path,
            acodec=audio_format,
            audio_bitrate=audio_bitrate,
            vn=None
        )

        ffmpeg.run(stream, overwrite_output=True)

        return output_path

    except ffmpeg.Error:
        logging.error("FFmpeg error occurred")
        raise


async def upload_files(
        files,
        allowed_extensions: Optional[list],
        upload_folder: str,
        save_extension: str = 'pdf'
):
    '''Function to upload single or multiple files'''
    if not isinstance(files, list):
        files = [files]

    uploaded_files = []

    for file in files:
        # Check against invalid extensions
        file_name = file.filename.lower()
        file_extension = file_name.split('.')[-1]
        name = file_name.split('.')[0]

        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='File cannot be blank'
            )

        if allowed_extensions:
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Invalid file format for {file_name}'
                )

        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'media', 'uploads')
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Create file storage path
        UPLOAD_DIR = os.path.join(UPLOAD_FOLDER, upload_folder)
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Generate a new file name
        new_filename = f'{name}-{token_hex(5)}.{save_extension}'
        SAVE_FILE_DIR = os.path.join(UPLOAD_DIR, new_filename)

        with open(SAVE_FILE_DIR, 'wb') as f:
            content = await file.read()
            f.write(content)

        uploaded_files.append(SAVE_FILE_DIR)

    return uploaded_files
