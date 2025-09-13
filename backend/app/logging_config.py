
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """
    Configure structured JSON logging for the application's root logger.

    This function is idempotent, meaning it won't add duplicate handlers
    if it's called multiple times.
    """
    logger = logging.getLogger()
    
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    
    return logger
logger = setup_logging()