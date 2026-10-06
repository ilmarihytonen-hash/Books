"""Shared dark theme for all application windows."""

from PyQt6.QtGui import QColor, QPalette

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
    color: #11111b;
    border: 2px solid #89b4fa;
    border-radius: 6px;
    min-height: 42px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton * {
    color: #11111b;
}
QPushButton:hover {
    background-color: #b4befe;
    border-color: #b4befe;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #cdd6f4;
    border-color: #45475a;
}
QPushButton#quitExam {
    background-color: #f38ba8;
    color: #11111b;
}
QPushButton#quitExam:hover {
    background-color: #eba0ac;
}
QPushButton#removeUrl {
    background-color: #f38ba8;
    color: #11111b;
}
QPushButton#removeUrl:hover {
    background-color: #eba0ac;
}
QToolButton#appMenu {
    color: #cdd6f4;
    background-color: #313244;
    border: 1px solid #585b70;
    border-radius: 6px;
    min-height: 40px;
    padding: 6px 12px;
    font-weight: 700;
}
QToolButton#appMenu:hover {
    background-color: #45475a;
}
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #585b70;
    padding: 6px;
}
QMenu::item {
    color: #cdd6f4;
    padding: 9px 28px;
}
QMenu::item:selected {
    color: #1e1e2e;
    background-color: #89b4fa;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    selection-background-color: #45475a;
}
"""


def apply_app_theme(application):
    application.setStyleSheet(APP_STYLESHEET)
    palette = application.palette()
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#11111b"))
    application.setPalette(palette)
