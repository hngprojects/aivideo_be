from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import requests, os
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.files import get_media_type_from_extension
from api.utils.settings import settings
from api.utils.stock_media_service import StockMediaService
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.schemas.utilities import DownloadRequest, FetchStockMediaRequest, TextTranslateRequest
from api.v1.services.text_translation import translation_service
from api.v1.services.user import user_service
from api.v1.services.presets import preset_service

utilities = APIRouter(tags=["Utilities"])


@utilities.post("/download")
async def download_file(schema: DownloadRequest):
    try:
        # Fetch the file from the URL
        response = requests.get(schema.file_url, stream=True)
        response.raise_for_status()  # Check for errors in the response
        
        file_path = os.path.join(settings.TEMP_DIR, schema.file_url.split("/")[-1])
        with open(file_path, "wb") as video_file:
            for chunk in response.iter_content(chunk_size=8192):
                video_file.write(chunk)

        # Return the file as a FileResponse
        return FileResponse(
            file_path,
            media_type=get_media_type_from_extension(file_path.split(".")[-1]),
            filename=file_path.split('/')[-1]
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading file: {str(e)}")


@utilities.post('/translate-text')
async def translate_text(schema: TextTranslateRequest):

    translated_text = translation_service.translate_text(
        source_text=schema.text,
        target_language=schema.target_language
    )

    return success_response(
        status_code=200,
        message="Translation successful",
        data={
            'translated_text': translated_text
        }
    )
    

@utilities.post('/fetch-stock-media', status_code=200)
async def fetch_stock_media(
    schema: FetchStockMediaRequest,
    page: int = Query(1),
    per_page: int = Query(80, le=80),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to retrieve stock media'''
    
    result = None
    
    if isinstance(schema.query, str):
        result = []
        stock_service = StockMediaService(
            query=schema.query,
            page=page,
            per_page=per_page
        )
        
        if schema.media_type == 'stock images':
            image_list = stock_service.fetch_images()
            result = image_list
        
        elif schema.media_type == 'stock videos':
            video_list = stock_service.fetch_videos()
            result = video_list
        
        elif schema.media_type == 'talking avatar':
            avatars = preset_service.fetch_all_avatars(db)
            avatar_list = [
                {
                    'preview': avatar.file_url,
                    'normal': avatar.file_url,
                } for avatar in avatars
            ]
            result = avatar_list
        
        # Need generation of images here
        elif schema.media_type == 'ai images':
            pass
        
        elif schema.media_type == 'ai illustrations':
            pass
        
        elif schema.media_type == '3d moving videos':
            pass
    
    elif isinstance(schema.query, list):
        result = {}
        for query in schema.query:
            # try:
            stock_service = StockMediaService(
                query=query,
                page=page,
                per_page=per_page
            )
            
            if schema.media_type == 'stock images':
                image_list = stock_service.fetch_images()
                result[query] = image_list
            
            elif schema.media_type == 'stock videos':
                video_list = stock_service.fetch_videos()
                result[query] = video_list
            
            elif schema.media_type == 'talking avatar':
                avatars = preset_service.fetch_all_avatars(db)
                avatar_list = [
                    {
                        'preview': avatar.file_url,
                        'normal': avatar.file_url,
                    } for avatar in avatars
                ]
                result = avatar_list
            
            # Need generation of images here
            elif schema.media_type == 'ai images':
                pass
            
            elif schema.media_type == 'ai illustrations':
                pass
            
            elif schema.media_type == '3d moving videos':
                pass
                
            # except Exception as e:
            #     continue
            
    return success_response(
        status_code=200,
        message='Stock media fetched successfully',
        data=result
    )
