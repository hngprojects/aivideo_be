from typing import List
from uuid import uuid4
import ffmpeg, os
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, ImageClip, CompositeVideoClip
from moviepy.video import fx as vfx

from api.utils.openai_service import openai_service
from api.utils.settings import settings
from api.v1.services.tools.general import general_service
from api.v1.services.tools.general_video_service import video_service
from api.v1.services.tools.ffmpeg_tools import ffmpeg_service


class TweetToTiktokService:
    
    def generate_scene_descriptions(self, script: str, no_of_scenes: int = 5):
        
        response = openai_service.prompt_ai(
            prompt=f'Generate {no_of_scenes} simple and short scene descriptions not more than 30 characters that can be used as an image description for AI and stock images and videos API query for the following script and I do not want any form of numbering or bulleting on them. Also, do not say any other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:',
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
    
    
    def generate_subtitles(self, audio_file: str, width: int=1080, height: int=1920):
        '''This function generates subtitles from an audio file'''
        
        return video_service.generate_custom_subtitles_from_audio(
            audio_file=audio_file,
            video_width=width,
            video_height=height
        )
        
    
    def add_subtitles_to_video(self, subtitles_file: str, video_file: str):
        '''This function adds subtitles to a video file'''
        
        return video_service.add_custom_subtitles_to_video(
            input_video=video_file,
            subtitles_file=subtitles_file
        )
        
    
    # def process_media(
    #     self, 
    #     media_file: str, 
    #     display_time: float, 
    #     width: int=1080, 
    #     height: int=1920
    # ):
    #     '''Process a single media file'''
        
    #     # Check for media extension
    #     file_ext = media_file.split('.')[-1].lower()
    #     is_image = file_ext in ['jpg', 'jpeg', 'png']
    #     is_video = file_ext in ['mp4', 'mov']
        
    #     if is_image:
    #         img_clip = ImageClip(media_file).set_duration(display_time)
    #         # Resize while preserving aspect ratio, then add padding
    #         img_clip = img_clip.resize(height=height) if img_clip.h > img_clip.w else img_clip.resize(width=width)
    #         final_clip = img_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")
    #         final_clip = final_clip.fadein(1).fadeout(1)  # Add transitions
            
    #     elif is_video:
    #         video_clip = VideoFileClip(media_file)
    #         # Resize video while preserving aspect ratio
    #         video_clip = video_clip.resize(height=height) if video_clip.h > video_clip.w else video_clip.resize(width=width)
    #         # Add padding to fit the specified width and height
    #         final_clip = video_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")
    #         clips = []
    #         remaining_time = display_time
            
    #         # Loop the video until the display time is met
    #         while remaining_time > 0:
    #             clip_duration = min(remaining_time, final_clip.duration)
    #             clips.append(final_clip.subclip(0, clip_duration))
    #             remaining_time -= clip_duration

    #         # Concatenate all the repeated clips to match the display time
    #         final_clip = concatenate_videoclips(clips, method='compose').set_duration(display_time)
    #         # Apply fade-in and fade-out effects
    #         final_clip = final_clip.fadein(1).fadeout(1)
        
    #     return final_clip
            
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
            
    
    # def compose_video(
    #     self, 
    #     audio_file: str, 
    #     avatar_file: str, 
    #     media_files: List[str],
    #     width: int=1080, 
    #     height: int=1920
    # ):
    #     '''Function to bring all video components together'''
        
    #     audio_details = video_service.get_audio_details(audio_file)
    #     audio_duration = audio_details['duration']
    #     print('Audio details gotten')
        
    #     # Get display time per media file
    #     display_time_per_media = audio_duration / len(media_files)
        
    #     # Avatar clip
    #     avatar_clip = VideoFileClip(avatar_file).set_duration(audio_duration)
    #     avatar_clip = avatar_clip.resize(height=height) if avatar_clip.h > avatar_clip.w else avatar_clip.resize(width=width)
            
    #     video_clips = [
    #         self.process_media(file, display_time_per_media, width, height) 
    #         for file in media_files
    #     ]
    #     print('All media processed')
        
    #     # Concatenate the clips with transition effects
    #     video = concatenate_videoclips(video_clips, method="compose")
    #     print('Media clips concatenated')

    #     # Add the audio file
    #     audio = AudioFileClip(audio_file)
    #     video = video.set_audio(audio)

    #     # Set the duration of the video to match the audio duration
    #     video = video.set_duration(audio.duration)
    #     print('Audio set and video duration set')

    #     output_video_file = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')
    #     # Write the final video file to the specified output path
    #     video.write_videofile(
    #         output_video_file, 
    #         codec='libx264', 
    #         audio_codec="aac", 
    #         fps=24, 
    #         # threads=1,  # Try reducing threads for stability
    #         # preset="fast",  # Speeds up rendering at the cost of file size
    #         threads=4, 
    #         preset="faster", 
    #         ffmpeg_params=["-crf", "23"],
    #         # progress_bar=True
    #     )
    #     print('Video file written')
        
    #     # Clean up
    #     for file in media_files:
    #         os.remove(file)
        
    #     return output_video_file
    
    # def compose_video(
    #     self,
    #     audio_file: str, 
    #     media_files: List[str],
    #     talking_avatar_file: str,
    #     overlay_durations: List[float],
    #     width: int = 1080, 
    #     height: int = 1920
    # ):
    #     """Function to bring all video components together"""
    #     audio_details = video_service.get_audio_details(audio_file)
    #     audio_duration = audio_details['duration']
    #     print('Audio details gotten')
        
    #     display_time_per_media = audio_duration / len(media_files)
        
    #     avatar_clip = VideoFileClip(talking_avatar_file).set_duration(audio_duration)
    #     avatar_clip = avatar_clip.resize(height=height) if avatar_clip.h > avatar_clip.w else avatar_clip.resize(width=width)
        
    #     overlay_clips = []
    #     for idx, media_file in enumerate(media_files):
    #         overlay_clip = self.process_media(media_file, overlay_durations[idx], width, height)
    #         # Position overlay clip on top of avatar and set start time
    #         overlay_start_time = sum(overlay_durations[:idx])
    #         overlay_clip = overlay_clip.set_start(overlay_start_time).set_position("center")
    #         overlay_clips.append(overlay_clip)
        
    #     # Create composite clip with overlays
    #     final_video = CompositeVideoClip([avatar_clip] + overlay_clips, size=(width, height))
    #     final_video = final_video.set_duration(audio_duration)
        
    #     # Add audio
    #     audio = AudioFileClip(audio_file)
    #     final_video = final_video.set_audio(audio)
        
    #     output_video_file = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')
    #     final_video.write_videofile(
    #         output_video_file,
    #         codec='libx264',
    #         audio_codec="aac",
    #         fps=24,
    #         threads=4,
    #         preset="faster",
    #         ffmpeg_params=["-crf", "23"]
    #     )
    #     print('Video file written')
    #     return output_video_file
    
    # def process_overlay_clips(
    #     self,
    #     overlay_media_files: List[str],
    #     overlay_duration: float,
    #     width: int = 1080,
    #     height: int = 1920
    # ):
    #     """
    #     Processes overlay media files and prepares them with appropriate durations and sizes.
    #     """
    #     overlay_clips = []
    #     for index, media_file in enumerate(overlay_media_files):
    #         file_ext = media_file.split('.')[-1].lower()
    #         is_image = file_ext in ['jpg', 'jpeg', 'png']
    #         is_video = file_ext in ['mp4', 'mov']

    #         if is_image:
    #             overlay_clip = ImageClip(media_file).set_duration(overlay_duration)
    #             overlay_clip = overlay_clip.resize(height=height) if overlay_clip.h > overlay_clip.w else overlay_clip.resize(width=width)
    #         elif is_video:
    #             video_clip = VideoFileClip(media_file)
    #             overlay_clip = video_clip.subclip(0, min(overlay_duration, video_clip.duration))
    #             overlay_clip = overlay_clip.resize(height=height) if overlay_clip.h > overlay_clip.w else overlay_clip.resize(width=width)

    #         # Set start time dynamically based on the index
    #         start_time = index * overlay_duration
    #         overlay_clip = overlay_clip.set_start(start_time).set_duration(overlay_duration)
    #         overlay_clips.append(overlay_clip)

    #         print(f'Processed overlay clip {media_file} (start: {start_time}s, duration: {overlay_duration}s)')

    #     return overlay_clips


    # def compose_video(
    #     self,
    #     base_video_file: str,
    #     overlay_media_files: List[str],
    #     audio_file: str,
    #     width: int = 1080,
    #     height: int = 1920
    # ) -> str:
    #     """
    #     Composes the final video by combining the base video, overlays, and audio.
    #     """
    #     # Get audio duration
    #     audio_details = video_service.get_audio_details(audio_file)
    #     audio_duration = audio_details['duration']

    #     print('Audio details retrieved')

    #     # Calculate overlay duration
    #     num_media_files = len(overlay_media_files)
    #     overlay_duration = audio_duration / (num_media_files + 1)

    #     # Load and resize the base video
    #     base_video_clip = VideoFileClip(base_video_file)
    #     base_video_clip = base_video_clip.resize(height=height) if base_video_clip.h > base_video_clip.w else base_video_clip.resize(width=width)
    #     base_video_clip = base_video_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")
    #     base_video_clip = base_video_clip.set_duration(audio_duration)

    #     print('Base video processed')

    #     # Process overlay clips
    #     overlay_clips = self.process_overlay_clips(overlay_media_files, overlay_duration, width, height)

    #     # Composite overlays onto the base video
    #     final_video = CompositeVideoClip([base_video_clip] + overlay_clips)

    #     print('Overlays added to the base video')

    #     # Add audio to the final video
    #     audio = AudioFileClip(audio_file)
    #     final_video = final_video.set_audio(audio)

    #     # Set the final duration to match the audio
    #     final_video = final_video.set_duration(audio.duration)

    #     print('Audio added to final video')

    #     # Write the final video file
    #     output_video_file = os.path.join(settings.TEMP_DIR, f'final-video-{uuid4().hex}.mp4')
    #     final_video.write_videofile(
    #         output_video_file,
    #         codec='libx264',
    #         audio_codec='aac',
    #         fps=24,
    #         threads=1,
    #         preset='ultrafast',
    #         ffmpeg_params=['-crf', '23']
    #     )

    #     print('Final video file written')

    #     return output_video_file

    def compose_video(
        self,
        base_video_file: str,
        overlay_media_files: List[str],
        audio_file: str,
        # interval: float,
        # overlay_duration: float,
        num_overlays: int,
        width: int = 1080,
        height: int = 1920
    ) -> str:
        """
        Processes the base avatar video and overlays media clips dynamically, alternating between them.

        Args:
            base_video_file (str): Path to the avatar base video.
            overlay_media_files (List[str]): List of overlay media files.
            audio_file (str): Path to the audio file.
            interval (float): Interval between overlays (in seconds).
            overlay_duration (float): Duration of each overlay clip (in seconds).
            width (int): Target width of the video (default: 1080).
            height (int): Target height of the video (default: 1920).

        Returns:
            str: Path to the final output video file.
        """
        
        # def prepare_overlay_clip(overlay_clip, target_size):
        #     """
        #     Resize and pad the overlay clip to ensure it matches the target size.
        #     """
            
        #     overlay_clip = overlay_clip.resize(height=target_size[1]) if overlay_clip.h > overlay_clip.w else overlay_clip.resize(width=target_size[0])
        #     overlay_clip = overlay_clip.on_color(size=target_size, color=(0, 0, 0), pos="center")
        #     return overlay_clip
        
        # Load and resize the base video
        base_video_clip = VideoFileClip(base_video_file)
        base_video_clip = base_video_clip.resize(height=height) if base_video_clip.h > base_video_clip.w else base_video_clip.resize(width=width)
        base_video_clip = base_video_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")

        # Get audio details and duration
        audio = AudioFileClip(audio_file)
        audio_duration = audio.duration

        print(f"Audio duration: {audio_duration}s")

        # Set base video duration to match audio duration
        base_video_clip = base_video_clip.set_duration(audio_duration)
        
        # Calculate dynamic interval and overlay duration
        interval = audio_duration / (num_overlays + 1)  # Time between start of overlays
        overlay_duration = min(interval * 0.8, 5)  # Overlays are 80% of the interval, capped at 5 seconds

        # Prepare overlay clips
        overlay_clips = []
        current_time = 0
        overlay_index = 0
        while current_time < audio_duration and overlay_index < len(overlay_media_files):
            overlay_file = overlay_media_files[overlay_index]
            file_ext = overlay_file.split('.')[-1].lower()

            if file_ext in ['jpg', 'jpeg', 'png']:
                overlay_clip = ImageClip(overlay_file).set_duration(overlay_duration)
            elif file_ext in ['mp4', 'mov']:
                video_clip = VideoFileClip(overlay_file)
                overlay_clip = video_clip.subclip(0, min(overlay_duration, video_clip.duration))
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Resize overlay clip and match the base video size
            overlay_clip = overlay_clip.resize(height=height) if overlay_clip.h >= overlay_clip.w else overlay_clip.resize(width=width)
            # Resize and position overlay clip to match the base video size
            overlay_clip = overlay_clip.on_color(size=(width, height), color=(0, 0, 0), pos="center")
            # overlay_clip = overlay_clip.resize(height=height).on_color(size=(width, height), color=(0, 0, 0), pos="center")
            overlay_clip = overlay_clip.set_start(current_time).set_duration(overlay_duration)
            overlay_clip = overlay_clip.crossfadein(1).crossfadeout(1)  # Smooth transitions

            overlay_clips.append(overlay_clip)
            current_time += interval
            overlay_index = (overlay_index + 1) % len(overlay_media_files)  # Cycle through overlays

        # Combine base video and overlays
        final_video = CompositeVideoClip([base_video_clip] + overlay_clips)

        # Set audio to the final video
        final_video = final_video.set_audio(audio)
        final_video = final_video.set_duration(audio_duration)

        # Export the video
        output_video_file = os.path.join(settings.TEMP_DIR, f'final-video-{uuid4().hex}.mp4')
        final_video.write_videofile(
            output_video_file,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            threads=4,
            preset='ultrafast',
            ffmpeg_params=['-crf', '23']
        )

        print(f"Final video saved to {output_video_file}")
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
            height=height,
            use_subprocess=False
        )
        

tweet_to_tiktok_service = TweetToTiktokService()
