"""Bookapp splash screen and application entry point."""

import logging
import sys

from PyQt6.QtCore import QCoreApplication, Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QLabel, QProgressBar, QVBoxLayout, QWidget

from app_logging import configure_logging
from app_theme import apply_app_theme
from i18n import translate
from saver import get_language

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "WINDOW_WIDTH": 600,
    "WINDOW_HEIGHT": 400,
    "ACCENT_COLOR": "#89b4fa",
    "TEXT_COLOR_MAIN": "#ffffff",
    "TEXT_COLOR_SUB": "#a6adc8",
    "FALLBACK_BG_COLOR": "#1e1e2e",
    "ANIMATION_SPEED_MS": 30,
}


class ConfigurableSplashScreen(QWidget):
    def __init__(self, language="en"):
        super().__init__()
        self.language = language
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(
            DEFAULT_CONFIG["WINDOW_WIDTH"], DEFAULT_CONFIG["WINDOW_HEIGHT"]
        )
        self.progress_value = 0
        self.main_window = None
        self._create_ui()
        self._center_on_screen()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(DEFAULT_CONFIG["ANIMATION_SPEED_MS"])

    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 50, 40, 40)
        layout.setSpacing(12)
        self.setStyleSheet(
            f"background-color: {DEFAULT_CONFIG['FALLBACK_BG_COLOR']};"
        )

        brand = QLabel(translate(self.language, "brand_title"))
        brand.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        brand.setStyleSheet(
            f"color: {DEFAULT_CONFIG['ACCENT_COLOR']}; background: transparent;"
        )
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(translate(self.language, "subtitle"))
        subtitle.setStyleSheet(
            f"color: {DEFAULT_CONFIG['TEXT_COLOR_SUB']}; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel(translate(self.language, "starting"))
        self.status_label.setStyleSheet(
            f"color: {DEFAULT_CONFIG['TEXT_COLOR_MAIN']}; background: transparent;"
        )
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #313244; border: none; border-radius: 4px; }"
            f"QProgressBar::chunk {{ background: {DEFAULT_CONFIG['ACCENT_COLOR']}; "
            "border-radius: 4px; }"
        )

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

    def _center_on_screen(self):
        screen = self.screen()
        if screen:
            frame = self.frameGeometry()
            frame.moveCenter(screen.availableGeometry().center())
            self.move(frame.topLeft())

    def _update_progress(self):
        self.progress_value = min(100, self.progress_value + 1)
        self.progress_bar.setValue(self.progress_value)
        if self.progress_value < 30:
            key = "starting"
        elif self.progress_value < 100:
            key = "loading"
        else:
            key = "ready"
        self.status_label.setText(translate(self.language, key))
        if self.progress_value == 100:
            self.timer.stop()
            self._launch_main_application()

    def _launch_main_application(self):
        from main import MainWindow

        logger.info("Splash screen complete; opening application menu")
        self.main_window = MainWindow(language=self.language)
        self.close()
        self.main_window.show()


def main():
    configure_logging()
    try:
        language = get_language()
    except Exception:
        logger.exception("Could not load language preference; using English")
        language = "en"
    QCoreApplication.setAttribute(
        Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True
    )
    app = QApplication(sys.argv)
    apply_app_theme(app)
    splash = ConfigurableSplashScreen(language)
    splash.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
