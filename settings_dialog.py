"""Editable browser and password-saving preferences."""

import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QSlider,
    QVBoxLayout,
)

from configreader import load_config, save_config
from credential_store import clear_logins
from i18n import LANGUAGE_NAMES, translate
from saver import add_url, get_all_urls, normalize_url, set_language

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, language, parent=None):
        super().__init__(parent)
        self.language = language if language in LANGUAGE_NAMES else "en"
        self.config = load_config()
        self.setWindowTitle(translate(self.language, "settings"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.language_combo = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self.language_combo.addItem(name, code)
        index = self.language_combo.findData(self.language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        form.addRow(translate(self.language, "language"), self.language_combo)

        self.home_url_combo = QComboBox()
        self.home_url_combo.addItem(
            translate(self.language, "settings_use_selected_url"), ""
        )
        saved_urls = get_all_urls()
        configured_home = self.config.get("home_url", "")
        if not isinstance(configured_home, str):
            configured_home = ""
        if configured_home and configured_home not in saved_urls:
            saved_urls.append(configured_home)
        for url in saved_urls:
            self.home_url_combo.addItem(url, url)
        selected_home = self.home_url_combo.findData(configured_home)
        self.home_url_combo.setCurrentIndex(max(selected_home, 0))
        form.addRow(
            translate(self.language, "settings_home_url"), self.home_url_combo
        )

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 150)
        self.zoom_slider.setSingleStep(10)
        self.zoom_slider.setPageStep(10)
        self.zoom_slider.setTickInterval(10)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setValue(
            self._configured_zoom(self.config.get("browser_zoom", 100))
        )
        self.zoom_value = QLabel()
        self.zoom_slider.valueChanged.connect(
            lambda value: self.zoom_value.setText(f"{value}%")
        )
        self.zoom_value.setText(f"{self.zoom_slider.value()}%")
        zoom_row = QVBoxLayout()
        zoom_row.addWidget(self.zoom_slider)
        zoom_row.addWidget(self.zoom_value)
        form.addRow(translate(self.language, "settings_zoom"), zoom_row)

        self.password_saving_checkbox = QCheckBox(
            translate(self.language, "settings_password_saving_description")
        )
        self.password_saving_supported = sys.platform == "win32"
        self.password_saving_checkbox.setChecked(
            self.password_saving_supported
            and self.config.get("password_saving_enabled", True) is True
        )
        self.password_saving_checkbox.setEnabled(
            self.password_saving_supported
        )
        if not self.password_saving_supported:
            self.password_saving_checkbox.setToolTip(
                translate(
                    self.language, "settings_password_saving_unavailable"
                )
            )
        form.addRow(
            translate(self.language, "settings_password_saving"),
            self.password_saving_checkbox,
        )

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addLayout(form)
        layout.addWidget(self.status_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _configured_zoom(value):
        try:
            zoom = int(value)
        except (TypeError, ValueError):
            return 100
        return max(50, min(150, round(zoom / 10) * 10))

    def _save(self):
        password_saving_enabled = (
            self.password_saving_checkbox.isChecked()
            if self.password_saving_supported
            else self.config.get("password_saving_enabled", True) is True
        )
        if (
            self.password_saving_supported
            and self.config.get("password_saving_enabled", True) is True
            and not password_saving_enabled
        ):
            answer = QMessageBox.question(
                self,
                translate(self.language, "settings_password_saving"),
                translate(
                    self.language, "settings_password_saving_disable_confirm"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.password_saving_checkbox.setChecked(True)
                return

        home_url = self.home_url_combo.currentData()
        if not home_url:
            home_url = ""
        if home_url:
            normalized_home_url = normalize_url(home_url)
            if not normalized_home_url:
                self.status_label.setText(
                    translate(self.language, "settings_invalid_home_url")
                )
                return
            home_url = normalized_home_url

        updated_config = dict(self.config)
        updated_config["home_url"] = home_url
        updated_config["browser_zoom"] = self.zoom_slider.value()
        if self.password_saving_supported:
            updated_config["password_saving_enabled"] = password_saving_enabled

        try:
            if home_url and home_url not in get_all_urls():
                add_url(home_url)
            save_config(updated_config)
            if self.password_saving_supported and not password_saving_enabled:
                clear_logins()
            set_language(self.language_combo.currentData())
        except Exception as error:
            logger.exception("Could not save application settings")
            QMessageBox.critical(
                self,
                translate(self.language, "settings"),
                translate(self.language, "settings_save_failed", error=error),
            )
            return

        self.config = updated_config
        self.accept()
