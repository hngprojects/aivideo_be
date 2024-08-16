from api.utils.transcriber import transcribe
from api.utils.pdf_transform import pdf_transform
from api.v1.services.ai_tools.summary import summary_service


class YoutubeSummary:
    def summarize_video(self, video_pth):
        """Summarize a youtube video"""

        transcript = transcribe(video_pth)
        pdf_file = pdf_transform(transcript)
        full_summary = summary_service.summarize_pdf(pdf_file)
        return {"summary": full_summary, "transcript": transcript}


yts_service = YoutubeSummary()
