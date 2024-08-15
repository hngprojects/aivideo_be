
from deep_translator import GoogleTranslator



def translate_text(text: str, target_language: str) -> str:
    """Translate text using Deep Translator with Google Translator."""
    translation = GoogleTranslator(target=target_language).translate(text)
    return translation