import logging
import logging.handlers
import sys


def setup_logger(name: str = "AppLogger") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-10s | "
            "%(module)-10s | %(lineno)-5d | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    file_handler = logging.handlers.RotatingFileHandler(
        filename="app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
