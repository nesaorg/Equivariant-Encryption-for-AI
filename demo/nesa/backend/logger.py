import logging
from logging.handlers import RotatingFileHandler
import os
import sys

MAX_LINES = int(os.getenv("LOG_MAX_LINES", 20000))

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

log_file_path = os.path.join(log_dir, "web-ui.log")


def setup_logger(name: str = "web_ui_logger") -> logging.Logger:
    """
    set up a logger that writes to a single rotating file and captures stdout.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file_path, mode="a", maxBytes=MAX_LINES * 100, backupCount=0
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


logger = setup_logger()