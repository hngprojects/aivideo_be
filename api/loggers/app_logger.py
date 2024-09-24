import logging

# Configure the logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app_logs.log"), logging.StreamHandler()],
)

error_logger = logging.getLogger(__name__)
