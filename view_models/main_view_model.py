from cgi import test
import os
import typing

from PySide6 import QtCore, QtWidgets, QtGui
import threading
import subprocess
from models import main_model
from utils.general_utils import MessageBox, set_config_data, is_onedrive_running
from utils.text_utils import post_telemetry_data
from shutil import copyfile, move
from datetime import datetime


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
    email_button_state_update = QtCore.Signal()
    process_button_count_update = QtCore.Signal()
    window_size_update = QtCore.Signal()
    profile_update_list = QtCore.Signal()
    parameter_update_list = QtCore.Signal()
    email_profiles_updated = QtCore.Signal(list)
    anonymous_usage_update = QtCore.Signal(bool)
    batch_email_update = QtCore.Signal(bool)
    backup_data = QtCore.Signal(str)
    project_data_update = QtCore.Signal()

    def __init__(self, main_model: main_model.MainModel, config: dict = None):
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
        self.process_button_state = False
        self.email_button_state = False
        self.process_button_count = 0
        self.os = os.sys.platform
        self.version = config["version"]
        self._telemetry_id = config["telemetry"]["identifier"] if not config["telemetry"]["annonymous"] else None
        self.config = config
        self.window_icon = QtGui.QIcon()
        self._email_profiles = None

    def on_close(self):
        backup_location = self.fetch_backup_directory()
        if not backup_location: 
            return
        project_data_backup_location = os.path.abspath(os.path.join(backup_location, "project_data.csv"))
        database_backup_location = os.path.abspath(os.path.join(backup_location, "db.sqlite3"))
        database_current_location = os.path.abspath(os.path.join(os.getcwd(), 'database', 'db.sqlite3'))
        copyfile(database_current_location, database_backup_location)
        self.backup_data.emit(project_data_backup_location)

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

    def set_email_button_state(self, state: bool) -> None:
        self.email_button_state = state
        self.email_button_state_update.emit()

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
        self._email_profiles = email_profile_names
        self.email_profiles_updated.emit(email_profile_names)
        return
    
    @property
    def email_profiles(self) -> list[str]:
        return self._email_profiles

    def get_local_email_directory(self) -> str | os.PathLike:
        relative_directory = "signatures"
        if not os.path.exists(relative_directory):
            os.makedirs(relative_directory)
        return os.path.abspath(relative_directory)
    
    def get_outlook_email_directory(self) -> str | os.PathLike:
        appdata_path = os.getenv("APPDATA")
        signatures_path = os.path.abspath(os.path.join(appdata_path, "Microsoft", "Signatures"))
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

    def send_telemetry_data(self, quantity: int):
        """Sends telemetry data to the API Gateway endpoint in a separate thread.

        Args:
            quantity (int): The quantity of telemetry data to send.
        """
        def telemetry_thread():
            response = post_telemetry_data(usage_count=quantity, identifier=self._telemetry_id)
            if response is None:
                self.config["telemetry"]["pending"] = self.config["telemetry"]["pending"] + quantity
                set_config_data(self.config)
                
        telemetry_thread = threading.Thread(target=telemetry_thread)
        telemetry_thread.start()

    def fetch_unique_id(self) -> str:
        return self._telemetry_id
    
    def set_unique_id(self, new_id: str) ->  bool:
        
        if new_id : 
            self._telemetry_id = str(new_id)
            return True
        
        return False
    
    def toggle_anonymous_usage(self, check_state: bool) -> None:

        self.config["telemetry"]["annonymous"] = check_state
        if check_state:
            self._telemetry_id = None
        else:
            self._telemetry_id = self.config["telemetry"]["identifier"]
        self.anonymous_usage_update.emit(check_state)
        set_config_data(self.config)
        
        return
    
    def toggle_onedrive_check(self, check_state: bool) -> None:
        self.config["onedrive_check"] = check_state
        set_config_data(self.config)
        return
    
    def fetch_onedrive_check(self) -> bool:
        return self.config["onedrive_check"]
    
    def fetch_anonymous_usage(self) -> bool:
        return self.config['telemetry']['annonymous']
    
    def fetch_batch_email(self) -> bool:
        try:
            return self.config['batch-email']
        except KeyError:
            self.config['batch-email'] = False
            set_config_data(self.config)
            return self.config['batch-email']
    
    def toggle_batch_email(self, check_state: bool) -> None:
        self.config['batch-email'] = check_state
        set_config_data(self.config)
        self.batch_email_update.emit(check_state)
        return
    
    def fetch_backup_directory(self) -> str:
        try:
            return self.config['backup_directory']
        except KeyError:
            self.config['backup_directory'] = ""
            set_config_data(self.config)
            return self.config['backup_directory']
        
    def set_backup_directory(self, directory: str) -> None:
        self.config['backup_directory'] = directory
        set_config_data(self.config)
        return
    
    def set_poppler_path(self, path: str) -> None:
        self.config["poppler_path"] = path
        set_config_data(self.config)
        return
    
    def fetch_poppler_path(self) -> str:
        return self.config["poppler_path"]
    
    def set_tesseract_path(self, path: str) -> None:
        self.config["tesseract_path"] = path
        set_config_data(self.config)
        return
    
    def fetch_tesseract_path(self) -> str:
        return self.config["tesseract_path"]
    
    def set_default_email(self, profile_name: str):
        self.config["default_email"] = profile_name
        set_config_data(self.config)
        return
    
    def fetch_default_email(self) -> str:
        return self.config["default_email"]
    
    def test_tesseract_path(self) -> bool:
        try:
            # Run 'tesseract --version' command
            tesseract_path = self.fetch_tesseract_path()
            
            # Get tess parent dir
            parent_dir = os.path.dirname(tesseract_path)

            result = subprocess.run([os.path.join(parent_dir, 'tesseract'), "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
            
            # If the command was successful, 'tesseract v...' should be in the output
            return 'tesseract v' in result.stderr.decode('utf-8') or 'tesseract v' in result.stdout.decode('utf-8')
        except Exception as e:
            print(f"An error occurred while testing Tesseract path: {e}")
            return False
        
    def test_poppler_path(self) -> bool:
        try:
            # Run 'pdfinfo' command
            poppler_path = self.fetch_poppler_path()

            result = subprocess.run([os.path.join(poppler_path, "pdfinfo"), "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
            
            # If the command was successful, 'pdfinfo' should be in the output
            return 'pdfinfo' in result.stderr.decode('utf-8') or 'pdfinfo' in result.stdout.decode('utf-8')
        except Exception as e:
            print(f"An error occurred while testing Poppler path: {e}")
            return False
    
    def onedrive_check(self):
        """Checks if OneDrive is currently running. If so it prompts the user to Pause syncing to avoid any file conflicts.
        """

        if self.config.get("onedrive_check") and is_onedrive_running():
            message_box = MessageBox(
                title="OneDrive Syncing",
                text="OneDrive is currently running. Please pause syncing to avoid any file conflicts.",
                button_roles=["Close",],
                callback=[None,],
            )
            message_box = MessageBox()
            message_box.title = "OneDrive Syncing"
            message_box.icon = QtWidgets.QMessageBox.Warning
            message_box.text = "OneDrive detected as running. If possible pause syncing while using PDF Flow to speed up processing and avoid any file conflicts."
            message_box.buttons = ["Close",]
            message_box.button_roles = [
                QtWidgets.QMessageBox.RejectRole,
            ]
            message_box.callback = [None,]
            self.message_box_alert.emit(message_box)
    
    def import_database(self, database_path: str):
        current_database = os.path.abspath(os.path.join(os.getcwd(), "database", "db.sqlite3"))
        new_directory = os.path.join("database", "old")

        os.makedirs(new_directory, exist_ok=True)
        
        date_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, extension = os.path.splitext(os.path.basename(current_database))
        
        new_filename = f"{filename}_{date_time_str}{extension}"
        new_path = os.path.join(new_directory, new_filename)
        
        move(current_database, new_path)
        copyfile(database_path, current_database)

        self.profile_update_list.emit()
        self.parameter_update_list.emit()
        self.project_data_update.emit()