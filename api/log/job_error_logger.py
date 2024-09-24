import logging

# Configure the logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("job_logs.log"), logging.StreamHandler()],
)

job_error_logger = logging.getLogger(__name__)
