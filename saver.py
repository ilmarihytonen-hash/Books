"""Read and write the persisted URL and language settings."""

import logging
import os
from urllib.parse import urlsplit

import yaml

from app_paths import migrate_legacy_file, resource_path, writable_path

logger = logging.getLogger(__name__)
FILENAME = writable_path("urls.yaml")
DEFAULT_DATA = {"title": "Bookapp", "language": "en", "urls": []}


def normalize_url(url):
    value = url.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or not hostname
        or any(character.isspace() for character in parsed.netloc)
    ):
        return None
    return value


def load_data():
    migrate_legacy_file("urls.yaml")
    if not os.path.exists(FILENAME):
        bundled_urls = resource_path("urls.yaml")
        source = bundled_urls if os.path.exists(bundled_urls) else None
        if source and os.path.abspath(source) != os.path.abspath(FILENAME):
            with open(source, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
            if isinstance(data, dict):
                data.setdefault("language", "en")
                data.setdefault("urls", [])
                save_data(data)
                return data
        save_data(DEFAULT_DATA.copy())
        return DEFAULT_DATA.copy()

    with open(FILENAME, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        data = DEFAULT_DATA.copy()
    if not isinstance(data, dict):
        raise ValueError("urls.yaml must contain a YAML mapping")
    urls = data.get("urls", [])
    if not isinstance(urls, list) or not all(isinstance(url, str) for url in urls):
        raise ValueError("the 'urls' setting in urls.yaml must be a list of strings")
    data["urls"] = urls
    if data.get("language") not in ("en", "fi", "sv"):
        data["language"] = "en"
    return data


def save_data(data):
    os.makedirs(os.path.dirname(FILENAME), exist_ok=True)
    with open(FILENAME, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)
    logger.info("Saved application settings to %s", FILENAME)


def add_url(new_url):
    normalized_url = normalize_url(new_url)
    if normalized_url is None:
        return False
    data = load_data()
    if normalized_url in data["urls"]:
        return False
    data["urls"].append(normalized_url)
    save_data(data)
    logger.info("Added saved website: %s", normalized_url)
    return True


def remove_url(url_to_remove):
    data = load_data()
    if url_to_remove not in data["urls"]:
        return False
    data["urls"].remove(url_to_remove)
    save_data(data)
    logger.info("Removed saved website: %s", url_to_remove)
    return True


def get_all_urls():
    return load_data()["urls"]


def get_language():
    return load_data().get("language", "en")


def set_language(language):
    if language not in ("en", "fi", "sv"):
        raise ValueError("language must be one of: en, fi, sv")
    data = load_data()
    data["language"] = language
    save_data(data)
    logger.info("Language set to %s", language)
