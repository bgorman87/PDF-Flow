from PySide6.QtCore import QObject
from PySide6.QtWidgets import QPushButton
from os import startfile, system

from view_models import main_view_model


class NavigationViewModel(QObject):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        self.main_view_model = main_view_model
        self._currently_active_button = None

    @property
    def currently_active_button(self) -> QPushButton:
        return self._currently_active_button

    @currently_active_button.setter
    def currently_active_button(self, button: QPushButton):
        self._currently_active_button = button

    def stacked_item_change(self, button: QPushButton):
        self.main_view_model.set_current_stack_item_id(button.property("id"))
        self._currently_active_button = button
        
    def open_feedback_link(self):
        """Opens the default email client with a pre-filled email to the developer."""

        mailto_link = f"mailto:brandon.gorman@englobecorp.com?subject=PDF%20Flow%20v{self.main_view_model.version}%20Feedback"

        if self.main_view_model.os == "win32":
            startfile(mailto_link)
        elif self.main_view_model.os == "darwin":
            system(f'open "{mailto_link}"')
        elif self.main_view_model.os == "linux":
            system(f'xdg-open "{mailto_link}"')
