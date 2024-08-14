import os
from typing import Optional
from secrets import token_hex
from fastapi import HTTPException, status
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


async def upload_file(file, allowed_extensions: Optional[list], upload_folder: str, max_file_size: int, save_extension: str = 'pdf'):
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

    content = await file.read()
    if len(content) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='File exceeds size limit')

    # Reset file pointer after reading the content
    file.file.seek(0)

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

    return SAVE_FILE_DIR


async def download_file(thumbnail_category: str, thumbnail_content: bytes, save_extension: str = 'jpg') -> str:
    '''Function to save a generated thumbnail'''

    if not thumbnail_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Thumbnail content cannot be blank')

    download_folder_path = os.path.join(
        BASE_DIR, 'media', 'downloads', thumbnail_category)
    os.makedirs(download_folder_path, exist_ok=True)

    new_filename = f'{thumbnail_category}-{token_hex(5)}.{save_extension}'
    save_thumbnail_path = os.path.join(download_folder_path, new_filename)

    with open(save_thumbnail_path, 'wb') as f:
        f.write(thumbnail_content)

    return save_thumbnail_path
