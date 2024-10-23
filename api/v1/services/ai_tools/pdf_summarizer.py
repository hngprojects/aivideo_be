import os
import uuid
from api.utils.pdf_builder import PDFBuilder
from api.utils.settings import settings
from api.utils.openai_service import openai_service
from io import BytesIO
from deep_translator import GoogleTranslator
from openai import OpenAI
from io import BytesIO

import PyPDF2, tiktoken


class PDFSummaryService:

    def __init__(self):
        self.translator = GoogleTranslator()

    
    def get_reading_time(self, text: str):
        '''This function gets the reading time of a text'''

        read_time = round(len(text.split()) / 250) 
        return read_time

    
    def extract_pdf_data(self, pdf_file_path: str):
        '''This function extracts and returns data from pdf'''

        with open(file=pdf_file_path, mode='rb') as pdf:
            pdf_reader = PyPDF2.PdfReader(pdf)
            text = ''

            # Get number of pages in text
            no_of_pages = len(pdf_reader.pages)

            for page_no in range(no_of_pages):
                # Extract text from a single page
                page = pdf_reader.pages[page_no]
                text += page.extract_text()

            # Get number of words in the text
            no_of_words = len(text.split())

            read_time = self.get_reading_time(text)
            estimated_read_time = f'{read_time} minute' if read_time == 1 else f'{read_time} minutes'

            # return text, no_of_pages, no_of_words
            return {
                'text': text,
                'number_of_pages': no_of_pages,
                'number_of_words': no_of_words,
                'estimated_read_time': estimated_read_time
            }

    
    def split_text_into_chunks(self, text: str, max_tokens: int=2000):
        '''This function splits text into chunks based on the openai model'''

        encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        
        tokens = encoding.encode(text)
        chunk_size = max_tokens
        chunks = []
        current_chunk = []
        current_token_count = 0
        
        # Loop through the list of encoded tokens
        for token in tokens:
            # Append a token to the current chunk and increment the current token count
            current_chunk.append(token)
            current_token_count += 1

            # Check if the current token count has reached its limit
            if current_token_count >= chunk_size:
                # Append the decoded current chunk to the list of chunks and reset the current chunk and token count
                chunks.append(encoding.decode(current_chunk))
                current_chunk = []
                current_token_count = 0

        if current_chunk:
            chunks.append(encoding.decode(current_chunk))
        
        return chunks


    def summarize_text(self, text: str, max_tokens: int=2000, detail_level: str = 'short'):
        """_summary_

        Args:
            text (str): Text to be summarized
            max_tokens (int, optional): Max tokens that can be processed by openai. Defaults to 2000.
            detail_level (str, optional): The datail levl of the summary. Can be `very short`, `short`, `detailed`.  Defaults to `short`.

        Returns:
            str: The summarized version of the input text
        """

        prompt = f'Generate a {detail_level} summary of the following text: {text}. Separate the summary into paragraphs if need be but do not add anything else except the summary alone. Although, please ensure that the summary is shorter than the text itself.'
        
        response = openai_service.prompt_ai(
            prompt=prompt,
            system_role_desc='You are a great summarization assistant.',
            max_tokens=max_tokens
        )
        return response

    
    def translate_summary(self, text, target_lang):
        """Translates the summary to the target language using GoogleTranslator."""
        
        translated_text = self.translator.translate(text, target_lang=target_lang)
        return translated_text
    

    def save_summary_to_pdf(self, text: str):
        '''This saves the generated text to a file as a pdf'''

        pdf_buffer = BytesIO()
        pdf_builder = PDFBuilder(pdf_buffer)

        file_path = os.path.join(settings.TEMP_DIR, f"pdfsum-{uuid.uuid4()}.pdf")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Add summary to pdf file
        pdf_builder.add_section(title='Summary', text=text)

        # Build pdf
        pdf_builder.build()

        # Save the PDF content to a file
        pdf_buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.read())

        pdf_buffer.close()

        return file_path
    

pdf_summary_service = PDFSummaryService()
