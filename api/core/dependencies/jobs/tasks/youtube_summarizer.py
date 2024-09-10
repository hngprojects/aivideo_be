from api.utils.files import delete_file, download_audio_yt
import json, sys
from api.utils.transcripts import create_documents_from_transcript, get_paragraphs
from api.v1.services.ai_tools.video_subtitles import transcribe_audio_segments
from api.v1.services.ai_tools.summary import summary_service


payload = json.loads(sys.argv[1])

audio_file = None

try:
    print('Downloading and extracting audio from youtube video...')
    audio_file = download_audio_yt(payload.get('link'))

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
        "transcript_word_count": summary_service.calculate_word_count( transcript)
    }

    print('Done!!!')
    
    print(json.dumps(result))
except Exception as e:
    print('Youtube summarization failed')
finally:
    try:
        if audio_file:
            delete_file(audio_file)
    except Exception as deletion_error:
        print(str(deletion_error))
