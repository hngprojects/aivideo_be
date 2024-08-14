import csv
from io import StringIO
from api.core.base.services import Service
from sqlalchemy.orm import Session
from api.v1.models.project import Project
from api.utils.pagination import paginated_response


class JobManagementService(Service):
    def create(self):
        return super().create()

    def update(self):
        return super().update()

    def delete(self):
        return super().delete()

    def fetch(self):
        return super().fetch()

    def fetch_all(self):
        return super().fetch_all()

    def fetch_all_summarized_videos(self, db: Session, skip: int, limit: int, filters):
        return paginated_response(
            db=db,
            model=Project,
            skip=skip,
            limit=limit,
            filters=filters,
            related_models=[Project.user],
            related_model_excludes={
                "user": [
                    "password",
                    "is_superadmin",
                    "is_deleted",
                    "created_at",
                    "update_at",
                    "avatar_url",
                    "is_active",
                ]
            },
        )

    def export_jobs_as_csv(self, db: Session):
        # get videos

        videos = db.query(Project).all()

        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)

        csv_writer.writerow(
            [
                "ID",
                "Firstname",
                "Lastname",
                "Email",
                "Title",
                "Description",
                "Project Type",
                "Duration",
                "Size",
                "Status",
            ]
        )

        for video in videos:
            csv_writer.writerow(
                [
                    video.id,
                    video.user.first_name,
                    video.user.last_name,
                    video.user.email,
                    video.title,
                    video.description,
                    video.project_type,
                    video.duration,
                    video.size,
                    video.status.value,
                ]
            )

        csv_file.seek(0)

        return csv_file


job_management_service = JobManagementService()
