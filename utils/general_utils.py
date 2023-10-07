from typing import List, Optional, Callable
from PySide6.QtWidgets import QMessageBox, QPushButton


class MessageBox:
    def __init__(
        self,
        title: str = "",
        icon: QMessageBox.Icon = QMessageBox.Information,
        text: str = "",
        buttons: List[QPushButton] = None,
        button_roles: List[QMessageBox.ButtonRole] = None,
        callback: Optional[Callable] = None,
    ):
        self.title = title
        self.icon = icon
        self.text = text
        self.buttons = buttons or []
        self.button_roles = button_roles or []
        self.callback = callback


class FauxResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text
