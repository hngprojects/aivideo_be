import json, sys, os
from uuid import uuid4

from api.db.database import get_db
from api.v1.services.job import tifi_job_service
from api.utils.files import delete_file
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils import mime_types
from api.v1.services.ai_tools.article_translator import article_translator_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

article = payload.get('article')
languages = payload.get('languages')
names = payload.get('names')

number_to_process = len(languages)
progress_per_article = round(95 / number_to_process)

articles = []

try:
    for i in range(len(languages)):
        translated_article = article_translator_service.generate_translated_article(
            article=article,
            language=languages[i],
            name=names[i]
        )

        # TODO: Might add pdf functionality

        articles.append({
            'language': languages[i],
            'translated_article': translated_article
        })

        save_and_print_job_progress(
            db, 
            job, 
            progress = (i+1) * progress_per_article, 
            progress_info = f'{languages[i]} article generated. {number_to_process-i} remaining'
        )
    
    print(json.dumps(articles))

except Exception as e:
    raise e
