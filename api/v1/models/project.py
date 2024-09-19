from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from enum import Enum

from api.v1.models.base_model import BaseTableModel


class ProjectToolsEnum(str, Enum):
    # AI TOOLS
    youtube_summarizer = "Youtube Summarizer"
    video_summarizer = "Video Summarizer"
    script_to_video = "Script To Video"
    talking_avatar = "Talking Avatar"
    audio_transcriber = "Audio Transcriber"
    audio_summarizer = "Audio Summarizer"
    image_to_video = "Image To Video"
    podcast_summarizer = "Podcast Summarizer"
    thumbnail_generator = "Thumbnail Generator"
    pdf_summarizer = "PDF Summarizer"
    subtitle_translator = "Subtitle Translator"

    # FFMPEG TOOLS
    audio_extractor = 'Audio Extractor'
    resize_video = 'Resize Video'
    video_compressor = 'Video Compressor'


class Project(BaseTableModel):
    __tablename__ = 'projects'

    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    project_type = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    archived = Column(Boolean, server_default='false')
    is_deleted = Column(Boolean, server_default='false')
    is_active = Column(Boolean, server_default='false')
    archived_at = Column(DateTime, nullable=True)
    thumbnail = Column(String, nullable=True)
    
    user = relationship('User', back_populates='projects')
    # tifi_job = relationship("TifiJob", back_populates="project", uselist=False)
    job = relationship("Job", back_populates="project", uselist=False)
