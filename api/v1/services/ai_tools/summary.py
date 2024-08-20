import os
import uuid
from api.utils.settings import settings
import pytesseract
from PIL import Image
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from deep_translator import GoogleTranslator
from openai import OpenAI as OI
from langchain_community.llms.openai import OpenAI
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
        self.llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
    
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

    def summarize_pdf(self, pdf_file_path: str):
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

        # Summarize Text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
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
    
    def transcribe_audio(self, file_path):
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
            raise HTTPException(status_code=500, detail=f"Failed to extract audio URL: {str(e)}")

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
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        documents = text_splitter.create_documents([transcribed_text])

        summaries = []
        for doc in documents:
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)
        
        final_summary = " ".join(summaries)
        
        return {
            "summary": final_summary,
            "transcript": transcribed_text
        }
        
    def translate_summary(self, text, target_lang):
        """Translates the summary to the target language using GoogleTranslator."""
        translated_text = self.translator.translate(text, target_lang=target_lang)
        return translated_text

    def export_results(self, summary, transcript, translation, output_dir="exports"):
        """Exports the summary, transcript, and translation to a text file."""
        os.makedirs(output_dir, exist_ok=True)
        export_file_path = os.path.join(output_dir, f"summary_export_{uuid.uuid4()}.txt")
        
        with open(export_file_path, 'w') as export_file:
            export_file.write("TRANSCRIPT:\n")
            export_file.write(transcript)
            export_file.write("\n\nSUMMARY:\n")
            export_file.write(summary)
            export_file.write("\n\nTRANSLATION:\n")
            export_file.write(translation)
        
        return export_file_path

    def process_audio(self, audio_file_path, target_lang):
        """Processes the audio file: transcribes, summarizes, translates, and exports."""
        # Step 1: Summarize the audio
        results = self.summarize_audio(audio_file_path)
        
        # Step 2: Translate the summary
        translated_summary = self.translate_summary(results["summary"], target_lang)
        
        # Step 3: Export the results
        export_path = self.export_results(results["summary"], results["transcript"], translated_summary)
        
        return {
            "transcript": results["transcript"],
            "summary": results["summary"],
            "translation": translated_summary,
            "export_path": export_path
        }
   

summary_service = SummaryService()
