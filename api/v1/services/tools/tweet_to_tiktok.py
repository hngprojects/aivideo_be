from typing import List
from uuid import uuid4
import ffmpeg, os

from api.utils.openai_service import openai_service
from api.utils.settings import settings
from api.v1.services.tools.general import general_service
from api.v1.services.tools.general_video_service import video_service
from api.v1.services.tools.ffmpeg_tools import ffmpeg_service


class TweetToTiktokService:
    
    def generate_scene_descriptions(self, script: str):
        
        response = openai_service.prompt_ai(
            prompt=f'Generate five simple and short scene descriptions not more than 100 characters that can be used as an image description for AI and stock images and videos API query for the following script and I do not want any form of numbering or bulleting on them. Also, do not say any other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:',
            system_role_desc='You are a great scene description generator.'
        )
        
        scenes = [scene.strip() for scene in response.strip().split('\n') if scene.strip()]
        return scenes
    
    
    def download_media(self, urls: List[str]):
        '''This function is used to dwonload media files'''
        
        save_paths = []
        for url in urls:
            if 'photo' in url or 'jpg' in url or 'png' in url or 'jpeg' in url:
                save_extension = 'jpg'
            elif 'video' in url or 'mp4' in url:
                save_extension = 'mp4'
            else:
                continue  # Skip unsupported media types
                
            file_path = general_service.download_file(url, extension=save_extension)
            save_paths.append(file_path)

        return save_paths
    

    def generate_audio(self, script: str, voice_over: str):
        '''This function generates audio from a script'''
        
        return video_service.convert_text_to_speech(script, voice_over)
    
    
    def generate_subtitles(self, audio_file: str):
        '''This function generates subtitles from an audio file'''
        
        video_service.generate_custom_subtitles_from_audio(
            audio_file=audio_file,
            video_width=1080,
            video_height=1920
        )
        
    
    def add_subtitles_to_video(self, subtitles_file: str, video_file: str):
        '''This function adds subtitles to a video file'''
        
        return video_service.add_custom_subtitles_to_video(
            video_file=video_file,
            subtitles_file=subtitles_file
        )
        
        
    def process_media(self, media_file: str, display_time: float):
        '''Process a single media file'''
        
        # Check for media extension
        is_image = media_file.split('.')[-1].lower() in ['jpg', 'jpeg', 'png']
        is_video = media_file.split('.')[-1].lower() in ['mp4', 'mov']
        
        if is_image:
            # Load image and loop it for display_time duration
            input_media = ffmpeg.input(media_file, loop=1, t=display_time)
            # Apply fade effects to the image
            processed_media = (
                input_media
                .filter('fade', type='in', start_time=0, duration=1)
                .filter('fade', type='out', start_time=display_time - 1, duration=1)
            )
            
        elif is_video:
            # Get video details
            video_details = video_service.get_video_details(media_file)
            
            # For video, load and set duration with fade in/out if necessary
            input_media = ffmpeg.input(media_file)
            
            # Apply fade effects to the video and trim/pad to fit display_time
            processed_media = (
                input_media
                .trim(start=0, end=min(display_time, video_details['duration']))  # Trim or extend
                .setpts(f'{display_time}/TBA*PTS')  # Adjust speed if video is shorter/longer
                .filter('fade', type='in', start_time=0, duration=1)
                .filter('fade', type='out', start_time=display_time - 1, duration=1)
            )

        # Save processed media to a temp file
        output_file = os.path.join(settings.TEMP_DIR, f'tmp-{uuid4().hex}.mp4')
        processed_media.output(output_file, vcodec='libx264', pix_fmt='yuv420p').run()
        return output_file
    
    
    def compose_video(self, audio_file: str, media_files: List[str]):
        '''Function to bring all video components together'''
        
        audio_details = video_service.get_audio_details(audio_file)
        audio_duration = audio_details['duration']
        
        # Get display time per media file
        display_time_per_media = audio_duration / len(media_files)
        
        processed_media = []
        for file in media_files:
            media = self.process_media(file, display_time_per_media)
            processed_media.append(media)
            
        # Concatenate processed media files and add audio
        input_streams = [ffmpeg.input(file) for file in processed_media]
        
        concat_video_path = os.path.join(settings.TEMP_DIR, f'tmp-{uuid4().hex}.mp4')
        ffmpeg.concat(*input_streams, v=1, a=0).output(concat_video_path)

        # Add audio to the concatenated video
        final_file = os.path.join(settings.TEMP_DIR, f'tmp-{uuid4().hex}.mp4')
        final_output = (
            ffmpeg
            .input(concat_video_path)
            .output(
                audio_file,
                final_file,
                vcodec='libx264', 
                acodec='aac', 
                pix_fmt='yuv420p'
            )
        )
        final_output.run()
        
        # Remove temp files
        os.remove(concat_video_path)
        for file in processed_media:
            os.remove(file)
        
        return final_file

    
    def resize_video(self, video_file: str):
        '''Function to resize the video'''

        return ffmpeg_service.resize_video(
            input_video=video_file,
            width=1080,
            height=1920
        )
        

tweet_to_tiktok_service = TweetToTiktokService()
