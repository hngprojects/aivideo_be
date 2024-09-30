import os, requests, csv, yt_dlp, subprocess, requests, json
from io import BytesIO
from uuid import uuid4

from api.utils.settings import settings
from api.utils.pdf_builder import PDFBuilder
from api.v1.services.ai_tools.general import general_service
from api.v1.services.ffmpeg_tools import ffmpeg_service
from api.v1.services.ai_tools.pdf_summarizer import pdf_summary_service
from api.v1.services.ai_tools.audio_summarizer import audio_summary_service
from api.loggers.job_logger import job_logger


class YtVidSummarizerService:
    '''Youtube and video summarizer service'''

    def get_audio_stream(self, youtube_url: str):
        '''This function gets only the audio stream of the youtube video'''

        try:
            output_path = os.path.join(settings.TEMP_DIR, f'ytaud-{uuid4()}.mp3')
            # output_path = os.path.join(settings.TEMP_DIR, f'ytvid-{uuid4()}.mp4')

            # The command to run yt-dlp to download audio only
            command = [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "mp3",  # Specify the audio format (e.g., mp3, m4a, etc.)
                "-o", output_path,  # Output path where audio will be saved
                youtube_url  # YouTube video URL
            ]
            
            # Run the command using subprocess
            result = subprocess.run(
                command, 
                check=True,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )  
            print(result.stdout)
            job_logger.info(result.stdout)

            return output_path
        
        except subprocess.CalledProcessError as subp_e:
            job_logger.info(f"An error occurred")
            job_logger.info(f"Error details: {subp_e.stderr}")
            job_logger.info('Trying alternative')
            
            video_url = self.get_video_stream_alternative(youtube_url)

            job_logger.info('Downloading video')
            video_file = self.download_video_file(video_url)

            job_logger.info('Extracting audio from video')
            audio_path = self.extract_audio_from_video(video_file)

            return audio_path
        
        except Exception as e:
            raise e
        
    
    def get_video_stream_alternative(self, youtube_url: str):
        '''Fetch audio url'''

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://cobalt.tools/',
                'Content-Type': 'application/json',
                'Origin': 'https://cobalt.tools',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Priority': 'u=4'
            }
            data = {
                "url": youtube_url
            }
            response = requests.post(
                'https://api.cobalt.tools/', 
                headers=headers, 
                data=json.dumps(data)
            )

            # # Parse response data
            data = response.json()

            # Check if the response contains a valid download URL
            if data and 'url' in data:
                return data['url']
            else:
                raise Exception('Error converting video from youtube.com')
            
        except Exception as e:
            raise e
        

    # def download_audio_file(self, audio_url: str):
    def download_video_file(self, video_url: str):
        '''Download audio file from generated audio stream'''

        general_service.download_file(
            url=video_url,
            extension='mp4',
            prefix_file_name='ytaud'
        )
        
    
    def extract_audio_from_video(self, video_path: str):
        '''This function extracts audio from a video and returns the audio file'''

        output_path = os.path.join(settings.TEMP_DIR, f'ytaud-{uuid4()}.mp3')
        # Use ffmpeg to extract the audio from the video
        ffmpeg_service.extract_audio_from_video(
            input_video=video_path,
            output_path=output_path
        )
        return output_path

    
    def transcribe_audio(self, audio_path_or_url: str):
        '''This function transcribes audio into text'''

        return audio_summary_service.transcribe_audio(audio_path_or_url)
    

    def summarize_transcript(self, transcript: str, detail_level: str = 'short'):
        '''This function summarizes the transcript'''

        return pdf_summary_service.summarize_text(
            text=transcript, 
            detail_level=detail_level
        )

    
    def generate_transcript_with_timestamp(self, audio_path_or_url: str, as_srt: bool = False):
        '''This function generates a transcript with timestamps'''

        return audio_summary_service.generate_transcript_with_timestamp(
            audio_path_or_url,
            as_srt=as_srt
        )
    

    def save_transcript_and_summary_to_pdf(
        self, 
        transcript: str, 
        summary: str
    ):
        '''This function saves the transcript and summary of the transcript to a pdf file'''

        return audio_summary_service.save_to_pdf(
            summary=summary,
            transcript=transcript,
            prefix_file_name='ytvidsum'
        )
    

    def save_transcript_and_summary_to_csv(
        self, 
        transcript: str, 
        summary: str, 
        transcript_with_timestamp: str,
        transcript_with_timestamp_srt: str,
        save_path: str
    ):
        '''This function saves the transcript and summary of the transcript to a csv file'''
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Check if the file already exists
        file_exists = os.path.isfile(save_path)

        with open(save_path, "a", newline='') as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(['Transcript', 'Summary', 'Transcript with Timestamp', 'Subtitles'])

            writer.writerow([transcript, summary, transcript_with_timestamp, transcript_with_timestamp_srt])


ytvid_service = YtVidSummarizerService()
