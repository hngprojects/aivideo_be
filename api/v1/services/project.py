import json
from typing import Any, Optional
from datetime import datetime

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
from api.v1.schemas.project import ProjectToolsEnum


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

    def archive_project(self, db: Session, project_id: str):
        """Archives a project"""

        project = self.fetch(db=db, project_id=project_id)
        project.archived = True
        project.archived_at=datetime.now()
        db.commit()

    def fetch_all_user_projects(self, user: User, db: Session):
        all_projects = db.query(Project).filter(
            Project.user_id == user.id,
            Project.is_active == True,
            Project.archived == False,
            Project.is_deleted == False,
        ).order_by(
            Project.updated_at.desc()
        ).all()
        
        return all_projects
    
    def fetch_all_user_archived_projects(self, user: User, db: Session):
        all_projects = db.query(Project).filter(
            Project.user_id == user.id,
            Project.is_active == True,
            Project.archived == True,
            Project.is_deleted == False,
        ).order_by(
            Project.updated_at.desc()
        ).all()

        return all_projects

    def fetch_project_by_id(self, db: Session, project_id: str):
        """Fetches a project by id"""

        return check_model_existence(db, Project, project_id)

    def fetch_all(self, db: Session):
        """Fetch all projects"""

        return db.query(Project).all()

    def save_project(self, db: Session, project: Project, user: User, project_result: str):
        """Add a user to a project"""

        project.user_id = user.id
        project.result = project_result
        db.commit()
        return project

    def fetch_statistics(self, db: Session):
        """Fetch tool usage statistics"""

        total_projects = db.query(Project).all()
        total_count = len(total_projects)

        all_project_count_dict = {}

        # Dict should look like {"podcast_summarizer": 2, ...} once iteration completes
        # Code can further be optimized to use single for-loop to count as well as calculate percentages
        for p in total_projects:
            # Map Enum value stored in db to Enum's name, for use as key in the `all_project_count_dict`
            # Catch errors that would occur when an unknown project_type is encountered
            try:
                project_type_name = ProjectToolsEnum(p.project_type).name
            except ValueError:
                continue

            # Increment count for each tool if already present in all_project_count_dict else intialise it to 1
            prev_count_value = all_project_count_dict.get(project_type_name)
            all_project_count_dict[project_type_name] = 1 if prev_count_value is None else prev_count_value + 1


        if total_count:
            return ToolStatsResponse(
                status="success",
                status_code=200,
                message="Tool Usage data successfully retrieved!",
                data=ToolStatsData(
                    **all_project_count_dict,
                ),
            )

        return ToolStatsResponse(
            status="success",
            status_code=200,
            message="No Tool Usage data recorded!",
            data=ToolStatsData(),       # Default values will be used
        )

    def fetch_user_projects_by_keywords(self, db: Session, user: User, keywords: str):
        query = db.query(Project).filter(
            and_(
                Project.user_id == user.id,
                Project.is_active == True,
                Project.archived == False,
                Project.is_deleted == False,
                or_(
                    Project.title.ilike(f"%{keywords}%"),
                    Project.description.ilike(f"%{keywords}%"),
                    Project.project_type.ilike(f"%{keywords}%"),
                ),
            )
        )

        # Order from newest to oldest
        project_search_results = query.order_by(
            Project.updated_at.desc()
        ).all()
        
        project_search_results = query.order_by(Project.updated_at.desc()).all()

        return project_search_results
    
    def update_project_status(
        self, 
        db: Session, 
        project_id: str, 
        is_active: bool, 
        result,
        user: Optional[User] = None
    ):
        '''Update project status'''

        project = check_model_existence(db, Project, project_id)

        project.is_active = is_active
        # print(project.is_active)

        project.result = result
        # print(project.result)

        if user:
            project.user_id = user.id
            # print('user is set')

        db.commit()



project_service = ProjectService()
