from PySide6 import QtCore

from view_models import main_view_model


class NavigationViewModel(QtCore.QObject):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        self.main_view_model = main_view_model

    def stacked_item_change(self, id: int):
        self.main_view_model.set_current_stack_item_id(id)
