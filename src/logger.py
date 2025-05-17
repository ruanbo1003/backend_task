import logging
import os
import json
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")


class JsonLineFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": getattr(record, "custom_module", "unknown"),
            "message": getattr(record, "json_message", {"raw": record.getMessage()})
        }
        return json.dumps(log_record)

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)


def log_info(module: str, message):
    record = logging.LogRecord(
        name=module,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",  # not used
        args=(),
        exc_info=None
    )
    record.custom_module = module
    record.json_message = message if isinstance(message, dict) else {"info": message}
    logging.getLogger().handle(record)

def log_error(module: str, message):
    record = logging.LogRecord(
        name=module,
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None
    )
    record.custom_module = module
    record.json_message = message if isinstance(message, dict) else {"info": message}
    logging.getLogger().handle(record)


setup_logging()
