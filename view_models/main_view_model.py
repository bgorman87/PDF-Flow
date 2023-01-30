import typing

from PySide6 import QtCore, QtWidgets

from models import main_model


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

    def update_processed_files_count(self, processed_files_count: int) -> None:
        self.processed_files += processed_files_count
        self.processed_files_update.emit()

    def reset_processed_files_count(self) -> None:
        self.process_files = 0
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

    def fetch_file_profiles(self, order_by: str = None) -> list[str]:
        return self.main_model.fetch_file_profiles(order_by=order_by)

    def fetch_profile_id(self, profile_name: str) -> int:
        return self.main_model.fetch_profile_id(profile_name=profile_name)

    def fetch_active_parameters(
        self, profile_id: str
    ) -> list[str]:
        return self.main_model.fetch_active_parameters(profile_id=profile_id)
    
    def update_profile_used_count(self, profile_id: int) -> None:
        self.main_model.update_profile_used_count(profile_id=profile_id)

    def fetch_project_directory(self, project_number: str) -> str:
        return self.main_model.fetch_project_directory(project_number=project_number)
    
    def fetch_all_project_directories(self) -> list[str]:
        return self.main_model.fetch_all_project_directories
    
    def fetch_all_project_numbers(self) -> list[str]:
        return self.main_model.fetch_all_project_numbers

    def fetch_profile_file_name_pattern(self, profile_id: int) -> str:
        return self.main_model.fetch_profile_file_name_pattern(profile_id=profile_id)
    
    def fetch_parameter_example_text(self, profile_id: int, paramater: str) -> str:
        return self.main_model.fetch_parameter_example_text(profile_id=profile_id, paramater=paramater)

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
