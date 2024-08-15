from typing import Any, Optional
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.resource import Resource
from api.v1.schemas.resource import CreateResource, UpdateResource
from api.utils.db_validators import check_model_existence
from fastapi import HTTPException


class ResourceService(Service):
    """Resource service functionality"""

    def create(self, db: Session, schema: CreateResource) -> Resource:
        """Create a new Resource

        Returns:
            (Resource): Resource object.
        """
        if (
            schema.title.strip() == ""
            or schema.image_url.strip() == ""
            or schema.content.strip() == ""
        ):
            raise HTTPException(status_code=400, detail="Invalid request body")

        new_resource = Resource(**schema.model_dump())
        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        return new_resource

    def fetch_all(self, db: Session, **query_params: Optional[Any]) -> list:
        """Fetch all Resources with option to search using query parameters

        Returns:
            (list): A list of all Resource objects present in the database
        """
        query = db.query(Resource)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Resource, column) and value:
                    query = query.filter(getattr(Resource, column).ilike(f"%{value}%"))

        return query.all()

    def fetch(self, db: Session, id):
        """Fetches a resource by their id"""

        resource = check_model_existence(db, Resource, id)

        # return resource if resource is not deleted
        if not resource.is_deleted:
            return resource

    def get_resource_by_id(self, db: Session, id: str):
        """Fetches a resource by their id"""

        resource = check_model_existence(db, Resource, id)
        return resource

    def update(
        self, db: Session, resource_id: str, schema: UpdateResource
    ) -> Resource | None:
        """Updates an Resource

        Args:
            db (Session): db Session object
            Resource_id (str)
            schema (UpdateResource): Pydantic schema object

        Returns:
            Resource
        """
        resource = self.fetch(db=db, id=resource_id)
        if not resource:
            return None

        # Update the fields with the provided schema data
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(resource, key, value)

        db.commit()
        db.refresh(resource)
        return resource

    def delete(self, db: Session, Resource_id: str) -> bool:
        """Deletes an Resource

        Args:
            db (Session)
            Resource_id (str)

        Returns:
            bool: True if Resource object is found else False
        """
        resource = check_model_existence(db, Resource, id)

        resource.is_deleted = True
        db.commit()

        return super().delete()


resource_service = ResourceService()
