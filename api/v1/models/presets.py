from sqlalchemy import Column, String, Enum
from api.v1.models.base_model import BaseTableModel


class Avatar(BaseTableModel):
    __tablename__ = "avatars"

    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    gender = Column(
        String,
        nullable=False,
        server_default='neutral'
    )
    # voice = Column(String, nullable=False)

class BackgroundMusic(BaseTableModel):
    __tablename__ = "background_music"

    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
