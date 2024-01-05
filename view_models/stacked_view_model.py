from PySide6.QtCore import QObject, Signal

from view_models import main_view_model


class StackedViewModel(QObject):
    stacked_item_id_update = Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self.main_view_model.stack_item_change_id.connect(
            lambda: self.change_current_stacked_item(self.main_view_model.current_stack_item_id))
        self._stacked_id = 0

    def reset_console_handler(self, id: int) -> None:
        if self._stacked_id == id:
            self.main_view_model.reset_console_alerts()

    def change_current_stacked_item(self, id: int):
        self._stacked_id = id
        self.stacked_item_id_update.emit()

    @property
    def new_id(self):
        return self._stacked_id
