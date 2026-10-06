"""Load the optional application configuration."""

import json
import logging

from app_paths import resource_path

logger = logging.getLogger(__name__)


def load_config(filename="config.json"):
    path = resource_path(filename)
    try:
        with open(path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except FileNotFoundError:
        logger.warning("Configuration file not found at %s; using an empty config", path)
        return {}
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not read configuration file %s", path)
        raise
    logger.info("Loaded configuration from %s", path)
    return config


config = load_config()
