from PySide6 import QtCore, QtWidgets
from models import main_model
import typing


class MainViewModel(QtCore.QObject):

    console_text_update = QtCore.Signal()
    stack_item_change = QtCore.Signal()
    message_box_alert = QtCore.Signal(dict)
    console_alerts_update = QtCore.Signal()
    loaded_files_update = QtCore.Signal()
    processed_files_update = QtCore.Signal()
    emailed_files_update = QtCore.Signal()
    process_progress_text_update = QtCore.Signal()
    process_progress_value_update = QtCore.Signal()
    procress_button_state_update = QtCore.Signal()
    process_button_count_update = QtCore.Signal()


    def __init__(self, main_model: main_model.MainModel):
        super().__init__()
        self.console_text = ""
        self.main_model = main_model
        self.main_model.initialize_database()
        self.current_stack_item = 0
        self.console_alerts = 0
        self.loaded_files = 0
        self.processed_files = 0
        self.emailed_files = 0
        self.process_progress_text = ""
        self.process_progress_value = 0
        self.process_button_state = True
        self.process_button_count = 0

    def add_console_text(self, new_text: str) -> None:
        self.console_text = new_text
        self.console_text_update.emit()

    def add_console_alerts(self, alerts: int) -> None:
        self.console_alerts += alerts
        self.console_alerts_update.emit()

    def set_current_stack_item(self, id: int) -> None:
        self.current_stack_item = id
        self.stack_item_change.emit()

    def reset_console_alerts(self) -> None:
        self.console_alerts = 0
        self.console_alerts_update.emit()

    def set_loaded_files(self, loaded_files_count: int) -> None:
        self.loaded_files = loaded_files_count
        self.loaded_files_update.emit()

    def set_processed_files(self, processed_files_count: int) -> None:
        self.processed_files = processed_files_count
        self.processed_files_update.emit()

    def set_emailed_files_update(self, emailed_files_count: int) -> None:
        self.emailed_files = emailed_files_count
        self.emailed_files_update.emit()

    def set_process_progress_text(self, text: str) -> None:
        self.process_progress_text = text
        self.process_progress_text_update.emit()

    def set_process_progress_value(self, value: int) -> None:
        self.process_progress_value = value
        self.process_progress_value_update.emit()

    def set_process_button_state(self, state: bool) -> None:
        self.process_button_state = state
        self.procress_button_state_update.emit()

    def set_process_button_count(self, value: int) -> None:
        self.process_button_count = value
        self.process_button_count_update.emit()

    def fetch_file_profiles(self) -> list[str]:
        return self.main_model.fetch_file_profiles()

    def fetch_active_parameters(
        self, profile_name: str
    ) -> tuple[list[tuple[str]], str]:
        return self.main_model.fetch_active_parameters(profile_name)

    def fetch_profile_file_name_pattern(self, profile_name: str) -> str:
        return self.main_model.fetch_profile_file_name_pattern(profile_name)

    def update_profile_file_name_pattern(
        self, profile_name: str, profile_file_name_pattern: str
    ) -> None:
        self.main_model.update_file_profile_file_name_pattern(
            profile_name, profile_file_name_pattern
        )

    def message_box_handler(
        self,
        message_box_result: int,
        callback: typing.Callable,
    ):
        # 5 = YesRole & 0 = AcceptRole
        if message_box_result != 5 and message_box_result != 0:
            return
        callback()
