from api.v1.models.project import ProjectToolsEnum as tools


BASE_DIR = 'api/core/dependencies/job_runner/tasks'
# BASE_DIR = 'tasks'  # for uvicorn

# Mapping between script names and their corresponding tools
# This is basically to register task scripts
tool_to_script_mapping = {
    tools.talking_avatar.value: f'{BASE_DIR}/talking_avatar.py',
    tools.script_to_video.value: f'{BASE_DIR}/script_to_video.py',
    tools.image_to_video.value: f'{BASE_DIR}/image_to_video.py',
    tools.podcast_summarizer.value: f'{BASE_DIR}/podcast_summarizer.py',
    tools.youtube_summarizer.value: f'{BASE_DIR}/youtube_summarizer.py',
    tools.video_summarizer.value: f'{BASE_DIR}/video_summarizer.py',
    tools.pdf_summarizer.value: f'{BASE_DIR}/pdf_summarizer.py',
}
