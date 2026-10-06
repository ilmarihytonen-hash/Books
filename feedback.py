"""Open the feedback destination configured for this application."""

import logging

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox, QWidget

from configreader import load_config
from i18n import translate

logger = logging.getLogger(__name__)


def is_valid_feedback_destination(destination):
    if not destination:
        return True
    if not isinstance(destination, str):
        return False
    url = QUrl(destination.strip())
    return url.scheme() == "mailto" or (
        url.scheme() == "https" and bool(url.host())
    )


def feedback_label(language):
    try:
        config = load_config()
    except Exception:
        logger.exception("Could not read feedback button configuration")
        return translate(language, "feedback")
    label = config.get("feedback_label")
    return label.strip() if isinstance(label, str) and label.strip() else translate(
        language, "feedback"
    )


def open_feedback(parent: QWidget, language):
    try:
        config = load_config()
    except Exception as error:
        logger.exception("Could not read feedback configuration")
        QMessageBox.critical(
            parent,
            translate(language, "feedback"),
            translate(language, "feedback_config_failed", error=error),
        )
        return
    destination = config.get("feedback_url", "")
    if not isinstance(destination, str) or not destination.strip():
        QMessageBox.information(
            parent,
            translate(language, "feedback"),
            translate(language, "feedback_not_configured"),
        )
        return

    url = QUrl(destination.strip())
    if not is_valid_feedback_destination(destination):
        QMessageBox.critical(
            parent,
            translate(language, "feedback"),
            translate(language, "feedback_invalid"),
        )
        return

    if not QDesktopServices.openUrl(url):
        QMessageBox.warning(
            parent,
            translate(language, "feedback"),
            translate(language, "feedback_open_failed"),
        )
