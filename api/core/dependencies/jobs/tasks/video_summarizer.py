"""Tasks that handle video transcription and summarization"""
from api.utils.files import delete_file
import json, sys
from api.utils.transcripts import create_documents_from_transcript, get_paragraphs
from api.v1.services.ai_tools.video_subtitles import convert_video_to_audio, transcribe_audio_segments
from api.v1.services.ai_tools.summary import summary_service

payload = json.loads(sys.argv[1])

audio_file = None
try:
    audio_file = convert_video_to_audio(payload.get('video_file'))
    transcription = transcribe_audio_segments(audio_file)
    documents, transcript = create_documents_from_transcript(transcription)
    summary = summary_service.summarize_transcript(documents)

    result = {
        "summary": summary,
        "summary_word_count": summary_service.calculate_word_count(summary),
        "transcript": get_paragraphs(transcription),
        "transcript_word_count": summary_service.calculate_word_count(transcript)
    }
    print(json.dumps(result))

except Exception as e:
    raise e

finally:
    try:
        delete_file(payload.get('video_file'))
        if audio_file:
            delete_file(audio_file)
    except Exception as deletion_error:
        print(str(deletion_error))
