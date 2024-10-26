import io
import os
from typing import List
import uuid
from api.utils import mime_types
from api.utils.minio_service import minio_service
from openai.types.audio.transcription import Transcription
from api.utils.settings import settings
import pytesseract
from PIL import Image
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAI
from deep_translator import GoogleTranslator
from openai import OpenAI as OI
from langchain.docstore.document import Document
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from fastapi import HTTPException
import json
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class SummaryService():
    def __init__(self):
        self.translator = GoogleTranslator()
        self.client = OI(
            base_url='https://openrouter.ai/api/v1',
            api_key=settings.OPENROUTER_API_KEY,
        )
        # self.llm = OpenAI(
        #     temperature=0, 
        #     base_url='https://openrouter.ai/api/v1',
        #     api_key=settings.OPENROUTER_API_KEY,
        # )

    def init_chain(self):
        prompt_template = """Write a concise summary of the following:
            "{text}"
        CONCISE SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(
            temperature=0,
            base_url='https://openrouter.ai/api/v1',
            model_name="openai/gpt-3.5-turbo-16k",
            api_key=settings.OPENROUTER_API_KEY
            # model_name="gpt-3.5-turbo-16k",
            # api_key=settings.OPENAI_API_KEY
        )
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        return llm_chain

    def apply_ocr_to_images(self, doc):
        """Extract text from images in the PDF using OCR."""
        text = ""
        for page in doc:
            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(BytesIO(image_bytes))
                text += pytesseract.image_to_string(image)
        return text

    def summarize_pdf(self, pdf_file_path: str, summary_length: str = "medium"):
        """Returns a summarized version of the PDF file located at pdf_file_path."""
        try:
            doc = fitz.open(pdf_file_path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF file at path {pdf_file_path}: {str(e)}")

        text = ""
        for page in doc:
            text += page.get_text()

        # If no text is found, apply OCR to extract text from images
        if not text.strip():
            text = self.apply_ocr_to_images(doc)

        if not text.strip():
            return "The PDF contains images but no text could be extracted."

        if summary_length == "brief":
            chunk_size = 1500
            chunk_overlap = 500
        elif summary_length == "detailed":
            chunk_size = 500
            chunk_overlap = 100
        else:  # default to "medium"
            chunk_size = 1000
            chunk_overlap = 300

        # Summarize Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.create_documents([text])

        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")

        summaries = []
        for doc in documents:
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)

        final_summary = " ".join(summaries)
        final_summary = final_summary.replace('\n', ' ').replace('\r', ' ').strip()
        return final_summary

    def transcribe_audio(self, file_path) -> Transcription:
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            response_format="text",
            file=open(file_path, "rb"),
        )
        return transcript

    def summarize_podcast(self, audio_file_path):
        """Summarize podcast audio file.

        Args:
            audio_file_path (str): Path to the audio file.

        Returns:
            tuple: Summary and Transcript of the podcast episode.
        """
        # Transcribe audio
        transcribed_text = self.transcribe_audio(audio_file_path)
        # segments = transcribe_audio_segments(audio_file_path)
        # transcription = get_paragraphs(segments)
        # delete_file(audio_file_path)
        # # Initialize LLM chain
        # text_splitter = CharacterTextSplitter()
        # texts = text_splitter.split_text(transcribed_text)
        # docs = [Document(page_content=t) for t in texts]
        # chain = load_summarize_chain(self.llm, chain_type='map_reduce')
        # summary = chain.run(docs)

        # return summary, transcription, transcribed_text
    
    def fetch_page(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    
    def get_podcast_details(self, podcast_url: str):
        """Get the transcript of a podcast episode from the provided URL."""
        try:
            content = self.fetch_page(podcast_url)
            soup = BeautifulSoup(content, 'html.parser')
            apple_title_meta = soup.find('meta', attrs={'name': 'apple:title'})

            title = apple_title_meta['content']
            li_tags = soup.select('ul.metadata li')
            duration = li_tags[-2].text.strip()
            host = soup.select('img', attrs={'class': 'artwork-component__contents artwork-component__image svelte-3e3mdo'})
            host_name = host[1]['alt']
            return {
                "title": title,
                "duration": duration,
                "host": host_name
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to extract podcast details: {str(e)}")


    def string_to_dict(self, input_string):
        try:
            # Parse the input string as a JSON object
            parsed_dict = json.loads(input_string)
            return parsed_dict
        except json.JSONDecodeError:
            return None

    def extract_scripts_with_asseturl(self, url):
        try:
            content = self.fetch_page(url)
            soup = BeautifulSoup(content, 'html.parser')
            script_tags = soup.find_all('script')

            for tag in script_tags:
                if tag.get('id') == 'serialized-server-data':
                    script_content = tag.string
                    return json.loads(script_content)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to extract audio URL: {str(e)}")

    def get_audio_url(self, podcast_url: str):
        data = self.extract_scripts_with_asseturl(podcast_url)
        if data and isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                intent_data = first_item.get('data', {})
            else:
                intent_data = {}
        else:
            intent_data = {}

        if not data:
            raise HTTPException(
                status_code=404, detail="Unable to retrieve audio from the provided URL")
        intent_data = data[0].get('data', {})
        shelves = intent_data.get('shelves', [])

        stream_url = None
        for shelf in shelves:
            items = shelf.get('items', [])
            for item in items:
                context_action = item.get('contextAction', {})
                episode_offer = context_action.get('episodeOffer', {})
                stream_url = episode_offer.get('streamUrl')
                if stream_url:
                    return stream_url
        if not stream_url:
            raise HTTPException(status_code=404, detail="Unable to retrieve audio from the provided URL")

    def summarize_audio(self, audio_file_path):
        """Summarizes an audio file by transcribing and then summarizing the transcript."""
        transcribed_text = self.transcribe_audio(audio_file_path)
        # segments = transcribe_audio_segments(audio_file_path)
        # transcription = get_paragraphs(segments)
        # llm_chain = self.init_chain()
        # stuff_chain = StuffDocumentsChain(
        #     llm_chain=llm_chain, document_variable_name="text")

        # text_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=1000, chunk_overlap=200)
        # documents = text_splitter.create_documents([transcribed_text])

        # summaries = []
        # for doc in documents:
        #     inputs = {"input_documents": [doc]}
        #     result = stuff_chain.invoke(inputs)
        #     summary = result.get("output_text", "")
        #     summaries.append(summary)

        # final_summary = " ".join(summaries)

        # """Calculate word counts"""
        # transcript_word_count = self.calculate_word_count(transcribed_text)
        # summary_word_count = self.calculate_word_count(final_summary)

        # """Calculate estimated read time (assuming 250 words per minute reading speed)"""
        # estimated_read_time = transcript_word_count / 250
        
        # return {
        #     "summary": final_summary,
        #     "summary_word_count": summary_word_count,
        #     "transcript": transcription,
        #     "transcribed_txt": transcribed_text,
        #     "transcript_word_count": transcript_word_count,
        #     "estimated_read_time": f"{estimated_read_time:.2f} minutes"
        # }
        
    def translate_summary(self, text, target_lang):
        """Translates the summary to the target language using GoogleTranslator."""
        translated_text = self.translator.translate(
            text, target_lang=target_lang)
        return translated_text

    def export_results_to_pdf(self, summary, transcript, translation):
        """Exports the summary, transcript, and translation to a PDF and uploads it to MinIO."""
        
        # Generate PDF in-memory
        pdf_file = io.BytesIO()
        c = canvas.Canvas(pdf_file, pagesize=letter)
        width, height = letter
    
        """Add Title"""
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 40, "Audio Summary and Transcript")

        """Add Transcript"""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, height - 80, "TRANSCRIPT:")
        c.setFont("Helvetica", 10)
        text = c.beginText(30, height - 100)
        text.setTextOrigin(30, height - 120)
        text.textLines(transcript)
        c.drawText(text)

        """Add Summary"""
        c.showPage()  # Start a new page
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, height - 40, "SUMMARY:")
        c.setFont("Helvetica", 10)
        text = c.beginText(30, height - 60)
        text.setTextOrigin(30, height - 80)
        text.textLines(summary)
        c.drawText(text)

        """Add Translation"""
        c.showPage()  # Start a new page
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, height - 40, "TRANSLATION:")
        c.setFont("Helvetica", 10)
        text = c.beginText(30, height - 60)
        text.setTextOrigin(30, height - 80)
        text.textLines(translation)
        c.drawText(text)

        c.save()

        """Save the PDF to a temporary file"""
        pdf_file.seek(0)
        temp_file_path = f'/tmp/summary_export_{uuid.uuid4().hex}.pdf'
        with open(temp_file_path, 'wb') as f:
            f.write(pdf_file.getvalue())

        """Upload the PDF to MinIO using the file path"""
        minio_save_file = os.path.basename(temp_file_path)
        save_url, download_url = minio_service.upload_to_minio(
            folder_name='summaries',
            source_file=temp_file_path,
            destination_file=minio_save_file,
            content_type=mime_types.APPLICATION_PDF
        )

        """Delete the temporary file after upload"""
        os.remove(temp_file_path)

        return save_url, download_url
    
    def calculate_word_count(self, text):
        """Calculates the word count of a given text."""
        words = text.split()
        return len(words)

    def process_audio(self, audio_file_path, target_lang, export_format="pdf"):
        """Processes the audio file: transcribes, summarizes, translates, and exports."""
        results = self.summarize_audio(audio_file_path)
        translated_summary = self.translate_summary(results["summary"], target_lang)
        
        if export_format == "pdf":
            save_url, download_url = self.export_results_to_pdf(results["summary"], results["transcribed_txt"], translated_summary)
        else:
            save_url, download_url = self.export_results(results["summary"], results["transcribed_txt"], translated_summary)

        return {
            "transcript": results["transcript"],
            "transcript_word_count": results["transcript_word_count"],
            "summary": results["summary"],
            "summary_word_count": results["summary_word_count"],
            "translation": translated_summary,
            "estimated_read_time": results["estimated_read_time"],
            "save_url": save_url,
            "download_url": download_url
        }

    def summarize_transcript(self, documents: List[Document]) -> str:
        """summarize the transcript"""
        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(
            llm_chain=llm_chain, document_variable_name="text")

        summaries = []
        for doc in documents:
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)
        final_summary = " ".join(summaries)
        return final_summary

    def create_documents(self, transcript: Transcription) -> List[Document]:
        """Create a list of documents from the transcript"""

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200)
        documents = text_splitter.create_documents(transcript)
        return documents


summary_service = SummaryService()
