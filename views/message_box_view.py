from PySide6 import QtWidgets
from view_models import message_box_view_model

class MessageBoxView(QtWidgets.QMessageBox):
    def __init__(self, view_model: message_box_view_model.MessageBoxViewModel):
        super().__init__()
        self.view_model = view_model
        self.setWindowTitle(self.view_model.window_title)
        self.setIcon(self.view_model.icon)
        self.setText(self.view_model.text)
        self.buttons = self.view_model.buttons
        self.roles = self.view_model.roles

        for button, role in zip(self.buttons, self.roles):
            self.addButton(button, role)
