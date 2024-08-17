from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from api.v1.models.base_model import BaseTableModel


class TextToVideo(BaseTableModel):
    """
    Represents TextToVideo table in the database
    """
    __tablename__ = "text_to_vdeos"

    user_id: Mapped[str] = mapped_column(String,
                                         ForeignKey("users.id",
                                                    ondelete="CASCADE"),
                                         nullable=True)
    task_id: Mapped[str] = mapped_column(String, nullable=True)
    job_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, server_default='Task is in queue')
    video_url: Mapped[str] = mapped_column(String, nullable=True)
    gif_url: Mapped[str] = mapped_column(String, nullable=True)
   
    user = relationship("User", back_populates="text_to_vdeos")
