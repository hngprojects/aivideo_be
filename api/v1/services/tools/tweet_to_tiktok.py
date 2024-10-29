from typing import List
from uuid import uuid4
import ffmpeg, os
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, ImageClip
from moviepy.video import fx as vfx

from api.utils.openai_service import openai_service
from api.utils.settings import settings
from api.v1.services.tools.general import general_service
from api.v1.services.tools.general_video_service import video_service
from api.v1.services.tools.ffmpeg_tools import ffmpeg_service


class TweetToTiktokService:
    
    def generate_scene_descriptions(self, script: str):
        
        response = openai_service.prompt_ai(
            prompt=f'Generate five simple and short scene descriptions not more than 30 characters that can be used as an image description for AI and stock images and videos API query for the following script and I do not want any form of numbering or bulleting on them. Also, do not say any other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:',
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
        
        return video_service.generate_custom_subtitles_from_audio(
            audio_file=audio_file,
            video_width=1080,
            video_height=1920
        )
        
    
    def add_subtitles_to_video(self, subtitles_file: str, video_file: str):
        '''This function adds subtitles to a video file'''
        
        return video_service.add_custom_subtitles_to_video(
            input_video=video_file,
            subtitles_file=subtitles_file
        )
        
    
    def process_media(
        self, 
        media_file: str, 
        display_time: float, 
        width: int=1080, 
        height: int=1920
    ):
        '''Process a single media file'''
        
        # Check for media extension
        file_ext = media_file.split('.')[-1].lower()
        is_image = file_ext in ['jpg', 'jpeg', 'png']
        is_video = file_ext in ['mp4', 'mov']
        
        if is_image:
            img_clip = ImageClip(media_file).set_duration(display_time)
            # Resize while preserving aspect ratio, then add padding
            img_clip = img_clip.resize(height=height) if img_clip.h > img_clip.w else img_clip.resize(width=width)
            final_clip = img_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")
            final_clip = final_clip.fadein(1).fadeout(1)  # Add transitions
            
        elif is_video:
            video_clip = VideoFileClip(media_file)
            # Resize video while preserving aspect ratio
            video_clip = video_clip.resize(height=height) if video_clip.h > video_clip.w else video_clip.resize(width=width)
            # Add padding to fit the specified width and height
            final_clip = video_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")
            clips = []
            remaining_time = display_time
            
            # Loop the video until the display time is met
            while remaining_time > 0:
                clip_duration = min(remaining_time, final_clip.duration)
                clips.append(final_clip.subclip(0, clip_duration))
                remaining_time -= clip_duration

            # Concatenate all the repeated clips to match the display time
            final_clip = concatenate_videoclips(clips).set_duration(display_time)
            # Apply fade-in and fade-out effects
            final_clip = final_clip.fadein(1).fadeout(1)
        
        return final_clip
            
            # original_duration = video_clip.duration
    
            # # If the video duration is different from display time, resize it accordingly
            # if original_duration != display_time:
            #     # Calculate speed factor
            #     speed_factor = original_duration / display_time
            #     # Adjust speed to match display time
            #     adjusted_clip = video_clip.fx(vfx.speedx, speed_factor).set_duration(display_time)
            # else:
            #     adjusted_clip = video_clip

            # # Apply fade-in and fade-out effects
            # final_clip = adjusted_clip.fadein(1).fadeout(1)
            # return final_clip
            
    
    def compose_video(
        self, 
        audio_file: str, 
        media_files: List[str],
        width: int=1080, 
        height: int=1920
    ):
        '''Function to bring all video components together'''
        
        audio_details = video_service.get_audio_details(audio_file)
        audio_duration = audio_details['duration']
        
        # Get display time per media file
        display_time_per_media = audio_duration / len(media_files)
            
        video_clips = [
            self.process_media(file, display_time_per_media, width, height) 
            for file in media_files
        ]
        
        # Concatenate the clips with transition effects
        video = concatenate_videoclips(video_clips, method="compose")

        # Add the audio file
        audio = AudioFileClip(audio_file)
        video = video.set_audio(audio)

        # Set the duration of the video to match the audio duration
        video = video.set_duration(audio.duration)

        output_video_file = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')
        # Write the final video file to the specified output path
        video.write_videofile(
            output_video_file, 
            codec='libx264', 
            audio_codec="aac", 
            fps=24, 
            threads=1,  # Try reducing threads for stability
            preset="ultrafast",  # Speeds up rendering at the cost of file size
        )
        
        # Clean up
        for file in media_files:
            os.remove(file)
        
        return output_video_file
       
    
    def resize_video(
        self, 
        video_file: str,
        width: int=1080, 
        height: int=1920
    ):
        '''Function to resize the video'''

        return ffmpeg_service.resize_video(
            input_video=video_file,
            width=width,
            height=height
        )
        

tweet_to_tiktok_service = TweetToTiktokService()
