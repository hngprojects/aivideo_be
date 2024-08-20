from typing import Optional
import os
from typing import Optional
from secrets import token_hex
from fastapi import HTTPException, status
from pydub import AudioSegment
from pathlib import Path
import asyncio
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid file format')
    

    new_filename = f'{name}-{token_hex(5)}.{save_extension}'
    SAVE_FILE_DIR = os.path.join(BASE_DIR, new_filename)
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


async def upload_to_current_dir(
    file, 
    allowed_extensions: Optional[list], 
    max_file_size: int,
    save_extension: str
):

    BASE_DIR = Path(__file__).resolve().parent

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
    SAVE_FILE_DIR = os.path.join(BASE_DIR, new_filename)
    with open(SAVE_FILE_DIR, 'wb') as f:
        content = await file.read()
        f.write(content)

    return SAVE_FILE_DIR


def delete_file(file_path: str):

    if os.path.exists(file_path):
        os.remove(file_path)
        

async def upload_files(
    files,
    allowed_extensions: Optional[list],
    upload_folder: str,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB default size
    chunk_size: int = 1024
):
    '''Function to upload single or multiple files with file size limitation'''

    if not isinstance(files, list):
        files = [files]

    uploaded_files = []

    for file in files:
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

        # Check the file size by reading it in chunks
        file_size = 0
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f'File {file_name} exceeds the maximum allowed size of {max_file_size / (1024 * 1024)} MB'
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
        SAVE_FILE_DIR = os.path.join(UPLOAD_DIR, new_filename)

        # Save the file
        with open(SAVE_FILE_DIR, 'wb') as f:
            while chunk := await file.read(chunk_size):
                f.write(chunk)

        uploaded_files.append(SAVE_FILE_DIR)

    return uploaded_files

    '''Check if the file size exceeds the allowed limit.'''
    await file.seek(0)
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    if file_size_mb > max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Please upload a file smaller than {max_file_size_mb} MB."
        )
    
async def audio_scan(file_path: str) -> bool:
    '''Basic scan to validate the audio file'''
    try:
        if not os.path.getsize(file_path):
            return False
        audio = AudioSegment.from_file(file_path)
        if len(audio) < 1000: 
            return False

        return True
    except Exception as e:
        print(f"Audio scan error: {e}")
        return False


async def contains_face(image_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    image = cv2.imread(image_path)
    
    if image is None:
        raise HTTPException(
            status_code=404,
            detail=f"Image not found or unable to load.",
        )
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) > 0:
        return True
    
    raise HTTPException(
            status_code=400,
            detail=f"Image does not contain a face.",
        ) 
