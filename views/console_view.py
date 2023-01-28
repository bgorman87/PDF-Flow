from PySide6 import QtWidgets
from view_models import console_view_model

class ConsoleWidget(QtWidgets.QPlainTextEdit):
    def __init__(self, view_model: console_view_model.ConsoleViewModel):
        super().__init__()
        self.setObjectName("console")
        self.setReadOnly(True)
        self.view_model = view_model
        self.view_model.console_text_insert.connect(lambda: self.insertPlainText(self.view_model.text))
