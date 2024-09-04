from fastapi import BackgroundTasks

from api.v1.models.user import User
from api.core.dependencies.email.email_sender import send_email


class EmailSendingService:
    """
    This service just allows for sending different types of email messages
    """

    def send_welcome_email(self, background_tasks: BackgroundTasks, user: User):
        '''Thiss function sends the welcome email to a user'''

        background_tasks.add_task(
        send_email,
        recipient=user.email,
        template_name="welcome.html",
        subject="Welcome to TiFi",
        context={
            "first_name": user.first_name, 
            "last_name": user.last_name, 
            "cta_link": "https://tifi.tv/about"
        }
    )


email_sending_service = EmailSendingService()