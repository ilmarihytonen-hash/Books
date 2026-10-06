"""Application menu for selecting a website, language, and exam mode."""

import logging
import sys

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_logging import configure_logging
from app_theme import apply_app_theme
from i18n import LANGUAGE_NAMES, translate
from saver import add_url, get_all_urls, get_language, normalize_url, set_language
from webengine import ModernApp

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, language=None):
        super().__init__()
        try:
            self.language = language or get_language()
            self.urls = get_all_urls()
        except Exception as error:
            logger.exception("Could not load application settings")
            self.language = "en"
            self.urls = []
            QMessageBox.critical(
                self, "Bookapp", translate("en", "load_failed", error=error)
            )

        self.setMinimumSize(480, 440)
        self.setWindowTitle(translate(self.language, "app_title"))
        self.browser_window = None
        self._create_ui()
        self._refresh_text()
        self._populate_urls()

    def _create_ui(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(16)

        brand = QLabel()
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)
        self.brand_label = brand

        self.url_label = QLabel()
        layout.addWidget(self.url_label)
        self.url_list = QListWidget()
        self.url_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self.url_list.setMinimumHeight(110)
        self.url_list.setMaximumHeight(160)
        layout.addWidget(self.url_list)

        self.new_url_input = QLineEdit()
        layout.addWidget(self.new_url_input)
        self.save_button = QPushButton()
        self.save_button.clicked.connect(self._save_url)
        layout.addWidget(self.save_button)

        options = QHBoxLayout()
        self.language_label = QLabel()
        options.addWidget(self.language_label)
        self.language_combo = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        language_index = self.language_combo.findData(self.language)
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)
        options.addWidget(self.language_combo)
        options.addStretch()
        layout.addLayout(options)

        self.exam_checkbox = QCheckBox()
        layout.addWidget(self.exam_checkbox)
        self.launch_button = QPushButton()
        self.launch_button.setMinimumHeight(48)
        self.launch_button.clicked.connect(self._launch_browser)
        layout.addWidget(self.launch_button)
        layout.addStretch()

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a6adc8;")
        layout.addWidget(self.status_label)
        self.setCentralWidget(content)

    def _refresh_text(self):
        t = lambda key: translate(self.language, key)
        self.setWindowTitle(t("app_title"))
        self.brand_label.setText(t("brand_title"))
        self.url_label.setText(t("choose_url"))
        self.new_url_input.setPlaceholderText(t("new_url"))
        self.save_button.setText(t("save_url"))
        self.language_label.setText(t("language"))
        self.exam_checkbox.setText(t("exam_mode"))
        self.launch_button.setText(t("launch_browser"))

    def _populate_urls(self, selected=None):
        self.url_list.clear()
        self.url_list.addItems(self.urls)
        if selected:
            matches = self.url_list.findItems(
                selected, Qt.MatchFlag.MatchExactly
            )
            if matches:
                self.url_list.setCurrentItem(matches[0])
        elif self.url_list.count():
            self.url_list.setCurrentRow(0)

    def _language_changed(self, index):
        code = self.language_combo.itemData(index)
        if not code or code == self.language:
            return
        self.language = code
        try:
            set_language(code)
        except Exception:
            logger.exception("Could not save language preference")
        self._refresh_text()

    def _save_url(self):
        value = self.new_url_input.text().strip()
        normalized_url = normalize_url(value)
        if not normalized_url:
            self.status_label.setText(translate(self.language, "url_invalid"))
            return
        try:
            if add_url(normalized_url):
                self.urls = get_all_urls()
                self._populate_urls(normalized_url)
                self.new_url_input.clear()
                self.status_label.setText(translate(self.language, "url_saved"))
            else:
                self.status_label.setText(translate(self.language, "url_exists"))
        except Exception as error:
            logger.exception("Could not save URL")
            QMessageBox.critical(
                self,
                translate(self.language, "app_title"),
                translate(self.language, "url_save_failed", error=error),
            )

    def _launch_browser(self):
        selected_item = self.url_list.currentItem()
        selected_url = selected_item.text() if selected_item else ""
        if not selected_url:
            self.status_label.setText(translate(self.language, "no_urls"))
            return
        try:
            logger.info(
                "Launching browser for %s (exam_mode=%s)",
                selected_url,
                self.exam_checkbox.isChecked(),
            )
            self.browser_window = ModernApp(
                selected_url,
                language=self.language,
                exam_mode=self.exam_checkbox.isChecked(),
                on_home=self._show_menu,
            )
            self.hide()
            if self.exam_checkbox.isChecked():
                self.browser_window.showFullScreen()
            else:
                self.browser_window.show()
        except Exception as error:
            logger.exception("Could not launch browser")
            QMessageBox.critical(
                self,
                translate(self.language, "app_title"),
                "Could not launch the browser:\n"
                f"{error}\n\nSee logs/bookapp.log for details.",
            )

    def _show_menu(self):
        self.browser_window = None
        self.show()
        self.raise_()
        self.activateWindow()


def main():
    configure_logging()
    try:
        import configreader

        _ = configreader.config
    except Exception:
        logger.exception("Configuration loading failed; continuing with defaults")
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True
    )
    app = QApplication(sys.argv)
    apply_app_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
