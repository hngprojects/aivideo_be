"""Tasks that handle video transcription and summarization"""
from api.utils.files import delete_file
import json, sys
from api.utils.transcripts import create_documents_from_transcript, get_paragraphs
from api.v1.services.ai_tools.video_subtitles import convert_video_to_audio, transcribe_audio_segments
from api.v1.services.ai_tools.summary import summary_service
from api.utils.minio_service import minio_service


payload = json.loads(sys.argv[1])

audio_file = None
video_url = payload.get('video_url')

print(f'Downloading and opening video file from {video_url}...')
video_file = minio_service.download_file_from_minio(video_url)

try:
    print('Extracting audio from video...')
    audio_file = convert_video_to_audio(video_file)

    print('Transcribing audio...')
    transcription = transcribe_audio_segments(audio_file)

    print('Generating transcript documents for summarization...')
    documents, transcript = create_documents_from_transcript(transcription)

    print('Summarizing transcript...')
    summary = summary_service.summarize_transcript(documents)

    result = {
        "summary": summary,
        "summary_word_count": summary_service.calculate_word_count(summary),
        "transcript": get_paragraphs(transcription),
        "transcript_word_count": summary_service.calculate_word_count(transcript)
    }

    print('Done!!!')
    
    print(json.dumps(result))

except Exception as e:
    print('Video summarization failed')

finally:
    try:
        delete_file(video_file)
        if audio_file:
            delete_file(audio_file)
    except Exception as deletion_error:
        print(str(deletion_error))
