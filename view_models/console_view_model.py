from view_models import main_view_model
from PySide6 import QtCore

class ConsoleViewModel(QtCore.QObject):
    console_text_insert = QtCore.Signal()
    
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self.main_view_model.console_text_update.connect(lambda: self.add_console_text(self.main_view_model.console_text))
        self._new_console_text = ""

    def add_console_text(self, console_text):
        self._new_console_text = console_text
        self.console_text_insert.emit()

    @property
    def text(self):
        return f"{self._new_console_text}\n"

    @text.setter
    def text(self, value):
        self._new_console_text = value
        self.console_text_insert.emit()
