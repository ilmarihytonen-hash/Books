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
from PyQt6.QtGui import QDesktopServices, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from app_logging import configure_logging
from app_theme import apply_app_theme
from configreader import load_config
from credential_store import (
    get_login,
    origin_for_url,
    remove_login,
    save_login,
)
from feedback import feedback_label, open_feedback
from i18n import LANGUAGE_NAMES, translate
from saver import add_url, get_all_urls, normalize_url, remove_url
from settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    fill_requested = pyqtSignal(str, str)

    def __init__(self, origin, language, parent=None):
        super().__init__(parent)
        self.origin = origin
        self.language = language
        self.setWindowTitle(translate(language, "manage_logins"))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(translate(language, "login_origin", origin=origin)))

        form = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(translate(language, "login_username"), self.username_input)
        form.addRow(translate(language, "login_password"), self.password_input)
        layout.addLayout(form)

        saved_login = get_login(origin)
        if saved_login:
            self.username_input.setText(saved_login["username"])
            self.password_input.setText(saved_login["password"])

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        self.save_button = QPushButton(translate(language, "login_save"))
        self.save_button.clicked.connect(self._save)
        buttons.addWidget(self.save_button)

        self.fill_button = QPushButton(translate(language, "login_fill"))
        self.fill_button.clicked.connect(self._fill)
        buttons.addWidget(self.fill_button)

        self.remove_button = QPushButton(translate(language, "login_remove"))
        self.remove_button.setObjectName("removeUrl")
        self.remove_button.setEnabled(saved_login is not None)
        self.remove_button.clicked.connect(self._remove)
        buttons.addWidget(self.remove_button)

        self.close_button = QPushButton(translate(language, "login_close"))
        self.close_button.clicked.connect(self.reject)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

    def _save(self):
        try:
            save_login(
                self.origin,
                self.username_input.text(),
                self.password_input.text(),
            )
            self.remove_button.setEnabled(True)
            self.status_label.setText(translate(self.language, "login_saved"))
        except Exception as error:
            logger.exception("Could not save website login")
            QMessageBox.critical(
                self,
                translate(self.language, "manage_logins"),
                translate(self.language, "login_save_failed", error=error),
            )

    def _fill(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            self.status_label.setText(
                translate(self.language, "login_fields_required")
            )
            return
        self.fill_requested.emit(username, password)
        self.accept()

    def _remove(self):
        answer = QMessageBox.question(
            self,
            translate(self.language, "login_remove_confirm_title"),
            translate(
                self.language, "login_remove_confirm", origin=self.origin
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            if not remove_login(self.origin):
                self.remove_button.setEnabled(False)
                self.status_label.setText(
                    translate(self.language, "login_not_saved")
                )
                return
            self.username_input.clear()
            self.password_input.clear()
            self.remove_button.setEnabled(False)
            self.status_label.setText(translate(self.language, "login_removed"))
        except Exception as error:
            logger.exception("Could not remove website login")
            QMessageBox.critical(
                self,
                translate(self.language, "manage_logins"),
                translate(self.language, "login_remove_failed", error=error),
            )


class ModernApp(QMainWindow):
    home_requested = pyqtSignal()

    def __init__(self, aloitus_url, language="en", exam_mode=False, on_home=None):
        super().__init__()
        self.language = language if language in LANGUAGE_NAMES else "en"
        self.exam_mode = exam_mode
        self.on_home = on_home
        self._allow_exam_quit = False
        try:
            self.config = load_config()
        except Exception:
            logger.exception("Could not load browser configuration")
            self.config = {}
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

        self.menu_button = QToolButton()
        self.menu_button.setObjectName("appMenu")
        self.menu_button.setMinimumHeight(40)
        self.menu = QMenu(self.menu_button)
        self.home_action = self.menu.addAction("")
        self.home_action.triggered.connect(self._request_home)
        self.menu.addSeparator()
        self.license_action = self.menu.addAction("")
        self.license_action.triggered.connect(self._open_license)
        self.help_action = self.menu.addAction("")
        self.help_action.triggered.connect(self._open_help)
        self.feedback_action = self.menu.addAction("")
        self.feedback_action.triggered.connect(self._open_feedback)
        self.settings_action = self.menu.addAction("")
        self.settings_action.triggered.connect(self._open_settings)
        self.menu.addSeparator()
        self.login_action = self.menu.addAction("")
        self.login_action.triggered.connect(self._manage_login)
        self.menu_button.setMenu(self.menu)
        self.menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        toolbar_layout.addWidget(self.menu_button)

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

        self.remove_url_button = QPushButton()
        self.remove_url_button.setObjectName("removeUrl")
        self.remove_url_button.setMinimumHeight(40)
        self.remove_url_button.clicked.connect(self._remove_url)
        toolbar_layout.addWidget(self.remove_url_button)

        self.new_url_input = QLineEdit()
        toolbar_layout.addWidget(self.new_url_input, stretch=1)
        self.save_url_button = QPushButton()
        self.save_url_button.setMinimumHeight(40)
        self.save_url_button.clicked.connect(self._save_url)
        toolbar_layout.addWidget(self.save_url_button)

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
        self.web_view.setZoomFactor(
            self._configured_zoom(self.config.get("browser_zoom", 100))
        )
        self.web_view.setUrl(QUrl(self._as_http_url(starting_url)))

        root_layout.addWidget(self.toolbar)
        root_layout.addWidget(self.web_view, stretch=1)
        self.version_label = QLabel()
        self.version_label.setStyleSheet(
            "color: #a6adc8; font-size: 12px; padding: 2px 10px;"
        )
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        root_layout.addWidget(self.version_label)
        self.setCentralWidget(root)

        self.url_list.setVisible(not self.exam_mode)
        self.remove_url_button.setVisible(not self.exam_mode)
        self.new_url_input.setVisible(not self.exam_mode)
        self.save_url_button.setVisible(not self.exam_mode)
        self.menu_button.setVisible(not self.exam_mode)
        self.quit_exam_button.setVisible(self.exam_mode)

    @staticmethod
    def _as_http_url(value):
        if value.startswith(("http://", "https://")):
            return value
        return "https://" + value

    def _refresh_text(self):
        self.setWindowTitle(translate(self.language, "app_title"))
        self.menu_button.setText(translate(self.language, "menu"))
        self.home_action.setText(translate(self.language, "home"))
        self.license_action.setText(translate(self.language, "license"))
        self.help_action.setText(translate(self.language, "help"))
        self.feedback_action.setText(feedback_label(self.language))
        self.settings_action.setText(translate(self.language, "settings"))
        self.login_action.setText(translate(self.language, "manage_logins"))
        self.new_url_input.setPlaceholderText(translate(self.language, "new_url"))
        self.save_url_button.setText(translate(self.language, "save_url"))
        self.remove_url_button.setText(translate(self.language, "remove_url"))
        self.quit_exam_button.setText(translate(self.language, "quit_exam"))
        version = self.config.get("version_number", "unknown")
        self.version_label.setText(
            translate(self.language, "project_version", version=version)
        )

    @staticmethod
    def _configured_zoom(value):
        try:
            zoom = int(value)
        except (TypeError, ValueError):
            return 1.0
        return max(50, min(150, zoom)) / 100

    def _open_help(self):
        QMessageBox.information(
            self,
            translate(self.language, "help"),
            translate(self.language, "help_text"),
        )

    def _request_home(self):
        self.home_requested.emit()

    def _open_feedback(self):
        open_feedback(self, self.language)

    def _open_license(self):
        if not QDesktopServices.openUrl(
            QUrl("https://www.gnu.org/licenses/gpl-3.0.html")
        ):
            QMessageBox.warning(
                self,
                translate(self.language, "license"),
                translate(self.language, "license_open_failed"),
            )

    def _open_settings(self):
        try:
            dialog = SettingsDialog(self.language, self)
        except Exception as error:
            logger.exception("Could not open application settings")
            QMessageBox.critical(
                self,
                translate(self.language, "settings"),
                translate(self.language, "settings_open_failed", error=error),
            )
            return
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.language = dialog.language_combo.currentData()
        self.config = dialog.config
        self.web_view.setZoomFactor(
            self._configured_zoom(self.config.get("browser_zoom", 100))
        )
        self._refresh_text()

        main_window = getattr(self.on_home, "__self__", None)
        if isinstance(main_window, QMainWindow):
            main_window.language = self.language
            main_window.config = self.config
            language_index = main_window.language_combo.findData(self.language)
            if language_index >= 0:
                main_window.language_combo.blockSignals(True)
                main_window.language_combo.setCurrentIndex(language_index)
                main_window.language_combo.blockSignals(False)
            main_window._refresh_text()
            main_window._populate_urls()

    def _manage_login(self):
        try:
            origin = origin_for_url(self.web_view.url().toString())
            dialog = LoginDialog(origin, self.language, self)
        except Exception as error:
            logger.exception("Could not open saved website logins")
            QMessageBox.warning(
                self,
                translate(self.language, "manage_logins"),
                translate(self.language, "login_load_failed", error=error),
            )
            return
        dialog.fill_requested.connect(self._fill_login)
        dialog.exec()

    def _fill_login(self, username, password):
        import json

        script = f"""(() => {{
            const username = {json.dumps(username)};
            const password = {json.dumps(password)};
            const visible = (input) => input.getClientRects().length > 0;
            const passwordField = Array.from(
                document.querySelectorAll('input[type="password"]')
            ).find(visible);
            if (!passwordField) return "no-password-field";
            const inputs = Array.from(document.querySelectorAll('input'))
                .filter((input) => input !== passwordField &&
                    input.type !== "hidden" && input.type !== "password" &&
                    visible(input));
            const usernameField = inputs.find((input) =>
                /user|email|login|account/i.test(
                    [input.name, input.id, input.autocomplete].join(" ")
                )
            ) || inputs.find((input) =>
                input.type === "text" || input.type === "email"
            );
            if (!usernameField) return "no-username-field";
            const setValue = (input, value) => {{
                const setter = Object.getOwnPropertyDescriptor(
                    HTMLInputElement.prototype, "value"
                ).set;
                setter.call(input, value);
                input.dispatchEvent(new Event("input", {{ bubbles: true }}));
                input.dispatchEvent(new Event("change", {{ bubbles: true }}));
            }};
            setValue(usernameField, username);
            setValue(passwordField, password);
            return "filled";
        }})()"""
        self.web_view.page().runJavaScript(
            script,
            lambda result: self._show_login_fill_result(result),
        )

    def _show_login_fill_result(self, result):
        if result == "filled":
            message = translate(self.language, "login_fill_success")
            show_message = QMessageBox.information
        else:
            message = translate(self.language, "login_fill_failed")
            show_message = QMessageBox.warning
        show_message(
            self,
            translate(self.language, "manage_logins"),
            message,
        )

    def _navigate(self, address):
        if address and not self.exam_mode:
            logger.info("Navigating to %s", address)
            self.web_view.setUrl(QUrl(self._as_http_url(address)))

    def _selected_url_changed(self, row):
        item = self.url_list.item(row)
        if item:
            self._navigate(item.text())

    def _remove_url(self):
        selected_item = self.url_list.currentItem()
        if not selected_item:
            QMessageBox.information(
                self,
                translate(self.language, "app_title"),
                translate(self.language, "select_url_to_remove"),
            )
            return

        url = selected_item.text()
        answer = QMessageBox.question(
            self,
            translate(self.language, "url_remove_confirm_title"),
            translate(self.language, "url_remove_confirm", url=url),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            if not remove_url(url):
                raise ValueError("The website is not in the saved URL list")
            current_row = self.url_list.currentRow()
            self.saved_urls = get_all_urls()
            self.url_list.blockSignals(True)
            self.url_list.clear()
            self.url_list.addItems(self.saved_urls)
            if self.saved_urls:
                self.url_list.setCurrentRow(
                    min(current_row, len(self.saved_urls) - 1)
                )
            self.url_list.blockSignals(False)
        except Exception as error:
            self.url_list.blockSignals(False)
            logger.exception("Could not remove website")
            QMessageBox.critical(
                self,
                translate(self.language, "app_title"),
                translate(self.language, "url_remove_failed", error=error),
            )

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

    def update_clock(self):
        self.clock_label.setText(QTime.currentTime().toString("hh:mm:ss"))

    def _enter_exam_mode(self):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.url_list.hide()
        self.new_url_input.hide()
        self.save_url_button.hide()
        self.menu_button.hide()
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
