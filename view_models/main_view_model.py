import os
import typing

from PySide6 import QtCore

from models import main_model
from utils.general_utils import MessageBox


class MainViewModel(QtCore.QObject):
    console_text_update = QtCore.Signal()
    stack_item_change_id = QtCore.Signal()
    message_box_alert = QtCore.Signal(MessageBox)
    console_alerts_update = QtCore.Signal()
    loaded_files_count_update = QtCore.Signal()
    processed_files_update = QtCore.Signal()
    emailed_files_count_update = QtCore.Signal()
    process_progress_text_update = QtCore.Signal()
    process_progress_value_update = QtCore.Signal()
    process_button_state_update = QtCore.Signal()
    process_button_count_update = QtCore.Signal()
    window_size_update = QtCore.Signal()
    profile_update_list = QtCore.Signal()
    parameter_update_list = QtCore.Signal()
    email_profiles_updated = QtCore.Signal(list)

    def __init__(self, main_model: main_model.MainModel):
        super().__init__()
        self.console_text = ""
        self.main_model = main_model
        self.main_model.initialize_database()
        self.current_stack_item_id = 0
        self.console_alerts = 0
        self.loaded_files_count = 0
        self.processed_files = 0
        self.emailed_files_count = 0
        self.process_progress_text = ""
        self.process_progress_value = 0
        self.process_button_state = True
        self.process_button_count = 0
        self.os = os.sys.platform
        self.version = "1.0.0"

    def add_console_text(self, new_text: str) -> None:
        self.console_text = new_text
        self.console_text_update.emit()

    def add_console_alerts(self, alerts: int) -> None:
        self.console_alerts += alerts
        self.console_alerts_update.emit()

    def set_current_stack_item_id(self, id: int) -> None:
        self.current_stack_item_id = id
        self.stack_item_change_id.emit()

    def reset_console_alerts(self) -> None:
        self.console_alerts = 0
        self.console_alerts_update.emit()

    def set_loaded_files_count(self, loaded_files_count: int) -> None:
        self.loaded_files_count = loaded_files_count
        self.loaded_files_count_update.emit()

    def update_processed_files_count(self, processed_files_count: int) -> None:
        self.processed_files += processed_files_count
        self.processed_files_update.emit()

    def reset_processed_files_count(self) -> None:
        self.process_files = 0
        self.processed_files_update.emit()

    def fetch_parameter_id_by_name_and_profile_id(
        self, profile_id: int, parameter_name: str
    ) -> int:
        return self.main_model.fetch_parameter_id_by_name(
            profile_id=profile_id, parameter_name=parameter_name
        )

    def update_emailed_files_update_count(self, emailed_files_count: int) -> None:
        self.emailed_files_count += emailed_files_count
        self.emailed_files_count_update.emit()

    def set_process_progress_bar_text(self, text: str) -> None:
        self.process_progress_text = text
        self.process_progress_text_update.emit()

    def set_process_progress_bar_value(self, value: int) -> None:
        self.process_progress_value = value
        self.process_progress_value_update.emit()

    def set_process_button_state(self, state: bool) -> None:
        self.process_button_state = state
        self.process_button_state_update.emit()

    def set_process_button_count(self, value: int) -> None:
        self.process_button_count = value
        self.process_button_count_update.emit()

    def fetch_all_file_profiles(self, order_by: str = None) -> list[str]:
        return self.main_model.fetch_all_file_profiles(order_by=order_by)

    def fetch_file_profiles_for_settings(self, order_by=None) -> list[str]:
        profiles = self.main_model.fetch_all_file_profiles(order_by)
        # format just the [name, identifier text]
        dropdown_profiles = [[profile[2], profile[1]] for profile in profiles]
        return dropdown_profiles

    def fetch_profile_id_by_profile_name(self, profile_name: str) -> int:
        return self.main_model.fetch_profile_id_by_profile_name(
            profile_name=profile_name
        )

    def fetch_profile_description_by_profile_id(self, profile_id: int) -> str:
        return self.main_model.fetch_profile_description_by_profile_id(
            profile_id=profile_id
        )

    def fetch_active_parameters_by_profile_id(self, profile_id: str) -> list[str]:
        return self.main_model.fetch_active_parameters_by_profile_id(
            profile_id=profile_id
        )
    
    def fetch_project_description_by_project_number(self, project_number: str) -> str:
        return self.main_model.fetch_project_description_by_project_number(
            project_number=project_number
        )

    def fetch_project_description_example(self) -> str:
        return self.main_model.fetch_project_description_example()

    def fetch_advanced_option_by_parameter_name_and_profile_id(
        self, profile_id: int, parameter_name: str
    ) -> str:
        return self.main_model.fetch_advanced_option_by_parameter_name_and_profile_id(
            profile_id=profile_id, parameter_name=parameter_name
        )
    
    def fetch_secondary_parameter_by_parameter_id(self, parameter_id: int) -> list[str]:
        return self.main_model.fetch_secondary_parameter_by_parameter_id(
            parameter_id=parameter_id
        )

    def display_message_box(self, message_box: dict):
        self.message_box_alert.emit(message_box)

    def update_profile_used_count_by_profile_id(self, profile_id: int) -> None:
        self.main_model.update_profile_used_count_by_profile_id(profile_id=profile_id)

    def fetch_project_directory_by_project_number(self, project_number: str) -> str:
        return self.main_model.fetch_project_directory_by_project_number(
            project_number=project_number
        )

    def fetch_all_project_directories(self) -> list[str]:
        return self.main_model.fetch_all_project_directories()

    def fetch_all_project_numbers(self) -> list[str]:
        return self.main_model.fetch_all_project_numbers()

    def fetch_profile_file_name_pattern_by_profile_id(self, profile_id: int) -> str:
        return self.main_model.fetch_profile_file_name_pattern_by_profile_id(
            profile_id=profile_id
        )

    def fetch_parameter_example_text_by_name_and_profile_id(
        self, profile_id: int, parameter: str
    ) -> str:
        return self.main_model.fetch_parameter_example_text_by_name_and_profile_id(
            profile_id=profile_id, parameter=parameter
        )

    def fetch_all_profile_template_info(self) -> list[str]:
        return self.main_model.fetch_all_profile_template_info()

    def fetch_profile_rectangle_bounds_by_profile_id(
        self, profile_id: int
    ) -> list[str]:
        return self.main_model.fetch_profile_rectangle_bounds_by_profile_id(
            profile_id=profile_id
        )

    def fetch_all_project_data(self) -> list[str]:
        return self.main_model.fetch_all_project_data()

    def fetch_project_data_by_project_number(self, project_number: str) -> list[str]:
        return self.main_model.fetch_project_data_by_project_number(
            project_number=project_number
        )

    def fetch_project_data_table_headers(self) -> list[str]:
        return self.main_model.fetch_project_data_table_headers()

    def delete_template_profile(self, profile_id: int):
        self.main_model.delete_profile_by_id(profile_id=profile_id)

    def import_project_data_thread(self, project_data: list[str]):
        self.main_model.import_project_data_thread(project_data=project_data)

    def export_project_data_thread(self, export_location: str):
        self.main_model.export_project_data_thread(export_location=export_location)

    def delete_all_project_data_thread(self):
        self.main_model.delete_all_project_data_thread()

    def rename_template_profile(self, profile_id: int, new_name: str) -> str:
        return self.main_model.rename_template_profile(
            profile_id=profile_id, new_name=new_name
        )

    def add_new_profile(
        self,
        profile_identifier: str,
        profile_name: str,
        x_1: int,
        x_2: int,
        y_1: int,
        y_2: int,
    ):
        self.main_model.add_new_profile(
            profile_identifier=profile_identifier,
            profile_name=profile_name,
            x_1=x_1,
            x_2=x_2,
            y_1=y_1,
            y_2=y_2,
        )

    def add_new_parameter(
        self,
        profile_id: int,
        parameter_name: str,
        regex: str,
        x_1: int,
        x_2: int,
        y_1: int,
        y_2: int,
        example: str,
        advanced_option: str,
    ):
        self.main_model.add_new_parameter(
            profile_id=profile_id,
            parameter_name=parameter_name,
            regex=regex,
            x_1=x_1,
            x_2=x_2,
            y_1=y_1,
            y_2=y_2,
            example=example,
            advanced_option=advanced_option,
        )

    def add_new_secondary_parameter(
        self,
        parameter_id: int,
        parameter_name: str,
        x_1: int,
        x_2: int,
        y_1: int,
        y_2: int,
        advanced_option: str,
        comparison_type: str,
    ):
        self.main_model.add_new_secondary_parameter(
            parameter_id=parameter_id,
            parameter_name=parameter_name,
            x_1=x_1,
            x_2=x_2,
            y_1=y_1,
            y_2=y_2,
            advanced_option=advanced_option,
            comparison_type=comparison_type,
        )

    def scrub(self, string_item: str) -> str:
        """Used to clean up OCR results as well as help prevent SQL injection/errors.

        Args:
            string_item (str): string to be cleaned

        Returns:
            str: Initial string with only alpha-numeric, "_", "-", ".", and " " characters remaining
        """
        return self.main_model.scrub(string_item=string_item)

    def update_template_profile_file_name_pattern(
        self, profile_name: str, profile_file_name_pattern: str
    ) -> None:
        self.main_model.update_template_profile_file_name_pattern(
            profile_name, profile_file_name_pattern
        )

    def message_box_handler(
        self,
        callback: typing.Callable,
    ):
        if callback is None:
            return

        callback()

    def update_window_size(self, width: int, height: int):
        self._width, self._height = width, height
        self.window_size_update.emit()

    @property
    def window_size(self):
        return self._width, self._height

    def fetch_all_parameter_rects_and_desc_by_primary_profile_id(self, profile_id: int) -> list[str]:
        return self.main_model.fetch_all_parameter_rectangles_and_description_by_primary_profile_id(
            profile_id
        )

    def fetch_profile_rect_and_desc(self, profile_id: int) -> list[str]:
        return self.main_model.fetch_profile_rectangle_by_profile_id(profile_id)

    def fetch_parameter_rectangle_by_name_and_profile_id(
        self, profile_id: int, parameter_name: str
    ) -> list[int]:
        return self.main_model.fetch_parameter_rectangle_by_name_and_profile_id(
            profile_id=profile_id, parameter_name=parameter_name
        )

    def fetch_parameter_regex_by_parameter_name_and_profile_id(
        self, profile_id: int, parameter_name: str
    ) -> str:
        return self.main_model.fetch_parameter_regex_by_parameter_name_and_profile_id(
            profile_id=profile_id, parameter_name=parameter_name
        )

    def delete_project_data_entry_by_project_number(self, project_number: str) -> None:
        return self.main_model.delete_project_data_entry_by_project_number(
            project_number=project_number
        )

    def update_project_data_entry(self, old_data: dict, new_data: dict) -> str:
        return self.main_model.update_project_data_entry(old_data, new_data)

    def add_new_project_data(self, project_data: dict) -> str:
        return self.main_model.add_new_project_data(new_data=project_data)

    def update_email_profile_names(self, email_profile_names: list[str]) -> None:
        self.email_profiles_updated.emit(email_profile_names)
        return

    def get_local_email_directory(self) -> str | os.PathLike:
        relative_directory = "signatures"
        if not os.path.exists(relative_directory):
            os.makedirs(relative_directory)
        return os.path.abspath(relative_directory)
    
    def get_outlook_email_directory(self) -> str | os.PathLike:
        appdata_path = os.getenv("APPDATA")
        signatures_path = os.path.join(appdata_path, "Microsoft", "Signatures")
        if os.path.exists(signatures_path):
            return signatures_path
        else:
            return ""

    def set_email_profile_by_profile_name(
        self, profile_name: str, email_profile_name: str
    ) -> None:
        profile_id = self.fetch_profile_id_by_profile_name(profile_name=profile_name)
        self.set_email_profile(
            profile_id=profile_id, email_profile_name=email_profile_name
        )

    def set_email_profile(self, profile_id: int, email_profile_name: str) -> None:
        self.main_model.update_email_profile_by_profile_id(
            profile_id=profile_id, email_profile_name=email_profile_name
        )

    def fetch_email_profile_name_by_profile_id(self, profile_id: int) -> str:
        return self.main_model.fetch_email_profile_name_by_profile_id(
            profile_id=profile_id
        )

    def fetch_email_profile_name_by_project_number(self, project_number: str) -> str:
        return self.main_model.fetch_email_profile_name_by_project_number(
            project_number=project_number
        )

    def fetch_email_template_info_by_email_template_name(
        self, email_template_name: str
    ) -> list[str]:
        return self.main_model.fetch_email_template_info_by_email_template_name(
            email_template_name=email_template_name
        )
