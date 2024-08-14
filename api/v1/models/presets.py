from sqlalchemy import Column, String
from api.v1.models.base_model import BaseTableModel


class Avatar(BaseTableModel):
    __tablename__ = "avatars"

    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)


class BackgroundMusic(BaseTableModel):
    __tablename__ = "background_music"

    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)

