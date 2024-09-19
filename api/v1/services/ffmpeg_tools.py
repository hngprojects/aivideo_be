import os, ffmpeg


class FfmpegService:
    '''Service class for all ffmpeg tools'''

    def extract_audio_from_video(
        self, 
        video_path: str, 
        output_path: str, 
        audio_extension: str = 'mp3'
    ):
        '''This extracts audio from a video file'''

        try:
            (
                ffmpeg
                .input(video_path)
                .output(output_path, format=audio_extension)
                .run(overwrite_output=True)
            )

        except ffmpeg.Error as e:
            raise e
        
    
    def resize_video(
        self,
        video_path: str,
        output_path: str,
        # aspect_ratio: str,
        width: int,
        height: int
    ):
        """
        Resizes a video to the specified width and height.

        Args:
            video_path (str): The path to the input video file.
            output_path (str): The path to the output (resized) video file.
            width (int): The desired width of the output video.
            height (int): The desired height of the output video.
        """

        try:
            # if aspect_ratio == 'square':
            #     width, height = (1000, 1000)
            # elif aspect_ratio == 'horizontal':
            #     width, height = (1920, 1080)
            # elif aspect_ratio =='vertical':
            #     width, height = (720, 1280)

            filter_complex = (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            )

            (
                ffmpeg
                .input(video_path)
                .output(output_path, vf=filter_complex)
                .run(overwrite_output=True)
            )
        
        except ffmpeg.Error as e:
            raise e
    

    def compress_video(
        self, 
        video_path: str,
        output_path: str,
        compression_speed: str = 'medium'
    ):
        """
        Compress a video file while maintaining quality using ffmpeg.

        Args:
            video_path (str): Path to the input video file.
            output_path (str): Path to save the compressed output video.
            compression_speed (str): Compression speed preset (default is 'medium'). Options: 'ultrafast', 'superfast', 
                        'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'.
        
        Options like `ultrafast` will give faster encoding but worse compression, while `veryslow` will give the best compression but take the longest time.

        Example:
            compress_video("input.mp4", "output.mp4", quality=20, speed="slow")
        """

        try:
            # Get video stream info using ffmpeg.probe
            probe = ffmpeg.probe(video_path)
            
            # Extract the video stream metadata
            video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')

            # Get the resolution
            width = int(video_stream['width'])
            height = int(video_stream['height'])

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

            (
                ffmpeg
                .input(video_path)
                .output(
                    output_path, 
                    crf=quality, 
                    preset=compression_speed, 
                    vcodec='libx264', 
                    acodec='aac'
                )
                .run(overwrite_output=True)
            )
            
        except ffmpeg.Error as e:
            raise e


ffmpeg_service = FfmpegService()
