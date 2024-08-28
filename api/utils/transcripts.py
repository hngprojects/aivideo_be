#!/usr/bin/env python3

"""transcripts function utils"""


from typing import List, Dict, Any, Tuple
from langchain.schema import Document


def get_paragraphs(transcription: List) -> List:
    """Get paragraphs from transcription"""
    paragraphs = []

    for segment in transcription:
        paragraph = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        paragraphs.append({
            'paragraph': paragraph,
            'start_time': start_time,
            'end_time': end_time
        })
    return paragraphs


def create_documents_from_transcript(
    transcript_segments: List[Dict[str, Any]]
) -> Tuple[List[Document], str]:
    """
    Convert transcript segments into a list of Langchain Document objects.

    Args:
    transcript_segments (List[Dict[str, Any]]): A list of dictionaries, each containing
        'start', 'end', and 'text' keys, along with any other relevant information.

    Returns:
    List[Document]: A list of Langchain Document objects.
    """
    documents = []
    transcript = ""

    for segment in transcript_segments:
        text = segment['text']
        transcript += text
        start_time = segment['start']
        end_time = segment['end']

        metadata = {
            'start_time': start_time,
            'end_time': end_time,
        }

        for key, value in segment.items():
            if key not in ['text', 'start', 'end']:
                metadata[key] = value

        doc = Document(
            page_content=text,
            metadata=metadata
        )

        documents.append(doc)

    return (documents, transcript)
