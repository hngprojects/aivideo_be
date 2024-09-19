import mimetypes
from typing import List, Optional, Union
import os
from secrets import token_hex
from fastapi import HTTPException, status, UploadFile
from pydub import AudioSegment
from pathlib import Path
from api.utils.settings import settings
import aiofiles
import asyncio
import yt_dlp as youtube_dl
import cv2


BASE_DIR = Path(__file__).resolve().parent.parent.parent


async def upload_file(
    file,
    allowed_extensions: Optional[list],
    upload_folder: str,
    save_extension: str = 'pdf'
):
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

    UPLOAD_FOLDER = os.path.join(settings.TEMP_DIR)
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Create file storage path
    DOWNLOAD_DIR = os.path.join(UPLOAD_FOLDER, upload_folder)
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Generate a new file name
    new_filename = f'{name}-{token_hex(5)}.{save_extension}'
    SAVE_FILE_DIR = os.path.join(settings.TEMP_DIR, new_filename)
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
    # SAVE_FILE_DIR = os.path.join(UPLOAD_DIR, new_filename)
    SAVE_FILE_DIR = os.path.join(DOWNLOAD_ROLDER, new_filename)
    with open(SAVE_FILE_DIR, 'wb') as f:
        content = await file.read()
        f.write(content)

    return SAVE_FILE_DIR


async def upload_file_to_current_dir(
    file: str,
    allowed_extensions: Optional[list],
    save_extension: str
):

    BASE_DIR = Path(__file__).resolve().parent

    # Check against invalid extensions

    if hasattr(file, 'filename'):
        file_name = file.filename.lower()
    else:
        # If it's a file-like object created from bytes
        file_name = getattr(file, 'filename', 'unnamed_file')

    file_extension = file_name.split('.')[-1]
    name = file_name.split('.')[0]

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='File cannot be blank')

    if allowed_extensions:
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid file format')

    new_filename = f'{name}-{token_hex(5)}.{save_extension}'
    SAVE_FILE_DIR = os.path.join(settings.TEMP_DIR, new_filename)
    with open(SAVE_FILE_DIR, 'wb') as f:
        if hasattr(file, 'read'):
            # If it's a file-like object (e.g., BytesIO)
            if asyncio.iscoroutinefunction(file.read):
                # If it's an async file
                content = await file.read()
            else:
                # If it's not an async file
                content = file.read()
        else:
            # If it's already bytes content
            content = file

        f.write(content)

    return SAVE_FILE_DIR


async def upload_to_temp_dir(
    file,
    allowed_extensions: Optional[list],
    max_file_size: int,
    save_extension: str
):

    file_extension = file.filename.split('.')[-1]
    name = file.filename.split('.')[0]

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='File cannot be blank')

    if allowed_extensions:
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid file format'
            )

    # Check file size
    file_size = len(file.file.read())
    if file_size > max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is {max_file_size / (1024 * 1024)} MB.",
        )

    # Reset file pointer after reading
    await file.seek(0)

    new_filename = f'{name}-{token_hex(5)}.{save_extension}'
    SAVE_FILE_DIR = os.path.join(settings.TEMP_DIR, new_filename)
    with open(SAVE_FILE_DIR, 'wb') as f:
        content = await file.read()
        f.write(content)

    return SAVE_FILE_DIR


def delete_file(file_path: str):

    if os.path.exists(file_path):
        os.remove(file_path)


async def save_file(file: UploadFile, save_path: str, chunk_size: int) -> None:
    """Save a file to a specified path"""
    async with aiofiles.open(save_path, 'wb') as f:
        while chunk := await file.read(chunk_size):
            await f.write(chunk)


async def upload_files(
    files: Union[List[UploadFile], UploadFile],
    allowed_extensions: Optional[list],
    upload_folder: str,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB default size
    chunk_size: int = 10 * 1024 * 1024
):
    '''Function to upload single or multiple files with file size limitation'''
    if not isinstance(files, list):
        files = [files]

    uploaded_files = []
    tasks = []

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'media', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    UPLOAD_DIR = os.path.join(UPLOAD_FOLDER, upload_folder)
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    for file in files:
        file_name = str(file.filename).lower()
        file_extension = os.path.splitext(file_name)[1]
        name = os.path.splitext(file_name)[0]

        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='File cannot be blank'
            )

        if allowed_extensions and file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid file format'
            )

        content_length = file.size
        if content_length and int(content_length) > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file_name} exceeds the maximum allowed size is {max_file_size / (1024 * 1024)} MB."
            )

        # Reset file pointer to the start after checking size
        await file.seek(0)

        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'media', 'uploads')
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Create file storage path
        UPLOAD_DIR = os.path.join(UPLOAD_FOLDER, upload_folder)
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Generate a new file name
        new_filename = f'{name}-{token_hex(5)}.{file_extension}'
        # SAVE_FILE_DIR = os.path.join(UPLOAD_DIR, new_filename)
        SAVE_FILE_DIR = os.path.join(settings.TEMP_DIR, new_filename)

        # Save the file
        with open(SAVE_FILE_DIR, 'wb') as f:
            if not content_length:
                file_size = 0
                await file.seek(0)
                while chunk := await file.read(chunk_size):
                    file_size += len(chunk)
                    if file_size > max_file_size:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File {file_name} exceeds the maximum allowed size is {max_file_size / (1024 * 1024)} MB."
                        )
                await file.seek(0)

        new_filename = f'{name}-{token_hex(5)}{file_extension}'
        save_path = os.path.join(UPLOAD_DIR, new_filename)

        tasks.append(save_file(file, save_path, chunk_size))
        uploaded_files.append(save_path)

    await asyncio.gather(*tasks)

    return uploaded_files


async def check_file_size(file, max_file_size_mb=10):
    '''Check if the file size exceeds the allowed limit.'''
    await file.seek(0)
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    if file_size_mb > max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Please upload a file smaller than {max_file_size_mb} MB."
        )



async def contains_face(image_path):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    image = cv2.imread(image_path)

    if image is None:
        raise HTTPException(
            status_code=404, detail=f"Image not found or unable to load.",)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        return True

    raise HTTPException(
        status_code=400, detail=f"Image does not contain a face.",)


def get_media_type_from_extension(file_extension):
    """
    Given a file extension (e.g., 'mp4', 'jpg', 'pdf'), return the corresponding media type (MIME type).
    """
    media_type, _ = mimetypes.guess_type(f"dummy.{file_extension}")
    return media_type


def download_audio_yt(link):
    """
    Download audio from a youtube video link
    """
    try:
        ydl_opts = {
            'format': 'worstaudio/worst',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': f'{settings.TEMP_DIR}/%(title)s.%(ext)s',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            video_title = info_dict.get('title', None)
            ydl.download([link])

        return f"{settings.TEMP_DIR}/{video_title}.wav"
    except Exception as e:
        print(f"Error in download_audio_yt: {e}")
        raise
