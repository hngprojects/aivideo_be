from typing import Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from api.core.base.services import Service
from api.v1.models.project import Project
from api.v1.schemas.project import (
    CreateProject,
    UpdateProject,
    ToolStatsData,
    ToolStatsResponse,
)
from api.utils.db_validators import check_model_existence
from api.v1.models.user import User


class ProjectService(Service):
    """Project service functionality"""

    def create(self, db: Session, schema: CreateProject):
        """Create a new project"""

        new_project = Project(**schema.model_dump())
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return new_project

    def fetch_all_projects(self, db: Session, **query_params: Optional[Any]):
        """Fetch all projects with option to search using query parameters"""
        query = db.query(Project)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Project, column) and value:
                    query = query.filter(
                        Project.is_active == True,
                        getattr(Project, column).ilike(f"%{value}%"),
                    )

        return query.all()

    def fetch_user_project(self, user: User, project_id: str):
        """Fetch a project by user and project ID."""
        project = next(
            (p for p in user.projects if p.id == project_id and not p.is_deleted), None
        )
        return project

    def fetch(self, db: Session, project_id: str):
        """Fetches a, project by id"""

        project = check_model_existence(db, Project, project_id)
        return project

    def update(self, db: Session, project_id: str, schema: UpdateProject):
        """Updates a project"""

        project = self.fetch(db=db, project_id=project_id)

        # Update the fields with the provided schema data
        update_data = schema.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        db.commit()
        db.refresh(project)
        return project

    def delete(self, db: Session, project_id: str):
        """Deletes a project"""
        project = self.fetch(db=db, project_id=project_id)
        project.is_deleted = True
        db.commit()

    def archive(self, db: Session, project_id: str):
        """Archives anproject"""

        project = self.fetch(db=db, project_id=project_id)
        project.archived = True
        db.commit()

    def fetch_all_user_projects(self, user: User, db: Session):
        all_projects = (
            db.query(Project)
            .filter(
                Project.user_id == user.id,
            )
            .order_by(Project.updated_at.desc())
            .all()
        )

        return all_projects

    def fetch_project_by_id(self, db: Session, project_id: str):
        """Fetches a project by id"""
        return check_model_existence(db, Project, project_id)

    def fetch_all(self, db: Session):
        """Fetch all projects"""
        return db.query(Project).all()

    def add_user_to_project(self, db: Session, project: Project, user: User):
        """Add a user to a project"""
        project.user = user
        db.commit()
        db.refresh(project)
        return project

    def fetch_statistics(self, db: Session):
        """Fetch tool usage statistics"""

        total_projects = db.query(Project).all()
        total_count = len(total_projects)

        pdf_summarizer = sum(
            [
                1
                for project in total_projects
                if project.project_type == "PDF Summarizer"
            ]
        )
        podcast_summarizer = sum(
            [
                1
                for project in total_projects
                if project.project_type == "Podcast Summarizer"
            ]
        )
        youtube_summarizer = sum(
            [
                1
                for project in total_projects
                if project.project_type == "Youtube Summarizer"
            ]
        )
        audio_transcriber = sum(
            [
                1
                for project in total_projects
                if project.project_type == "Audio transcriber"
            ]
        )
        text_to_video = sum(
            [1 for project in total_projects if project.project_type == "Text To Video"]
        )
        image_to_video = sum(
            [1 for project in total_projects if project.project_type == "Talking Head"]
        )
        thumbnail_generator = sum(
            [
                1
                for project in total_projects
                if project.project_type == "Video Thumbnail Generator"
            ]
        )

        if total_count:
            pdf_summarizer_percentage = (pdf_summarizer / total_count) * 100
            podcast_summarizer_percentage = (podcast_summarizer / total_count) * 100
            youtube_summarizer_percentage = (youtube_summarizer / total_count) * 100
            audio_transcriber_percentage = (audio_transcriber / total_count) * 100
            text_to_video_percentage = (text_to_video / total_count) * 100
            image_to_video_percentage = (image_to_video / total_count) * 100
            thumbnail_generator_percentage = (thumbnail_generator / total_count) * 100

            return ToolStatsResponse(
                status="success",
                status_code=200,
                message="Tool Usage data successfully retrieved!",
                data=ToolStatsData(
                    pdf_summarizer=pdf_summarizer_percentage,
                    podcast_summarizer=podcast_summarizer_percentage,
                    audio_transcriber=audio_transcriber_percentage,
                    text_to_video=text_to_video_percentage,
                    image_to_video=image_to_video_percentage,
                    thumbnail_generator=thumbnail_generator_percentage,
                    youtube_summarizer=youtube_summarizer_percentage,
                ),
            )

        return ToolStatsResponse(
            status="success",
            status_code=200,
            message="No Tool Usage data recorded!",
            data=ToolStatsData(
                pdf_summarizer=0,
                podcast_summarizer=0,
                audio_transcriber=0,
                text_to_video=0,
                image_to_video=0,
                thumbnail_generator=0,
                youtube_summarizer=0,
            ),
        )

    def fetch_user_projects_by_keywords(self, db: Session, user: User, keywords: str):
        query = db.query(Project).filter(
            and_(
                Project.user_id == user.id,
                or_(
                    Project.title.ilike(f"%{keywords}%"),
                    Project.description.ilike(f"%{keywords}%"),
                    Project.project_type.ilike(f"%{keywords}%"),
                ),
            )
        )

        # Order from newest to oldest
        project_search_results = query.order_by(Project.updated_at.desc()).all()

        return project_search_results


project_service = ProjectService()
