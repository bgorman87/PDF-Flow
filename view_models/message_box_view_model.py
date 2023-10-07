from PySide6 import QtCore, QtGui, QtWidgets
from view_models import main_view_model
from utils.general_utils import MessageBox


class MessageBoxViewModel(QtCore.QObject):
    def __init__(
        self, main_view_model: main_view_model.MainViewModel, message_box: MessageBox
    ):
        super().__init__()
        self.main_view_model = main_view_model
        self._window_title = message_box.title
        self._icon = message_box.icon
        self._text = message_box.text
        self._buttons = message_box.buttons
        self._roles = message_box.button_roles

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
