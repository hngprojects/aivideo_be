# import ffmpeg

# def add_background_audio(video_path: str, audio_path: str, output_path: str, video_audio_volume: float = 1.0):
#     try:
#         # Load the video file with its audio
#         video = ffmpeg.input(video_path)

#         # Load the background audio and adjust its volume
#         background_audio = ffmpeg.input(audio_path).filter('volume', 0.2)

#         # Adjust the volume of the original audio from the video
#         original_audio = video.audio.filter('volume', video_audio_volume)

#         # Combine the original audio with the background audio
#         combined_audio = ffmpeg.filter_([original_audio, background_audio], 'amix', inputs=2)

#         # Combine the video with the combined audio
#         output = ffmpeg.output(
#             video.video,                  # Video stream
#             combined_audio,               # Combined audio stream
#             output_path,                  # Output file path
#             vcodec='copy',                # Copy the video codec (no re-encoding)
#             acodec='aac',                 # Encode the audio with AAC codec
#             strict='experimental',        # Allow use of experimental codecs
#             shortest=None                 # Stop the output when the shortest input ends
#         )

#         # Run the ffmpeg command
#         ffmpeg.run(output, overwrite_output=True)

#         print(f"Successfully added background audio to {output_path}")

#     except ffmpeg.Error as e:
#         print(f"Error occurred: {e.stderr.decode()}")

# # Usage
# video_path = './scripts/test-vid.mp4'
# audio_path = './scripts/test-audio.mp3'
# output_path = './test-output.mp4'

# add_background_audio(video_path, audio_path, output_path)



# # python3 api/core/dependencies/jobs/tasks/talking_avatar.py '{"image_file": "presets/avatars/avatar-32d49deff3.png", "audio_file": null, "aspect_ratio": "square", "script": "I am just testing please. Just work abeg. Let us see what happens from here on out", "voice_over": "man"}'



from api.utils.minio_service import minio_service

minio_service.download_file_from_minio(
    'https://media.tifi.tv/text-to-video/ttvid-02b81068-c5c2-4b38-b540-4f68f22576b2.mp4',
)