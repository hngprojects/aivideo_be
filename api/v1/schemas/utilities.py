from pydantic import BaseModel


class DownloadRequest(BaseModel):

    file_url: str


class TextTranslateRequest(BaseModel):

    text: str
    target_language: str
    