import os
from pathlib import Path
import wave
import random
from uuid import uuid4
import openai
import ffmpeg
import requests
from moviepy.editor import VideoFileClip

from deepgram_captions import DeepgramConverter, srt
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

from api.utils.settings import settings
from api.v1.services.tools.audio_summarizer import audio_summary_service


class GeneralVideoService:

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def download_file(self, url, save_path):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Large file downloaded successfully and saved as {save_path}")

            return save_path
        except requests.RequestException as e:
            print(f"Error downloading large file: {e}")

    
    def get_audio_duration(self, audio_path):
        with wave.open(audio_path, "rb") as audio_file:
            num_frames = audio_file.getnframes()
            frame_rate = audio_file.getframerate()
            duration_seconds = num_frames / frame_rate
            return int(duration_seconds)

    
    def compress_video(self, input_file, bitrate: int=700):
        """
        Compresses a video file using moviepy.

        Parameters:
        - input_file: Path to the input video file.
        - output_file: Path to the output compressed video file.
        - bitrate: Desired bitrate for the output video (e.g., '1000k' for 1000 kbps).
        """

        output_file = os.path.join(settings.STORAGE_DIR, 'video', f'video-{str(uuid4().hex)}.mp4')
        try:
            clip = VideoFileClip(input_file)
            clip.write_videofile(output_file, bitrate=f"{bitrate}k")
            print(f"Video compressed successfully: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error compressing video: {e}")
            return input_file


    # TODO: Update this function to use replicate and pick a voice from the voices in the db
    def convert_text_to_speech(self, script, voice_over='man'):
        file_path = os.path.join(settings.TEMP_DIR, f'audio-{str(uuid4().hex)}.wav')

        female = ["nova", "shimmer"]
        neutral = ["fable", "alloy"]
        male = ["echo", "onyx"]

        voice = male[random.randint(0, 1)]

        if voice_over == 'woman':
            voice = female[random.randint(0, 1)]
        elif voice_over == 'neutral':
            voice = neutral[random.randint(0, 1)]

        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=script,
            response_format="wav"
        )

        response.stream_to_file(file_path)
        return file_path
    

    def generate_subtitles_from_audio(self, audio_file: str):
        try:
            captions = audio_summary_service.generate_transcript_with_timestamp(
                audio_file,
                as_srt=True
            )

            subtitles_file = os.path.join(settings.TEMP_DIR, f'subtitles-{uuid4().hex}.srt')
            with open(subtitles_file, 'w') as subtitles:
                subtitles.write(captions)
            
            return subtitles_file

        except Exception as e:
            print(f"Exception: {e}")
    
    
    def convert_milliseconds_to_centiseconds(self, timestamp):
        '''This function converts milliseconds to centiseconds'''
        
        hours, minutes, seconds = timestamp.split(':')
        sec, millis = seconds.split('.')
        # Convert milliseconds to centiseconds
        centis = int(millis) // 10
        return f"{hours}:{minutes}:{sec}.{centis:02d}"
    
    
    def convert_subtitles_to_dict(self, captions: str, as_srt=False):
        
        captions_list = captions.split('\n\n')
        formatted_subtitles = []

        for caption in captions_list:
            single_caption_list = caption.split('\n')
            
            timestamp_list = single_caption_list[0].split('-->')
            text = single_caption_list[-1].upper()
            start = timestamp_list[0].strip()
            end = timestamp_list[1].strip()
            
            start = start if len(start) == 12 else f'00:{start}'
            end = end if len(end) == 12 else f'00:{end}'
            
            if text == '':
                continue
            
            formatted_subtitles.append({
                "start": self.convert_milliseconds_to_centiseconds(start) if not as_srt else start,
                "end": self.convert_milliseconds_to_centiseconds(end) if not as_srt else end,
                "text": text
            })
        
        return formatted_subtitles
    
    
    def generate_custom_subtitles_from_audio(
        self, 
        audio_file: str, 
        video_width: int, 
        video_height: int
    ):

        base_font_path = os.path.abspath('presets/fonts')

        fonts = {
            'impact': f'{base_font_path}/impact.ttf',
            'comic sans ms': f'{base_font_path}/comic.ttf',
            'ar christy': f'{base_font_path}/ARCHRISTY.ttf',
            'ar carter': f'{base_font_path}/ARCARTER.ttf',
            'ar bonnie': f'{base_font_path}/ARBONNIE.ttf',
            'levenim mt': f'{base_font_path}/lvnm.ttf',
            'segoe script': f'{base_font_path}/segoesc.ttf',
            'segoe print': f'{base_font_path}/segoepr.ttf',
            'segoe print bold': f'{base_font_path}/segoeprb.ttf',
            'bebas neue': f'{base_font_path}/BebasNeue.ttf',
            'montserrat bold': f'{base_font_path}/Montserrat-Bold.ttf',
            'poppins bold': f'{base_font_path}/Poppins-Bold.ttf',
            'lobster': f'{base_font_path}/Lobster-Regular.ttf',
            'oswald': f'{base_font_path}/Oswald-Regular.ttf',
            'raleway': f'{base_font_path}/Raleway-Regular.ttf',
            'anton': f'{base_font_path}/Anton-Regular.ttf',
            'pacifico': f'{base_font_path}/Pacifico-Regular.ttf',
            'roboto bold': f'{base_font_path}/Roboto-Bold.ttf',
            'playfair display': f'{base_font_path}/PlayfairDisplay-Regular.ttf',
            'dancing script': f'{base_font_path}/DancingScript-Regular.ttf',
            'amatic sc': f'{base_font_path}/AmaticSC-Regular.ttf',
            'open sans bold': f'{base_font_path}/OpenSans-Bold.ttf',
            'merriweather bold': f'{base_font_path}/Merriweather-Bold.ttf',
            'bangers': f'{base_font_path}/Bangers-Regular.ttf',
            'caveat': f'{base_font_path}/Caveat-Regular.ttf',
            'fredoka one': f'{base_font_path}/FredokaOne-Regular.ttf',
            'chewy': f'{base_font_path}/Chewy-Regular.ttf',
            'great vibes': f'{base_font_path}/GreatVibes-Regular.ttf',
            'shadows into light': f'{base_font_path}/ShadowsIntoLight-Regular.ttf',
            'archivo': f'{base_font_path}/ArchivoBlack-Regular.ttf'
        }


        primary_colors = [
            # "&H00FFFFFF",  # White
            "&H00FFFF00",  # Yellow
            "&H00FF00FF",  # Magenta
            "&H00FF0000",  # Red
            "&H0000FF00",  # Green
            "&H000000FF",  # Blue
            "&H00FFA500",  # Orange
            "&H00A52A2A",  # Brown
        ]

        outline_colors = [
            "&H00000000",  # Black
            "&H00FFFFFF",  # White
            "&H00FFFF00",  # Yellow
            "&H0000FF00",  # Green
            "&H000000FF",  # Blue
            "&H00808080",  # Gray
        ]

        shadow_colors = [
            "&H00000000",  # Black
            "&H00808080",  # Gray
            "&H00FFFFFF",  # White
        ]

        background_colors = [
            "&H00000000",  # Black
            "&H00FFFFFF",  # White
            "&H00202020",  # Dark Gray
            "&H00333333",  # Charcoal Gray
            "&H00F5F5DC",  # Beige
            "&H00B0C4DE",  # Light Steel Blue
        ]

        # Select random styles
        font_name = random.choice(list(fonts.keys()))
        primary_color = random.choice(primary_colors)
        outline_color = random.choice(outline_colors)
        shadow_color = random.choice(shadow_colors)
        background_color = random.choice(background_colors)
        
        # .ass subtitle file header
        header = f"""[Script Info]
        PlayResY: {video_height}
        PlayResX: {video_width}
        WrapStyle: 1

        [V4+ Styles]
        Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, BorderStyle, Outline, Shadow, Alignment, Encoding
        Style: S00, {font_name}, 70, {primary_color}, {outline_color}, {background_color}, 3, 0, 1, 5, 0

        [Fonts]
        """
        
        try:
            subtitles_file = os.path.join(settings.TEMP_DIR, f'subtitles-{uuid4().hex}.ass')
            captions = audio_summary_service.generate_transcript_with_timestamp(
                audio_file, 
                as_srt=False
            ).strip()
            
            formatted_subtitles = self.convert_subtitles_to_dict(captions)

            with open(subtitles_file, 'w') as subtitles:
                # Set up file
                for font, path in fonts.items():
                    header += f"{font}: {path}\n"
                header+='\n[Events]\nFormat: Start, End, Style, Text\n'
                
                subtitles.write(header)
                
                for subtitle in formatted_subtitles:
                    start_time = subtitle['start']
                    end_time = subtitle['end']
                    text = subtitle['text']
                    
                    # Format the subtitle with custom styling (e.g., fade-in, shadow, border)
                    event_line = f"Dialogue: {start_time},{end_time},S00,{{\\pos({int(video_width/2)},{int(video_height/2)+300})}}{text}\n"
                    
                    # Write the event to the file
                    subtitles.write(event_line)
                
            return subtitles_file

        except Exception as e:
            print(f"Exception: {e}")
    
    
    # def add_subtitles_to_video(self, input_video: str, subtitles_file: str, output_video: str):
    def add_subtitles_to_video(self, input_video: str, subtitles_file: str):
        
        if '.srt' not in subtitles_file:
            raise ValueError("Subtitle file must be in SRT format.")
        
        output_video = os.path.join(settings.TEMP_DIR, f'sibtitles-{uuid4().hex}.mp4')
        
        # Load the input video
        input_stream = ffmpeg.input(input_video)
        
        # Apply the subtitles filter
        video = input_stream.video.filter('subtitles', subtitles_file)
        
        # Combine the video with audio (if any) and output the result
        output = ffmpeg.output(video, input_stream.audio, output_video)
        
        # Run the command
        ffmpeg.run(output)

        return output_video
    
    
    def add_custom_subtitles_to_video(self, input_video: str, subtitles_file: str):
        '''THis function adds a customized subtitle file in ass format to a video'''
        
        if '.ass' not in subtitles_file:
            raise ValueError("Subtitle file must be in ASS format.")
        
        output_video = os.path.join(settings.TEMP_DIR, f'video-{uuid4().hex}.mp4')
        (
            ffmpeg
            .input(input_video)
            .output(output_video, vf=f"ass={subtitles_file}")
            .run(overwrite_output=True)
        )
        
        return output_video
    

    def get_video_details(self, video_file: str):
        '''This function gets comprehensive details about a video and returns them as a dictionary'''
        
        # Probe the video file for metadata
        probe = ffmpeg.probe(video_file)
        
        # Extract the video stream details
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        # Extract the audio stream details
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

        # General file information
        format_info = probe['format']

        # Extracting relevant video details
        video_details = {
            'width': int(video_stream['width']),
            'height': int(video_stream['height']),
            'duration': float(format_info['duration']),
            'bit_rate': int(format_info['bit_rate']),
            'codec': video_stream['codec_name'],
            'codec_long_name': video_stream.get('codec_long_name'),
            'profile': video_stream.get('profile'),
            'pix_fmt': video_stream.get('pix_fmt'),
            'frame_rate': eval(video_stream['r_frame_rate']),  # Converts frame rate to a float
            'bit_depth': video_stream.get('bits_per_raw_sample'),
            'aspect_ratio': video_stream.get('display_aspect_ratio'),
            'avg_frame_rate': eval(video_stream.get('avg_frame_rate', '0/1')),
            'nb_frames': int(video_stream['nb_frames']),
            'tags': video_stream.get('tags', {}),
            'level': video_stream.get('level')
        }

        # Extracting relevant audio details if audio stream is available
        if audio_stream:
            audio_details = {
                'codec': audio_stream['codec_name'],
                'codec_long_name': audio_stream.get('codec_long_name'),
                'channels': int(audio_stream['channels']),
                'channel_layout': audio_stream.get('channel_layout'),
                'sample_rate': int(audio_stream['sample_rate']),
                'bit_rate': audio_stream.get('bit_rate'),
                'duration': float(audio_stream.get('duration', 0)),
                'tags': audio_stream.get('tags', {})
            }
            video_details['audio'] = audio_details
        
        # Add general format info
        video_details.update({
            'format_name': format_info['format_name'],
            'format_long_name': format_info['format_long_name'],
            'file_size': int(format_info['size']),
            'start_time': float(format_info.get('start_time', 0)),
            'bit_rate': int(format_info.get('bit_rate', 0)),
            'duration': float(format_info['duration']),
            'tags': format_info.get('tags', {}),
        })
        
        return video_details

    
    def get_audio_details(self, audio_file: str):
        '''This function gets comprehensive details about an audio file and returns them as a dictionary'''
        
        # Probe the audio file for metadata
        probe = ffmpeg.probe(audio_file)
        
        # Extracting relevant audio stream details
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

        # General file information
        format_info = probe['format']

        # Extracting relevant audio details
        audio_details = {
            'duration': float(format_info['duration']),
            'bit_rate': int(format_info['bit_rate']),
            'codec': audio_stream['codec_name'],
            'codec_long_name': audio_stream.get('codec_long_name'),
            'channels': int(audio_stream['channels']),
            'channel_layout': audio_stream.get('channel_layout'),
            'sample_rate': int(audio_stream['sample_rate']),
            'bit_depth': audio_stream.get('bits_per_raw_sample'),
            'tags': audio_stream.get('tags', {}),
            'file_size': int(format_info['size']),
            'format_name': format_info['format_name'],
            'format_long_name': format_info['format_long_name'],
            'start_time': float(format_info.get('start_time', 0)),
        }

        return audio_details
        

    def set_aspect_ratio(self, aspect_ratio: str):
        if aspect_ratio == 'square':
            return (1000, 1000)
        elif aspect_ratio == 'horizontal':
            return (1920, 1080)
        elif aspect_ratio =='vertical':
            return (720, 1280)
        

    def change_aspect_ratio(self, input_file: str, output_file: str, aspect_ratio: str):
        """
        Change the aspect ratio of a video by resizing and/or adding padding.
        
        :param input_file: Path to the input video file.
        :param output_file: Path to save the output video file.
        :param aspect_ratio: Desired aspect ratio of the video, Can be one of square, horizontal or veritcal.
        """

        aspect_ratio = self.set_aspect_ratio(aspect_ratio)
        # Define the scaling and padding filter
        filter_complex = (
            f"scale={aspect_ratio[0]}:{aspect_ratio[1]}:force_original_aspect_ratio=decrease,"
            f"pad={aspect_ratio[0]}:{aspect_ratio[1]}:(ow-iw)/2:(oh-ih)/2"
        )

        try:
            # Run the ffmpeg command
            ffmpeg.input(input_file).output(output_file, vf=filter_complex).run(overwrite_output=True)
            print(f"Aspect ratio changed. Output saved to {output_file}")

            return output_file
        
        except ffmpeg.Error as e:
            print(f"An error occurred: {e}")


    def add_background_audio(self, video_path: str, audio_path: str):
        try:
            output_path = os.path.join(settings.TEMP_DIR, f'video-{str(uuid4().hex)}.mp4')
            
            # Load the video file with its audio
            video = ffmpeg.input(video_path)

            # Load the background audio and adjust its volume
            background_audio = ffmpeg.input(audio_path).filter('volume', 0.15)

            # Adjust the volume of the original audio from the video
            original_audio = video.audio.filter('volume', 1.0)

            # Combine the original audio with the background audio
            combined_audio = ffmpeg.filter_([original_audio, background_audio], 'amix', inputs=2)

            # Combine the video with the combined audio
            output = ffmpeg.output(
                video.video,                  # Video stream
                combined_audio,               # Combined audio stream
                output_path,                  # Output file path
                vcodec='copy',                # Copy the video codec (no re-encoding)
                acodec='aac',                 # Encode the audio with AAC codec
                strict='experimental',        # Allow use of experimental codecs
                shortest=None                 # Stop the output when the shortest input ends
            )

            # Run the ffmpeg command
            ffmpeg.run(output, overwrite_output=True)

            print(f"Successfully added background audio to {output_path}")

            return output_path

        except ffmpeg.Error as e:
            print(f"Error occurred: {e}")


video_service = GeneralVideoService()
