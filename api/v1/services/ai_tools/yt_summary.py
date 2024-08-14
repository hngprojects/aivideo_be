from api.utils.transcriber import transcribe
from api.utils.pdf_transform import pdf_transform
from api.v1.services.ai_tools.summary import summary_service


class YoutubeSummary:
    async def summarize_video(self, video_pth):
        """Summarize a youtube video"""
        
        transcript = await transcribe(video_pth)
        pdf_file = await pdf_transform(transcript)
        full_summary = summary_service.summarize_pdf(pdf_file)
        return full_summary


yts_service = YoutubeSummary()
