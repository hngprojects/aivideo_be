from deepgram_captions import DeepgramConverter, srt
from api.utils.settings import settings

# dg_converter = DeepgramConverter()


from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

AUDIO_FILE = "scripts/testing.wav"


def add_subtitles_to_video(self, audio_file: str, video_file: str, output: str):
    try:
        deepgram = DeepgramClient(settings.DEEPGRAM_API_KEY)

        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )

        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)

        transcription = DeepgramConverter(dg_response=response)
        captions = srt(transcription)


        with open('subs.srt', 'w') as subtitles:
            subtitles.write(captions)

    except Exception as e:
        print(f"Exception: {e}")
