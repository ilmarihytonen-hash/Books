"""Load locale dictionaries and provide translated UI strings."""

import json
import logging
import os
from functools import lru_cache

from app_paths import resource_path

logger = logging.getLogger(__name__)
LANGUAGE_NAMES = {"en": "English", "fi": "Suomi", "sv": "Svenska"}


@lru_cache(maxsize=len(LANGUAGE_NAMES))
def _load_language(language):
    if language not in LANGUAGE_NAMES:
        language = "en"
    path = resource_path(os.path.join("languages", f"{language}.json"))
    try:
        with open(path, "r", encoding="utf-8") as file:
            translations = json.load(file)
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not load language file %s", path)
        raise
    if not isinstance(translations, dict):
        raise ValueError(f"Language file {path} must contain a JSON object")
    return translations


def translate(language, key, **values):
    """Return a translated string, falling back to English for missing entries."""
    translations = _load_language(language)
    template = translations.get(key)
    if template is None:
        template = _load_language("en").get(key, key)
    return template.format(**values)
