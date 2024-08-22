import os
from typing import List
import uuid

from openai.types.audio.transcription import Transcription
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from api.utils.settings import settings
import pytesseract
from typing import Optional 
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
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
import requests
from bs4 import BeautifulSoup
from api.utils.files import delete_file
from io import BytesIO
from fastapi import HTTPException
import json
import fitz


class SummaryService():
    def __init__(self):
        self.translator = GoogleTranslator()
        self.client = OI(api_key=settings.OPENAI_API_KEY)
        self.llm = OpenAI(
            temperature=0, openai_api_key=settings.OPENAI_API_KEY)

    def init_chain(self):
        prompt_template = """Write a concise summary of the following:
            "{text}"
        CONCISE SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k",
                         api_key=settings.OPENAI_API_KEY)
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
            raise ValueError(
                f"Failed to open PDF file at path {pdf_file_path}: {str(e)}")

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
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.create_documents([text])

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
        final_summary = final_summary.replace(
            '\n', ' ').replace('\r', ' ').strip()
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
        delete_file(audio_file_path)
        # Initialize LLM chain
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(transcribed_text)
        docs = [Document(page_content=t) for t in texts]
        chain = load_summarize_chain(self.llm, chain_type='map_reduce')
        summary = chain.run(docs)

        return summary, transcribed_text

    def fetch_page(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.text

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
        intent_data = data[0].get('data', {})
        shelves = intent_data.get('shelves', [])

        for shelf in shelves:
            items = shelf.get('items', [])
            for item in items:
                context_action = item.get('contextAction', {})
                episode_offer = context_action.get('episodeOffer', {})
                stream_url = episode_offer.get('streamUrl')
                if stream_url:
                    break
            if stream_url:
                break
        return stream_url

    def summarize_audio(self, audio_file_path):
        """Summarizes an audio file by transcribing and then summarizing the transcript."""
        transcribed_text = self.transcribe_audio(audio_file_path)
        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(
            llm_chain=llm_chain, document_variable_name="text")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200)
        documents = text_splitter.create_documents([transcribed_text])

        summaries = []
        for doc in documents:
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)

        final_summary = " ".join(summaries)

        """Calculate word counts"""
        transcript_word_count = self.calculate_word_count(transcribed_text)
        summary_word_count = self.calculate_word_count(final_summary)

        return {
            "summary": final_summary,
            "summary_word_count": summary_word_count,
            "transcript": transcribed_text,
            "transcript_word_count": transcript_word_count
        }

    def translate_summary(self, text, target_lang):
        """Translates the summary to the target language using GoogleTranslator."""
        translated_text = self.translator.translate(
            text, target_lang=target_lang)
        return translated_text

    def export_results_to_pdf(self, summary, transcript, translation, output_dir="exports"):
        """Exports the summary, transcript, and translation to a PDF file."""
        os.makedirs(output_dir, exist_ok=True)
        pdf_file_path = os.path.join(
            output_dir, f"summary_export_{uuid.uuid4()}.pdf")

        c = canvas.Canvas(pdf_file_path, pagesize=letter)
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

        return pdf_file_path

    def calculate_word_count(self, text):
        """Calculates the word count of a given text."""
        words = text.split()
        return len(words)

    def process_audio(self, audio_file_path, target_lang, export_format="pdf"):
        """Processes the audio file: transcribes, summarizes, translates, and exports."""
        results = self.summarize_audio(audio_file_path)
        translated_summary = self.translate_summary(
            results["summary"], target_lang)

        if export_format == "pdf":
            export_path = self.export_results_to_pdf(
                results["summary"], results["transcript"], translated_summary)
        else:
            export_path = self.export_results(
                results["summary"], results["transcript"], translated_summary)

        return {
            "transcript": results["transcript"],
            "transcript_word_count": results["transcript_word_count"],
            "summary": results["summary"],
            "translation": translated_summary,
            "summary_word_count": results["summary_word_count"],
            "translation": translated_summary,
            "export_path": export_path
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
        documents = text_splitter.create_documents([transcript])
        return documents


summary_service = SummaryService()
