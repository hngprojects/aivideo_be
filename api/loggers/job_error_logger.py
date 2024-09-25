import logging

# Configure the logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/job_logs.log"), logging.StreamHandler()],
)

job_error_logger = logging.getLogger(__name__)
