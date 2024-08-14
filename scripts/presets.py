import os
from fastapi import Request

from api.db.database import get_db
from api.v1.models.presets import Avatar

db = next(get_db())

def load_avatars_in_db(request: Request):
    '''Function to load all avatar presets as static files in the database'''

    AVATAR_FOLDER = 'presets/avatars'
    HOSTNAME = request.url.hostname
    PORT = request.url.port

    for root, dir, files in os.walk(AVATAR_FOLDER):
        for file_name in files:
            file_url = f'http://{HOSTNAME}:{PORT}/{AVATAR_FOLDER}/{file_name}'

            # Check if avatar already exists in the database
            if not db.query(Avatar).filter(Avatar.file_name==file_name).first():
                # Store URL in database
                avatar = Avatar(
                    file_url=file_url,
                    file_name=file_name
                )

                db.add(avatar)
                db.commit()
                db.refresh(avatar)
                
