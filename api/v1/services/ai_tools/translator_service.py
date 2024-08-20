from deep_translator import GoogleTranslator
from fastapi import HTTPException

def translate_text(text: str, target_language: str) -> str:
    try:
        # Further reduce chunk size to avoid issues
        parts = [text[i:i + 1000] for i in range(0, len(text), 1000)]
        translated_parts = []

        for part in parts:
            if part.strip():  # Ensure the part is not empty or just whitespace
                translated_part = GoogleTranslator(source='auto', target=target_language).translate(part)
                translated_parts.append(translated_part)

        # Combine the translated parts into one string
        translated_text = " ".join(translated_parts)
        
        return translated_text
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during translation: {str(e)}"
        )
