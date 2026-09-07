import logging
import os
from logging.handlers import RotatingFileHandler

try:
    from config.config_manager import config
    LOG_LEVEL = config.get_setting("LOG_LEVEL", "INFO")
except Exception:
    LOG_LEVEL = "INFO"

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "jaguar.log")

logger = logging.getLogger("Jaguar")

if not logger.handlers:

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)


class JaguarLogger:

    def __init__(self, name="Jaguar"):
        self.logger = logging.getLogger(name)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)


logger = JaguarLogger()
