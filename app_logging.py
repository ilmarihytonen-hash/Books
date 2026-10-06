"""Linux-style console and file logging for the application."""

import logging
import os
import sys

from app_paths import writable_path


def configure_logging():
    log_dir = writable_path("logs")
    os.makedirs(log_dir, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", None)
        == os.path.abspath(os.path.join(log_dir, "bookapp.log"))
        for handler in root.handlers
    ):
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "bookapp.log"), encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    if sys.stdout is not None and not any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in root.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)
