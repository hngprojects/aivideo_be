import json
import os
import uuid
from api.utils.settings import settings
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.parsers import OpenAIWhisperParser
from langchain_openai import ChatOpenAI
from deep_translator import GoogleTranslator
from openai import OpenAI as OI
from langchain_openai import OpenAI
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

class SummaryService():

    def __init__(self):
        self.translator = GoogleTranslator()
        self.client = OI(api_key=settings.OPENAI_API_KEY)
        self.llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)

    def init_chain(self):
        """Initializes the LLM chain with a prompt for summarization."""
        prompt_template = """Write a concise summary of the following:
        "{text}"
        CONCISE SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k", openai_api_key=settings.OPENAI_API_KEY)
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        return llm_chain

    def transcribe_audio(self, file_path):
           transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            response_format="text",
            file=open(file_path, "rb"),
        )
           return transcript

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

# Initialize the service
summary_service = SummaryService()
