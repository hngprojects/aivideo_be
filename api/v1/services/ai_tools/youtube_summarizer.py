#!/usr/bin/env python3

"""Services to handle audio transcription"""

import os
from typing import Optional, Tuple
from typing_extensions import List
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_community.document_loaders.assemblyai import TranscriptFormat
from langchain_community.document_loaders import AssemblyAIAudioTranscriptLoader

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from api.utils.settings import settings


class ChatOpenRouter(ChatOpenAI):
    openai_api_base: str
    openai_api_key: str
    model_name: str

    def __init__(
        self,
        model_name: str,
        openai_api_key: Optional[str] = None,
        openai_api_base: str = "https://openrouter.ai/api/v1",
        **kwargs
    ):
        openai_api_key = openai_api_key or settings.OPENROUTER_API_KEY
        super().__init__(
            openai_api_base=openai_api_base,
            openai_api_key=openai_api_key,
            model_name=model_name,
            **kwargs
        )


class TranscriptionService:

    def __init__(self):
        self.assemblyai_api_key = settings.ASSEMBLYAI_API_KEY

    def init_chain(self):
        prompt_template = """Write a concise summary of the following:
        "{text}"
        CONCISE SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenRouter(
            temperature=0, 
            model_name="gpt-3.5-turbo-16k",
            openai_api_key=settings.OPENAI_API_KEY
        )
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        return llm_chain

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Tuple[List, str]:
        """
        Transcribes an audio file using AssemblyAI via LangChain.

        Args:
            audio_file_path (str): Path to the audio file to be transcribed.
            language (Optional[str]): The language of the audio. If None,
            AssemblyAI will auto-detect the language.

        Returns:
            Tuple[List, str]: The transcribed paragraphs with timestamps and summary.

        Raises:
            FileNotFoundError: If the audio file doesn't exist.
            Exception: If there's an error during transcription.
        """

        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        try:
            loader = AssemblyAIAudioTranscriptLoader(
                file_path=audio_file_path,
                api_key=self.assemblyai_api_key,
                transcript_format=TranscriptFormat.PARAGRAPHS  # Paragraph format
            )
            docs = loader.load()

            transcription_timestamp = []

            for doc in docs:
                # Each doc represents a paragraph. Get its content and timestamps.
                transcribe = {
                    "paragraph": doc.page_content,
                    "start_time": doc.metadata.get("start_time"),
                    "end_time": doc.metadata.get("end_time")
                }
                transcription_timestamp.append(transcribe)

            summary = self.summarize_transcription(docs)
            return (transcription_timestamp, summary)

        except Exception as e:
            print(f"An error occurred during transcription: {str(e)}")
            raise

    def summarize_transcription(self, transcription: List[Document]):
        """Returns a summarized version of the transcription

        Args:
            transcription (List[Document]): List of Document objects containing
            transcription

        Returns:
            str: Summary of the transcription
        """

        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(
            llm_chain=llm_chain, 
            document_variable_name="text"
        )

        summaries = []
        for doc in transcription:
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)

        final_summary = " ".join(summaries)
        return final_summary


transcription_service = TranscriptionService()
