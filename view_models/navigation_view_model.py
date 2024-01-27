import os

from PySide6 import QtCore, QtWidgets

from view_models import main_view_model


class NavigationViewModel(QtCore.QObject):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        self.main_view_model = main_view_model
        self._currently_active_button = None

    @property
    def currently_active_button(self) -> QtWidgets.QPushButton:
        return self._currently_active_button

    @currently_active_button.setter
    def currently_active_button(self, button: QtWidgets.QPushButton):
        self._currently_active_button = button

    def stacked_item_change(self, button: QtWidgets.QPushButton):
        self.main_view_model.set_current_stack_item_id(button.property("id"))
        self._currently_active_button = button
        
    def open_feedback_link(self):
        """Opens the default email client with a pre-filled email to the developer."""

        mailto_link = f"mailto:brandon@godevservices.com?subject=PDF%20Flow%20v{self.main_view_model.version}%20Feedback"

        if self.main_view_model.os == "win32":
            os.startfile(mailto_link)
        elif self.main_view_model.os == "darwin":
            os.system(f'open "{mailto_link}"')
        elif self.main_view_model.os == "linux":
            os.system(f'xdg-open "{mailto_link}"')
