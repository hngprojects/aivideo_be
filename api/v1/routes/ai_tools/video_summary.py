#!/usr/bin/env python3
"""Endpoints that handle video transcription and summarization"""


from fastapi import APIRouter, HTTPException


video_summary = APIRouter(prefix="/tools/video_summary", tags=["Tools"])


@video_summary.post("/summarize", status_code=200, response_model=success_response)
