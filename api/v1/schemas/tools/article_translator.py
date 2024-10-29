from pydantic import BaseModel
from typing import List


class TranslateArticle(BaseModel):

    article: str
    languages: List[str]
    names: List[str]
