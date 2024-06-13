from email import message
from os import remove
from pyexpat.errors import messages
from PySide6 import QtCore, QtWidgets
from view_models import main_view_model
from utils import general_utils


class SettingsViewModel(QtCore.QObject):
    anonymous_usage_update = QtCore.Signal(bool)
    batch_email_update = QtCore.Signal(bool)
    selected_templates_update = QtCore.Signal(int)
    profile_list_update = QtCore.Signal()
    poppler_path_removed = QtCore.Signal()
    tesseract_path_removed = QtCore.Signal()
    backup_directory_removed = QtCore.Signal()
    email_profile_list_update = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self.active_profiles = None
        self._chosen_templates = []
        self._email_profile_list = self.main_view_model.email_profiles

        self.main_view_model.anonymous_usage_update.connect(self.anonymous_usage_update.emit)
        self.main_view_model.profile_update_list.connect(self.profile_list_update.emit)
        self.main_view_model.batch_email_update.connect(self.batch_email_update.emit)
        self.main_view_model.email_profiles_updated.connect(self.set_email_profile_list)

    def format_file_profile_list(self) -> list[str]:
        """Transforms profiles into a list with profile name and identifier text. profiles list comes from fetch_file_profiles from data_handler.

        Returns:
            list: Items to display in profiles dropdown
        """
        dropdown_items = []
        results = self.main_view_model.fetch_file_profiles_for_settings()
        if results:
            dropdown_items = ["".join([result[0], " - ", result[1]])
                              for result in results]
        return dropdown_items
    
    def get_unique_id(self) -> str:
        """Gets the unique id from the data handler

        Returns:
            str: unique id
        """
        return self.main_view_model.fetch_unique_id()
    
    def toggle_anonymous_usage(self, check_state: bool) -> None:
        """Toggles anonymous usage in the data handler

        Args:
            check_state (bool): True if checked, False if unchecked
        """
        self.main_view_model.toggle_anonymous_usage(check_state)

    def toggle_batch_email(self, check_state: bool) -> None:
        """Toggles batch email in the data handler

        Args:
            check_state (bool): True if checked, False if unchecked
        """
        self.main_view_model.toggle_batch_email(check_state)

    def toggle_onedrive_check(self, check_state: bool) -> None:
        """Toggles onedrive check in the data handler

        Args:
            check_state (bool): True if checked, False if unchecked
        """
        self.main_view_model.toggle_onedrive_check(check_state)

    def get_onedrive_check_state(self) -> bool:
        """Gets the onedrive check state from the data handler

        Returns:
            bool: True if checked, False if unchecked
        """
        return self.main_view_model.fetch_onedrive_check()
        
    def get_anonymous_state(self) -> bool:
        """Gets the anonymous usage state from the data handler

        Returns:
            bool: True if checked, False if unchecked
        """
        return self.main_view_model.fetch_anonymous_usage()
    
    def get_batch_email_state(self) -> bool:
        """Gets the batch email state from the data handler

        Returns:
            bool: True if checked, False if unchecked
        """
        return self.main_view_model.fetch_batch_email()
    
    def template_item_clicked(self, checkbox: QtWidgets.QCheckBox, profile_line: str) -> None:
        """Handles the template item being clicked

        Args:
            state (bool): True if checked, False if unchecked
        """
        state = checkbox.isChecked()
        print("template_item_clicked", state, profile_line)
        if state:
            self._chosen_templates.append(profile_line)
        else:
            self._chosen_templates.remove(profile_line)

        self.selected_templates_update.emit(len(self._chosen_templates))

    def delete_selected_templates_handler(self):
        """Deletes the selected templates from the data handler
        """
        self.profile_template_deletion_dialog = general_utils.MessageBox()
        self.profile_template_deletion_dialog.title = "Delete Template Profiles"
        self.profile_template_deletion_dialog.icon = QtWidgets.QMessageBox.Warning
        self.profile_template_deletion_dialog.text = f"Are you sure you want to delete the selected templates?"
        self.profile_template_deletion_dialog.buttons = [QtWidgets.QPushButton("Yes"), QtWidgets.QPushButton("No")]
        self.profile_template_deletion_dialog.button_roles = [QtWidgets.QMessageBox.YesRole, QtWidgets.QMessageBox.RejectRole]
        self.profile_template_deletion_dialog.callback = [self.delete_selected_templates, None]

        self.main_view_model.display_message_box(message_box=self.profile_template_deletion_dialog)

    def delete_selected_templates(self):

        for profile_line in self._chosen_templates:
            profile_name = profile_line.split(" - ")[0]
            if profile_name:
                profile_id = self.main_view_model.fetch_profile_id_by_profile_name(profile_name)
                self.main_view_model.delete_template_profile(profile_id=profile_id)
            else:
                self.main_view_model.add_console_alerts(1)
                self.main_view_model.add_console_text(f"Settings Error: Unable to determine profile id for selected profile: {profile_line}")
                return

        self._chosen_templates = []
        self.selected_templates_update.emit(len(self._chosen_templates))
        self.main_view_model.profile_update_list.emit()

    def get_backup_directory(self) -> str:
        """Gets the backup directory from the data handler

        Returns:
            str: backup directory
        """
        return self.main_view_model.fetch_backup_directory()
    
    def set_backup_directory(self) -> str:
        """Gets the backup directory from file dialog

        Returns:
            str: backup directory
        """
        backup_dir = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select Backup Directory", ""
        )

        self.main_view_model.set_backup_directory(backup_dir)

        return backup_dir
    
    def remove_backup_directory(self) -> None:
        """Removes the backup directory from the data handler
        """
        self.main_view_model.set_backup_directory("")
        self.backup_directory_removed.emit()

    def get_poppler_path(self) -> str:
        """Gets the poppler path from the data handler

        Returns:
            str: poppler path
        """
        return self.main_view_model.fetch_poppler_path()

    def set_poppler_path(self) -> str:
        """Gets the poppler directory from file dialog

        Returns:
            str: poppler path
        """
        poppler_dir = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select Poppler 'bin' Directory", ""
        )

        self.main_view_model.set_poppler_path(poppler_dir)

        return poppler_dir
    
    def remove_poppler_path(self) -> None:
        """Removes the poppler path from the data handler
        """
        self.main_view_model.set_poppler_path("")
        self.poppler_path_removed.emit()

    def remove_tesseract_path(self) -> None:
        """Removes the tesseract path from the data handler
        """
        self.main_view_model.set_tesseract_path("")
        self.tesseract_path_removed.emit()

    def set_tesseract_path(self) -> str:
        """Gets the tesseract executable from file dialog

        Returns:
            str: tesseract path
        """

        tesseract_path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Tesseract Executable", "", "Tesseract Executable (*.exe)"
        )[0]

        self.main_view_model.set_tesseract_path(tesseract_path)

        return tesseract_path
    
    def get_tesseract_path(self) -> str:
        """Gets the tesseract path from the data handler

        Returns:
            str: tesseract path
        """
        return self.main_view_model.fetch_tesseract_path()
    
    def get_default_email(self) -> str:
        """Gets the default email from the data handler

        Returns:
            str: default email
        """
        return self.main_view_model.fetch_default_email()
    
    def test_tesseract_path(self) -> None:
        """Tests the tesseract path
        """
        
        test_result = self.main_view_model.test_tesseract_path()

        tesseract_path = self.main_view_model.fetch_tesseract_path()
        messages = {}

        if tesseract_path:
            messages["success"] = f"Tesseract path is valid: {tesseract_path}"
            messages["failure"] = f"Tesseract path is invalid: {tesseract_path}"
        else:
            messages["success"] = "Tesseract found in system PATH. You are good to go!"
            messages["failure"] = "Tesseract path is invalid"

        message_box = general_utils.MessageBox()
        message_box.title = "Tesseract Test"
        message_box.icon = QtWidgets.QMessageBox.Information if test_result else QtWidgets.QMessageBox.Warning
        message_box.text = messages["success"] if test_result else messages["failure"]
        message_box.buttons = [QtWidgets.QPushButton("OK")]
        message_box.button_roles = [QtWidgets.QMessageBox.AcceptRole]
        message_box.callback = [None]

        self.main_view_model.display_message_box(message_box=message_box)

    def test_poppler_path(self) -> None:
        """Tests the poppler path
        """
        test_result = self.main_view_model.test_poppler_path()
        poppler_path = self.main_view_model.fetch_poppler_path()
        messages = {}

        if poppler_path:
            messages["success"] = f"Poppler path is valid: {poppler_path}"
            messages["failure"] = f"Poppler path is invalid: {poppler_path}"
        else:
            messages["success"] = "Poppler found in system PATH. You are good to go!"
            messages["failure"] = "Poppler path is invalid"

        message_box = general_utils.MessageBox()
        message_box.title = "Poppler Test"
        message_box.icon = QtWidgets.QMessageBox.Information if test_result else QtWidgets.QMessageBox.Warning
        message_box.text = messages["success"] if test_result else messages["failure"]
        message_box.buttons = [QtWidgets.QPushButton("OK")]
        message_box.button_roles = [QtWidgets.QMessageBox.AcceptRole]
        message_box.callback = [None]

        self.main_view_model.display_message_box(message_box=message_box)

    def import_database_handler(self):
        """Imports the database from file dialog
        """

        message = (
            "WARNING: This import process will store all existing data into an 'archived' file and use the data "
            "from the imported file to populate the program. This includes templates, filenames, and project data.\n\n"
            "Are you sure you want to proceed with the import?"
        )
        self.database_import_dialog = general_utils.MessageBox()
        self.database_import_dialog.title = "Import Database"
        self.database_import_dialog.icon = QtWidgets.QMessageBox.Information
        self.database_import_dialog.text = message
        self.database_import_dialog.buttons = [QtWidgets.QPushButton("Yes"), QtWidgets.QPushButton("No")]
        self.database_import_dialog.button_roles = [QtWidgets.QMessageBox.YesRole, QtWidgets.QMessageBox.RejectRole]
        self.database_import_dialog.callback = [self.import_database, None]

        self.main_view_model.display_message_box(message_box=self.database_import_dialog)

    def import_database(self):
        """Imports the database from file dialog
        """
        database_path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Database File", "", "Database File (*.sqlite3)"
        )[0]
        if not database_path:
            return
        
        self.main_view_model.import_database(database_path)

    def update_default_email(self, email: str) -> None:
        """Updates the default email in the data handler

        Args:
            email (str): email address
        """
        self.main_view_model.set_default_email(email)

    def set_email_profile_list(self, email_profiles: list[str]) -> None:
        """Sets the email profile list"""

        self._email_profile_list = email_profiles
        self.email_profile_list_update.emit()
    
    @property
    def email_profile_list(self) -> list[str]:
        """list[str]: Returns the email profile list"""

        return self._email_profile_list    