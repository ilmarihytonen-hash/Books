"""Shared dark theme for all application windows."""

APP_STYLESHEET = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI";
    font-size: 14px;
}
QLabel#brand {
    color: #89b4fa;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 2px;
}
QLineEdit, QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 9px;
    selection-background-color: #89b4fa;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #7f849c;
}
QPushButton#quitExam {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#quitExam:hover {
    background-color: #eba0ac;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    selection-background-color: #45475a;
}
"""


def apply_app_theme(application):
    application.setStyleSheet(APP_STYLESHEET)
