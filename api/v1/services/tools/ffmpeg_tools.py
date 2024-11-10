import os, ffmpeg
from uuid import uuid4

from api.utils.settings import settings
from api.v1.services.tools.general_video_service import video_service


class FfmpegService:
    '''Service class for all ffmpeg tools'''

    def time_to_seconds(self, time_str: str):
        if time_str is None:
            return None
        time_parts = list(map(float, time_str.split(":")))
        if len(time_parts) == 3:  # HH:MM:SS format
            return time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
        elif len(time_parts) == 2:  # MM:SS format
            return time_parts[0] * 60 + time_parts[1]
        else:
            return time_parts[0]  # Just seconds
        
    
    def extract_audio_from_video(
        self, 
        input_video: str, 
        audio_extension: str = 'mp3',
        start_time: str = None,  # Start time in format 'HH:MM:SS' or 'seconds'
        end_time: str = None     # End time in format 'HH:MM:SS' or 'seconds'
    ):
        '''This extracts audio from a portion of a video file'''
        
        try:
            output_path = os.path.join(settings.TEMP_DIR, f'audio-{uuid4().hex}.{audio_extension}')
            
            # Check video duration to ensure start_time and end_time are within bounds
            video_details = video_service.get_video_details(input_video)
            video_duration = video_details['duration']

            start_seconds = self.time_to_seconds(start_time)
            end_seconds = self.time_to_seconds(end_time)

            # Validate start and end times
            if start_seconds and start_seconds >= video_duration:
                raise ValueError(f"Start time {start_time} exceeds video duration of {video_duration} seconds")
            if end_seconds and end_seconds > video_duration:
                raise ValueError(f"End time {end_time} exceeds video duration of {video_duration} seconds")
            if start_seconds and end_seconds and start_seconds >= end_seconds:
                raise ValueError(f"Start time {start_time} must be less than end time {end_time}")

            # # Prepare the ffmpeg input
            # ffmpeg_input = ffmpeg.input(input_video)

            # # Apply the start and end time if provided
            # if start_seconds:
            #     ffmpeg_input = ffmpeg_input.filter('atrim', start=start_seconds)
            # if end_seconds:
            #     ffmpeg_input = ffmpeg_input.filter('atrim', end=end_seconds)

            # # Execute the ffmpeg command
            # ffmpeg_command = (
            #     ffmpeg_input
            #     .output(output_path, format=audio_extension)
            #     .run(overwrite_output=True)
            # )
            
            
            # Prepare the FFmpeg input command
            command = ['ffmpeg', '-i', input_video]

            # Apply the start and end time if provided
            if start_seconds:
                command.extend(['-ss', str(start_seconds)])  # Start time
            if end_seconds:
                command.extend(['-to', str(end_seconds)])   # End time

            # Output format and file path
            command.extend(['-f', audio_extension, output_path])

            # Overwrite the output file without asking
            command.append('-y')
            
            return command, video_duration, output_path

        except ffmpeg.Error as e:
            print(f"ffmpeg error: {e.stderr.decode()}")
            raise e
        except ValueError as ve:
            print(f"Value error: {ve}")
            raise ve
        
    
    def resize_video(
        self,
        input_video: str,
        # aspect_ratio: str,
        width: int,
        height: int
    ):
        """
        Resizes a video to the specified width and height.

        Args:
            input_video (str): The path to the input video file.
            width (int): The desired width of the output video.
            height (int): The desired height of the output video.
        """

        try:
            video_details = video_service.get_video_details(input_video)
            video_duration = video_details['duration']
            
            output_path = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')
            
            # if aspect_ratio == 'square':
            #     width, height = (1000, 1000)
            # elif aspect_ratio == 'horizontal':
            #     width, height = (1920, 1080)
            # elif aspect_ratio =='vertical':
            #     width, height = (720, 1280)

            # filter_complex = (
            #     f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            #     f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            # )

            # (
            #     ffmpeg
            #     .input(input_video)
            #     .output(output_path, vf=filter_complex)
            #     .run(overwrite_output=True)
            # )
            
            command = [
                'ffmpeg',
                '-i', input_video,  # Input file
                '-vf', f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",  # Video filter
                '-y',  # Overwrite output file without asking
                output_path  # Output file
            ]
            
            return command, video_duration, output_path
        
        except ffmpeg.Error as e:
            raise e
    

    def compress_video(
        self, 
        input_video: str,
        compression_speed: str = 'medium'
    ):
        """
        Compress a video file while maintaining quality using ffmpeg.

        Args:
            input_video (str): Path to the input video file.
            compression_speed (str): Compression speed preset (default is 'medium'). Options: 'ultrafast', 'superfast', 
                        'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'.
        
        Options like `ultrafast` will give faster encoding but worse compression, while `veryslow` will give the best compression but take the longest time.

        Example:
            compress_video("input.mp4", "output.mp4", quality=20, speed="slow")
        """

        try:
            output_path = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')
            
            # Get video details
            video_details = video_service.get_video_details(input_video)

            # Get the resolution
            width = video_details['width']
            height = video_details['height']
            video_duration = video_details['duration']

            # Calculate the total number of pixels (width x height)
            total_pixels = width * height

            # Define CRF based on the resolution
            if total_pixels >= 1920 * 1080:  # 1080p and higher resolutions
                quality = 18  # Lower quality
            elif 1280 * 720 <= total_pixels < 1920 * 1080:  # 720p
                quality = 23  # Balanced quality
            elif 640 * 360 <= total_pixels < 1280 * 720:  # Lower than 720p
                quality = 28  # Higher quality for lower resolution
            else:
                quality = 30  # Very low resolutions, more compression``

            # (
            #     ffmpeg
            #     .input(input_video)
            #     .output(
            #         output_path, 
            #         crf=quality, 
            #         preset=compression_speed, 
            #         vcodec='libx264', 
            #         acodec='aac'
            #     )
            #     .run(overwrite_output=True)
            # )
            
            command = [
                'ffmpeg',
                '-i', input_video,  # Input file
                '-crf', str(quality),  # Constant Rate Factor (CRF) for video quality
                '-preset', compression_speed,  # Compression speed preset
                '-vcodec', 'libx264',  # Video codec
                '-acodec', 'aac',  # Audio codec
                '-y',  # Overwrite output file without asking
                output_path  # Output file
            ]
            
            return command, video_duration, output_path

        except ffmpeg.Error as e:
            raise e
    

    def create_gif_from_video(
        self, 
        input_video, 
        start_time=0, 
        duration=5, 
    ):
        """
        Convert a segment of a video to a GIF using ffmpeg-python.
        
        Args:
            input_video (str): Path to the input video file.
            output_gif (str): Path to save the output GIF file.
            start_time (int): Start time (in seconds) of the video to begin the GIF.
            duration (int): Duration (in seconds) of the GIF.
            width (int): Width of the output GIF.
        """

        try:
            video_details = video_service.get_video_details(input_video)
            video_duration = video_details['duration']
            
            output_gif = os.path.join(settings.TEMP_DIR, f'gif-{uuid4().hex}.gif')
            
            # Use ffmpeg to create a GIF
            # (
            #     ffmpeg
            #     .input(input_video, ss=start_time, t=duration)  # Input file, start time, and duration
            #     .filter('fps', fps=15)  # Set frame rate
            #     .filter('scale', 360, -1)  # Resize, keep aspect ratio (-1)
            #     .output(output_gif, loop=0)  # Output as a GIF
            #     .run()
            # )
            
            command = [
                'ffmpeg',
                '-i', input_video,  # Input file
                '-ss', str(start_time),  # Start time
                '-t', str(duration),  # Duration of the GIF
                '-vf', 'fps=15,scale=360:-1',  # Set frame rate and resize, keeping aspect ratio
                '-loop', '0',  # Loop the GIF indefinitely
                output_gif  # Output file
            ]
            
            return command, video_duration, output_gif

        except ffmpeg.Error as e:
            raise e
        

    def add_watermark_to_video(
        self, 
        input_video, 
        watermark_image, 
        position="top-right"
    ):
        """
        Adds a watermark image to a video using ffmpeg-python.
        
        Args:
            input_video (str): Path to the input video file.
            watermark_image (str): Path to the watermark image (PNG/JPG) file.
            output_video (str): Path to save the watermarked output video.
            position (str): Position of the watermark on the video (options: 'top-right', 'top-left', 'bottom-right', 'bottom-left').
            watermark_scale (float): Scale factor for the watermark image size.
        """

        # Define positions
        positions = {
            'top-right': 'main_w-overlay_w-10:10',
            'top-left': '10:10',
            'bottom-right': 'main_w-overlay_w-10:main_h-overlay_h-10',
            'bottom-left': '10:main_h-overlay_h-10',
            'center': '(main_w-overlay_w)/2:(main_h-overlay_h)/2'
        }
        
        # Get the chosen position coordinates
        if position not in positions:
            raise ValueError(f"Invalid position argument: {position}. Valid options: {list(positions.keys())}")
        
        position_coords = positions[position]
        
        try:
            video_details = video_service.get_video_details(input_video)
            video_duration = video_details['duration']
            
            output_video = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')

            # (
            #     ffmpeg
            #     .input(input_video)
            #     .output(
            #         output_video, 
            #         vf=f"movie={watermark_image},\
            #             scale=50:50 [watermark];\
            #             [in][watermark] overlay={position_coords}"
            #     )
            #     .run()
            # )
            
            command = [
                'ffmpeg',
                '-i', input_video,  # Input file
                '-i', watermark_image,  # Watermark image
                '-filter_complex', f"movie={watermark_image},scale=50:50[watermark];[in][watermark]overlay={position_coords}",  # Apply watermark
                '-y',  # Overwrite output file if it exists
                output_video  # Output file
            ]
            
            return command, video_duration, output_video

        except ffmpeg.Error as e:
            raise e


ffmpeg_service = FfmpegService()
