from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressDialog


class LoadingWidget(QProgressDialog):
    def __init__(self, title: str, text: str, start: int = 0, end: int = 100, val: int = 0):
        super().__init__(parent=None)
        self.setWindowTitle(title)
        self.setLabelText(text)
        self.setMinimum(start)
        self.setMaximum(end)
        self.setWindowModality(Qt.WindowModal)
        self.setAutoClose(True)
        self.setAutoReset(True)
        self.setValue(val)
        self.show()

    def update_val(self, value):
        self.setValue(value)
