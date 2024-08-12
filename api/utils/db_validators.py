from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from api.v1.models import User


def check_model_existence(db: Session, model, id):
    """Checks if a model exists by its id"""

    # obj = db.query(model).filter(model.id == id).first()
    obj = db.get(model, ident=id)

    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} does not exist")

    return obj
