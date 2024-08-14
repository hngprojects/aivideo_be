from typing import Any, Optional
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.project import Project
from api.v1.schemas.project import CreateProject, UpdateProject
from api.utils.db_validators import check_model_existence
from api.v1.models.user import User


class ProjectService(Service):
    '''Project service functionality'''

    def create(self, db: Session, schema: CreateProject):
        """Create a new project"""

        new_project = Project(**schema.model_dump())
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return new_project

    def fetch_all(self, db: Session, **query_params: Optional[Any]):
        """Fetch all projects with option to search using query parameters"""

        query = db.query(Project)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Project, column) and value:
                    query = query.filter(getattr(Project, column).ilike(f"%{value}%"))

        return query.all()

    def fetch(self, db: Session, project_id: str):
        """Fetches a, project by id"""

        prohect = check_model_existence(db, Project, project_id)
        return prohect

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

    def fetch_all_user_projects(self, user: User):
        all_projects = user.projects

        return all_projects
    
    def fetch_user_project(self, user: User, project_id: str):
        all_user_projects = user.projects

        for project in all_user_projects:
            if str(project.id) == project_id:
                return project
        
        return None
    

project_service = ProjectService()