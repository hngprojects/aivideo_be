import os, requests, csv, yt_dlp, pickle, subprocess
from io import BytesIO
import assemblyai as aai
from uuid import uuid4
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from api.utils.settings import settings
from api.utils.pdf_builder import PDFBuilder
from api.v1.services.ffmpeg_tools import ffmpeg_service
from api.v1.services.ai_tools.pdf_summarizer import pdf_summary_service
from api.v1.services.ai_tools.audio_summarizer import audio_summary_service


class YtVidSummarizerService:
    '''Youtube and video summarizer service'''

    # def __init__(self):
        # aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        # self.transcriber = aai.Transcriber()

        # # Authenticate youtube request with Google
        # CLIENT_SECRETS_FILE = "google_secret.json"
        # SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

        # credentials = None
        # token_pickle = 'token.pickle'

        # # Check if we have saved credentials
        # if os.path.exists(token_pickle):
        #     with open(token_pickle, 'rb') as token:
        #         credentials = pickle.load(token)

        # # If no valid credentials are available, let the user log in.
        # if not credentials or not credentials.valid:
        #     if credentials and credentials.expired and credentials.refresh_token:
        #         credentials.refresh(Request())
        #     else:
        #         flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        #         credentials = flow.run_local_server(host='0.0.0.0', port=7003)

        #     # Save the credentials for the next run
        #     with open(token_pickle, 'wb') as token:
        #         pickle.dump(credentials, token)

        # self.oauth_token = credentials.token


    def get_audio_stream(self, youtube_url: str):
        '''This function gets only the audio stream of the youtube video'''

        # ydl_opts = {
        #     'format': 'bestaudio/best',
        #     'noplaylist': True,
        #     'quiet': True,
        #     'outtmpl': '-',
        #     'extractaudio': True,
        #     'audioformat': 'mp3',
        #     'postprocessors': [{
        #         'key': 'FFmpegExtractAudio',
        #         'preferredcodec': 'mp3',
        #         'preferredquality': '192',
        #     }],
        #     'no_warnings': True,
        #     # 'http_headers': {
        #     #     'Authorization': f'Bearer {self.oauth_token}',  # Add the OAuth token to the request
        #     # },
        #     # 'cookiefile': 'youtube_cookies.txt',  # Path to the cookies.txt file
        # }

        # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #     try:
        #         info_dict = ydl.extract_info(youtube_url, download=False)
        #         audio_url = info_dict['url']
        #         return audio_url
        #     except Exception as e:
        #         raise e

        try:
            output_path = os.path.join(settings.TEMP_DIR, f'ytaud-{uuid4()}.mp3')

            # The command to run yt-dlp to download audio only
            command = [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "mp3",  # Specify the audio format (e.g., mp3, m4a, etc.)
                "-o", output_path,  # Output path where audio will be saved
                # "--cookies", 'youtube_cookies.txt',  # Use the cookies file for authentication
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
            return output_path
        
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")
            print("Error details:", e.stderr)
            raise e
    

    def download_audio_file(self, audio_url: str):
        '''Download audio file from generated audio stream'''

        try:
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()  # Check for errors in the response
            
            file_path = os.path.join(settings.TEMP_DIR, f'ytaud-{uuid4()}.mp3')
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return file_path

        except requests.RequestException as e:
            raise e

    
    # def download_youtube_video(self, youtube_url: str):
    #     '''This function downloads a youtube video(s) and saves it to a temporary storage'''

    #     output_path = os.path.join(settings.TEMP_DIR, f'ytvid-{uuid4()}.mp4')
    #     ydl_opts = {
    #         'format': 'worst',  # Select the worst quality
    #         'outtmpl': output_path,
    #         'nocheckcertificate': True,
    #     }

    #     try:
    #         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #             ydl.download([youtube_url])
    #             return output_path
            
    #     except Exception as e:
    #         raise e 
        
    
    def extract_audio_from_video(self, video_path: str):
        '''This function extracts audio from a video and returns the audio file'''

        output_path = os.path.join(settings.TEMP_DIR, f'ytaud-{uuid4()}')
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
        summary: str, 
        transcript_with_timestamp: str
    ):
        '''This function saves the transcript and summary of the transcript to a pdf file'''

        pdf_buffer = BytesIO()
        pdf_builder = PDFBuilder(pdf_buffer)

        file_path = os.path.join(settings.TEMP_DIR, f"ytvidsum-{uuid4()}.pdf")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Add transcript to pdf file
        pdf_builder.add_section(title='Transcript', text=transcript)

        # Add summary to pdf file
        pdf_builder.add_section(title='Summary', text=summary)

        # Add transcript with timestamp to pdf file
        pdf_builder.add_section(title='Transcript with Timestamp', text=transcript_with_timestamp)

        # Build pdf
        pdf_builder.build()

        # Save the PDF content to a file
        pdf_buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.read())

        pdf_buffer.close()

        return file_path
    

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
