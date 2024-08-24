#!/usr/bin/env python3

"""transcripts function utils"""


from typing import List


def get_paragraphs(transcription: dict) -> List:
    """Get paragraphs from transcription"""
    paragraphs = []

    for segment in transcription['segments']:
        paragraph = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        paragraphs.append({
            'paragraph': paragraph,
            'start_time': start_time,
            'end_time': end_time
        })
    return paragraphs
