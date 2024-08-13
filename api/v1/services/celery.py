from typing import Optional
from fastapi import HTTPException

from api.db.database import get_db
from api.v1.models.celery import CeleryTask


db = next(get_db())

class CeleryTaskService:
    '''This is for celery tasks db operations'''

    def create_task(self, task_id: str, project_id: str):
        '''Creates a new celery task'''

        task = CeleryTask(
            task_id=task_id, 
            project_id=project_id, 
            status='RUNNING'
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    
    def fetch_by_task_id(self, task_id: str):
        '''Fetches the task details from the database'''

        task = db.query(CeleryTask).filter(CeleryTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail='Celery task not found')
        return task


    def update_task(self, task_id: str, status: str, result: Optional[str] = None):
        '''Updates the task details'''

        task = self.fetch_by_task_id(task_id=task_id)

        task.status = status
        task.result = result if result is not None else None
        db.commit()
        return task


celery_service = CeleryTaskService()
