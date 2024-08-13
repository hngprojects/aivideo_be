from sqlalchemy import create_engine
from celery.backends.database.models import Task, TaskSet
from celery.backends.database.session import ResultModelBase

from api.utils.settings import settings

db_url = f"{settings.DB_URL}"

engine = create_engine(db_url)


def setup_celery_results_db():
    """Create engine and create tables for celery results backend."""
    ResultModelBase.metadata.create_all(engine)
    print("Celery result backend tables created successfully.")


if __name__ == "__main__":
    setup_celery_results_db()