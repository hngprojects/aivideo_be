import os
from typing import List
import uuid
from api.utils.pdf_builder import PDFBuilder
from api.utils.settings import settings
from io import BytesIO
from openai import OpenAI
from io import BytesIO


class ArticleTranslatorService:

    def __init__(self):

        self.client = OpenAI(
            base_url='https://openrouter.ai/api/v1',
            api_key=settings.OPENROUTER_API_KEY,
        )

    
    def generate_translated_article(
        self, 
        article: str, 
        language: str,
        name: str
    ):
        """Function to generate a translated article. The function leverages OpenAI to generate translations

        Args:
            article (str): The article to be translated
            language (str): The language to translate to
            name (str): A name for a user

        Returns:
            str: The translation of the article
        """

        prompt = f'Translate this article into {language.capitalize()}. Article- {article}. The article should be generated for a user with the name {name.capitalize()}. Only generate the translated article and nothing else.'

        response = self.client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an article translation assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        translated_article = response.choices[0].message.content

        return translated_article


article_translator_service = ArticleTranslatorService()