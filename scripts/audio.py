import ffmpeg

def add_background_audio(video_path: str, audio_path: str, output_path: str, audio_volume: float = 0.7):
    # Adjust the volume of the background audio
    background_audio = ffmpeg.input(audio_path).filter('volume', audio_volume)

    # Combine the original video with the background audio
    video = ffmpeg.input(video_path)
    video_with_audio = ffmpeg.output(
        video, 
        background_audio, 
        output_path, 
        vcodec='copy', 
        acodec='aac', 
        strict='experimental'
    )

    # Run the ffmpeg command
    ffmpeg.run(video_with_audio)

# Usage
video_path = './test-vid.mp4'
audio_path = './test-audio.mp3'
output_path = './output.mp4'

add_background_audio(video_path, audio_path, output_path)
