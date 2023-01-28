from PySide6 import QtCore, QtGui, QtWidgets
from view_models import main_view_model
class MessageBoxViewModel(QtCore.QObject):
    def __init__(self, main_view_model: main_view_model.MainViewModel, message_box_dictionary: dict):
        super().__init__()
        self.main_view_model = main_view_model
        self._window_title = message_box_dictionary["title"]
        self._icon = message_box_dictionary["icon"]
        self._text = message_box_dictionary["text"]
        self._buttons = message_box_dictionary["buttons"]
        self._roles = message_box_dictionary["button_roles"]

    @property
    def window_title(self):
        return self._window_title
    
    @property
    def icon(self):
        return self._icon
    
    @property
    def text(self):
        return self._text
    
    @property
    def buttons(self):
        return self._buttons
    
    @property
    def roles(self):
        return self._roles

