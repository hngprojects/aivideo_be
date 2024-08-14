from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.project import project_service

project_router = APIRouter(prefix="/projects", tags=["Projects"])


@project_router.get("/", status_code=200)
async def get_all_projects(db: Session = Depends(get_db)):
    """Endpoint to fetch all projects"""
    projects = project_service.fetch_all(db)
    return projects


@project_router.get("/{project_id}", status_code=200)
async def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    """Endpoint to fetch a project by its ID"""
    project = project_service.fetch(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
