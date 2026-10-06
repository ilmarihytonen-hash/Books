"""PyQt browser window with optional exam kiosk mode."""

import logging
import sys

from PyQt6.QtCore import (
    QCoreApplication,
    QEvent,
    Qt,
    QTime,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
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
from PyQt6.QtWebEngineWidgets import QWebEngineView

from app_logging import configure_logging
from app_theme import apply_app_theme
from i18n import LANGUAGE_NAMES, translate
from saver import add_url, get_all_urls, normalize_url, set_language

logger = logging.getLogger(__name__)


class ModernApp(QMainWindow):
    home_requested = pyqtSignal()

    def __init__(self, aloitus_url, language="en", exam_mode=False, on_home=None):
        super().__init__()
        self.language = language if language in LANGUAGE_NAMES else "en"
        self.exam_mode = exam_mode
        self.on_home = on_home
        self._allow_exam_quit = False
        self.setWindowTitle(translate(self.language, "app_title"))
        self.resize(1200, 800)
        self._create_ui(aloitus_url)
        self._refresh_text()

        self.home_requested.connect(self._go_home)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        if self.exam_mode:
            self._enter_exam_mode()
            application = QApplication.instance()
            if application:
                application.installEventFilter(self)

    def _create_ui(self, starting_url):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.toolbar = QWidget()
        self.toolbar.setStyleSheet("background-color: #181825;")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(10)

        self.home_button = QPushButton()
        self.home_button.clicked.connect(self.home_requested.emit)
        toolbar_layout.addWidget(self.home_button)

        self.url_list = QListWidget()
        self.url_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self.url_list.setMaximumHeight(76)
        try:
            self.saved_urls = get_all_urls()
        except Exception:
            logger.exception("Could not load saved websites")
            self.saved_urls = []
        if starting_url not in self.saved_urls:
            self.saved_urls.append(starting_url)
        self.url_list.addItems(self.saved_urls)
        matches = self.url_list.findItems(
            starting_url, Qt.MatchFlag.MatchExactly
        )
        if matches:
            self.url_list.setCurrentItem(matches[0])
        self.url_list.currentRowChanged.connect(self._selected_url_changed)
        toolbar_layout.addWidget(self.url_list, stretch=1)

        self.new_url_input = QLineEdit()
        toolbar_layout.addWidget(self.new_url_input, stretch=1)
        self.save_url_button = QPushButton()
        self.save_url_button.clicked.connect(self._save_url)
        toolbar_layout.addWidget(self.save_url_button)

        self.language_combo = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.currentIndexChanged.connect(self._language_changed)
        language_index = self.language_combo.findData(self.language)
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)
        toolbar_layout.addWidget(self.language_combo)

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 0 8px;"
        )
        toolbar_layout.addWidget(self.clock_label)

        self.quit_exam_button = QPushButton()
        self.quit_exam_button.setObjectName("quitExam")
        self.quit_exam_button.clicked.connect(self._quit_exam)
        toolbar_layout.addWidget(self.quit_exam_button)

        self.web_view = QWebEngineView()
        if self.exam_mode:
            self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.web_view.setUrl(QUrl(self._as_http_url(starting_url)))

        root_layout.addWidget(self.toolbar)
        root_layout.addWidget(self.web_view, stretch=1)
        self.setCentralWidget(root)

        self.url_list.setVisible(not self.exam_mode)
        self.new_url_input.setVisible(not self.exam_mode)
        self.save_url_button.setVisible(not self.exam_mode)
        self.language_combo.setVisible(not self.exam_mode)
        self.home_button.setVisible(not self.exam_mode)
        self.quit_exam_button.setVisible(self.exam_mode)

    @staticmethod
    def _as_http_url(value):
        if value.startswith(("http://", "https://")):
            return value
        return "https://" + value

    def _refresh_text(self):
        self.setWindowTitle(translate(self.language, "app_title"))
        self.home_button.setText(translate(self.language, "home"))
        self.new_url_input.setPlaceholderText(translate(self.language, "new_url"))
        self.save_url_button.setText(translate(self.language, "save_url"))
        self.quit_exam_button.setText(translate(self.language, "quit_exam"))

    def _navigate(self, address):
        if address and not self.exam_mode:
            logger.info("Navigating to %s", address)
            self.web_view.setUrl(QUrl(self._as_http_url(address)))

    def _selected_url_changed(self, row):
        item = self.url_list.item(row)
        if item:
            self._navigate(item.text())

    def _save_url(self):
        value = self.new_url_input.text().strip()
        normalized_url = normalize_url(value)
        if not normalized_url:
            QMessageBox.warning(
                self,
                translate(self.language, "app_title"),
                translate(self.language, "url_invalid"),
            )
            return
        try:
            if not add_url(normalized_url):
                QMessageBox.warning(
                    self,
                    translate(self.language, "app_title"),
                    translate(self.language, "url_exists"),
                )
                return
            self.saved_urls = get_all_urls()
            self.url_list.blockSignals(True)
            self.url_list.clear()
            self.url_list.addItems(self.saved_urls)
            self.url_list.setCurrentRow(self.url_list.count() - 1)
            self.url_list.blockSignals(False)
            self.new_url_input.clear()
            self._navigate(self.url_list.currentItem().text())
        except Exception as error:
            logger.exception("Could not save website")
            QMessageBox.critical(
                self,
                translate(self.language, "app_title"),
                translate(self.language, "url_save_failed", error=error),
            )

    def _language_changed(self, index):
        language = self.language_combo.itemData(index)
        if not language or language == self.language:
            return
        self.language = language
        try:
            set_language(language)
        except Exception:
            logger.exception("Could not save language preference")
        self._refresh_text()

    def update_clock(self):
        self.clock_label.setText(QTime.currentTime().toString("hh:mm:ss"))

    def _enter_exam_mode(self):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.url_list.hide()
        self.new_url_input.hide()
        self.save_url_button.hide()
        self.language_combo.hide()
        self.home_button.hide()
        self.quit_exam_button.show()
        logger.info("Exam kiosk mode enabled")

    def _quit_exam(self):
        answer = QMessageBox.question(
            self,
            translate(self.language, "confirm_quit_title"),
            translate(self.language, "confirm_quit"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        logger.info("Exam session quit from the exam control")
        self._allow_exam_quit = True
        application = QApplication.instance()
        if application:
            application.removeEventFilter(self)
            application.quit()
        else:
            self.close()

    def _go_home(self):
        if self.exam_mode:
            return
        if self.on_home:
            self.close()
            self.on_home()
            return
        try:
            from main import MainWindow

            self._home_window = MainWindow(language=self.language)
            self._home_window.show()
            self.close()
        except Exception:
            logger.exception("Could not open the application menu")
            self.close()

    def eventFilter(self, watched, event):
        if (
            self.exam_mode
            and event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
        ):
            key_event = event
            if key_event.key() in (
                Qt.Key.Key_Escape,
                Qt.Key.Key_F11,
                Qt.Key.Key_F12,
            ):
                key_event.accept()
                return True
        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        if self.exam_mode and not self._allow_exam_quit:
            event.ignore()
            return
        event.accept()

def main():
    configure_logging()
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True
    )
    app = QApplication(sys.argv)
    apply_app_theme(app)
    url = sys.argv[1] if len(sys.argv) > 1 else "https://wikipedia.org"
    language = sys.argv[2] if len(sys.argv) > 2 else "en"
    exam_mode = "--exam" in sys.argv[3:]
    window = ModernApp(url, language=language, exam_mode=exam_mode)
    if exam_mode:
        window.showFullScreen()
    else:
        window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
