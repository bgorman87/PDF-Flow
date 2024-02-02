import csv

from PySide6 import QtCore, QtWidgets
from typing import List
from view_models import main_view_model
from utils import general_utils


class DataViewerViewModel(QtCore.QObject):
    export_project_data_button_enabled = QtCore.Signal(int)
    data_table_index_update = QtCore.Signal(int)
    data_table_update = QtCore.Signal()
    project_data_entry_deleted = QtCore.Signal()
    email_profile_list_update = QtCore.Signal()
    all_project_data_deleted = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._project_data = None
        self._project_data_headers = None
        self._project_data_loaded_id = None
        self._email_profiles_list = None
        self.main_view_model.email_profiles_updated.connect(self.set_email_profile_list)

    def update_data_table(self) -> None:
        """Updates the data table with the latest project data."""
        self._project_data = self.main_view_model.fetch_all_project_data()
        self._project_data_headers = (
            self.main_view_model.fetch_project_data_table_headers()
        )
        # If there is no project_data, dont let the user export nothing.
        if not self._project_data:
            self.export_project_data_button_enabled.emit(False)

        self.data_table_update.emit()

    @property
    def project_data(self) -> list[str]:
        """List[str]: Returns the current project data."""
        return self._project_data

    @property
    def project_data_headers(self) -> list[str]:
        """List[str]: Returns the headers for the current project data."""
        return self._project_data_headers

    @property
    def project_data_loaded_id(self) -> int:
        """int: Returns the loaded project data's ID."""
        return self._project_data_loaded_id

    def get_project_data_import_file(self) -> None:
        """Opens a file dialog for the user to select a CSV file and initiates its import."""
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            caption="Open Project Data File",
            dir="../../",
            filter="Comma Seperated Values (*.csv *.txt)",
        )

        if not file_name:
            return

        try:
            with open(file_name, "r") as imported_file:
                reader = csv.reader(imported_file)
                data_to_import = []
                for row in reader:
                    data_to_import.append(row)
            self.import_project_data(data_to_import=data_to_import)
        except csv.Error as e:
            message_box = general_utils.MessageBox()
            message_box.title = "Invalid Import File"
            message_box.icon = QtWidgets.QMessageBox.Information
            message_box.text = f"File unable to be read as a csv.\n\n{e}"
            message_box.buttons = [
                "Okay",
            ]
            message_box.button_roles = [
                QtWidgets.QMessageBox.RejectRole,
            ]
            message_box.callback = [
                None,
            ]

            self.main_view_model.display_message_box(message_box=message_box)

    def import_project_data(self, data_to_import: List[str]) -> None:
        """Imports the project data and initiates necessary threads to handle the import.

        Args:
            data_to_import (List[str]): Data rows to be imported.
        """
        while "project_number" in data_to_import[0]:
            data_to_import = data_to_import[1:]

        # Display invalid data to user somehow so they're aware not all data was imported properly
        # valid_data_to_import, _ = self.validate_data(data_to_import)
        valid_data_to_import = data_to_import
        self.main_view_model.main_model.import_result.connect(self.import_data_handler)
        self.main_view_model.import_project_data_thread(
            project_data=valid_data_to_import
        )

    def import_data_handler(self, error_message: str) -> None:
        """Handles the result of the data import process.

        Args:
            error_message (str): Any error messages received from the import process.
        """
        if not error_message:
            self.update_data_table()
            return
        self.main_view_model.add_console_alerts(1)
        self.main_view_model.add_console_text(f"Import {error_message}")

    def evt_import_complete(self, results) -> None:
        """Displays error message to user if one is present in results otherwise does nothing.

        Args:
            results (list): return message
        """
        self.importing = False
        self.process_button.setEnabled(True)
        self.process_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Process Files")
        )
        self.export_project_data_button.setEnabled(True)
        self.export_project_data_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Export Project Data")
        )
        if results and results[0] is not None:
            import_error_dialog = QtWidgets.QMessageBox()
            import_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
            import_error_dialog.setWindowTitle("Project Data Import Error")
            import_error_dialog.setWindowIcon(self.windowIcon())
            import_error_dialog.setText(
                f"Error when trying to import values into database.\n\n \
                {results[0]}"
            )
            import_error_dialog.exec()
        else:
            self.progress_popup.setValue(100)
            self.database_fetch("project_data")

    def get_project_data_export_location(self) -> None:
        """Opens a file dialog for user to select a location to export the project data to."""
        export_location = QtWidgets.QFileDialog.getSaveFileName(
            caption="Export Project Data",
            dir="../../",
            filter="Comma Seperated Values (*.csv)",
        )

        if not export_location:
            return

        export_location = export_location[0]
        if not export_location.endswith(".csv"):
            export_location += ".csv"

        self.export_project_data(export_location=export_location)

    def export_project_data(self, export_location: str) -> None:
        """Initiates the export of the project data to the specified location."""
        self.main_view_model.main_model.export_result.connect(self.export_data_handler)
        self.main_view_model.export_project_data_thread(export_location=export_location)

    def export_data_handler(self, error_message: str) -> None:
        """Handles the result of the data export process."""
        self.main_view_model.add_console_alerts(1)
        if not error_message:
            self.main_view_model.add_console_text(f"Export Complete.")
            return

        self.main_view_model.add_console_text(f"Export {error_message}")

    def delete_all_project_data_verification(self) -> None:
        """Verifies that the user wants to delete all project data."""

        message_box = general_utils.MessageBox()
        message_box.title = "Delete Project Data"
        message_box.icon = QtWidgets.QMessageBox.Warning
        message_box.text = f"It is advised to backup your project data via exporting before deleting.\n\n\
        Are you sure you want to delete all project data?"
        message_box.buttons = ["Delete", "Cancel"]
        message_box.button_roles = [
            QtWidgets.QMessageBox.YesRole,
            QtWidgets.QMessageBox.NoRole,
        ]
        message_box.callback = [self.delete_all_project_data, None]

        self.main_view_model.display_message_box(message_box=message_box)

    def delete_all_project_data(self) -> None:
        """Initiates the deletion of all project data."""

        self.main_view_model.main_model.delete_result.connect(
            self.delete_all_project_data_handler
        )
        self.main_view_model.delete_all_project_data_thread()

    def delete_all_project_data_handler(self, error_message: str) -> None:
        """Handles the result of the data deletion process."""

        self.main_view_model.add_console_alerts(1)
        if not error_message:
            self.main_view_model.add_console_text(
                f"Deletion of all project data complete."
            )
            self.update_data_table()
            self.all_project_data_deleted.emit()
            return
        self.main_view_model.add_console_text(f"Delete {error_message}")

    def delete_project_data_entry_verification(self, project_data: dict) -> None:
        """Verifies that the user wants to delete the specified project data entry."""

        message_box = general_utils.MessageBox()
        message_box.title = "Delete Project Data"
        message_box.icon = QtWidgets.QMessageBox.Warning
        message_box.text = f"Are you sure you want to delete project data for project: {project_data['project_number']}?"
        message_box.buttons = ["Delete", "Cancel"]
        message_box.button_roles = [
            QtWidgets.QMessageBox.YesRole,
            QtWidgets.QMessageBox.NoRole,
        ]
        message_box.callback = [
            lambda: self.delete_project_data_entry(project_data),
            None,
        ]

        self.main_view_model.display_message_box(message_box=message_box)

    def delete_project_data_entry(self, project_data: dict) -> None:
        """Initiates the deletion of the specified project data entry."""

        result = self.main_view_model.delete_project_data_entry_by_project_number(
            project_data["project_number"]
        )

        if result is not None:
            message_box = general_utils.MessageBox()
            message_box.title = "Delete Project Data"
            message_box.icon = QtWidgets.QMessageBox.Warning
            message_box.text = f"There was an error deleting project data for project: {project_data['project_number']}\n\n{result}"
            message_box.buttons = ["Close"]
            message_box.button_roles = [QtWidgets.QMessageBox.YesRole]
            message_box.callback = [None]

            self.main_view_model.display_message_box(message_box=message_box)
        else:
            self.project_data_entry_deleted.emit()
            self.update_data_table()

    def get_next_visible_row_index(
        self, current_row_index: int, table_widget: QtWidgets.QTableWidget
    ) -> int:
        """Get the next visible row index from the current index, with priority to previous row. Takes into account active filter.

        Args:
            current_index (int): current row index
            table_widget (QtWidgets.QTableWidget): Table widget to check

        Returns:
            int: row index
        """

        total_rows = table_widget.rowCount()

        # Find closest visible row by checking row visibility from current row to start of table
        # If no visible rows found, check from current row to end of table
        for i in range(current_row_index - 1, -1, -1):
            if table_widget.isRowHidden(i):
                continue
            return i

        for i in range(current_row_index + 1, total_rows):
            if table_widget.isRowHidden(i):
                continue
            return i

        return -1

    def database_populate_project_edit_fields(
        self, data_table: QtWidgets.QTableWidget
    ) -> None:
        # self.database_save_edited_project_data_button.setText("Save Changes")
        # self.database_save_edited_project_data_button.clicked.disconnect()
        # self.database_save_edited_project_data_button.clicked.connect(
        #     self.database_save_edited_project_data
        # )
        # If user is creating a new entry and they decide to click away into the table.
        # Just discard changes and load data from the table
        # if self.adding_new:
        #     # If user clicks a new row, reset the save new/save changes button
        #     self.project_data_changed = False
        #     if self.project_data_loaded_id is not None:
        #         self.data_table_index_update.emit(self.project_data_loaded_id)
        #     self.adding_new = False

        # self.database_delete_project_data_button.setEnabled(True)
        # if self.project_data_loaded_id == data_table.selectionModel().currentIndex():
        #     return

        # If user edited the project data ask if they want to discard or cancel
        # if self.project_data_changed:
        #     overwrite = QtWidgets.QMessageBox()
        #     overwrite.setIcon(QtWidgets.QMessageBox.Warning)
        #     overwrite.setWindowTitle("Project Data Changed")
        #     overwrite.setText(
        #         f"Project Data has been changed.\
        #             \n \
        #             \nPress 'Proceed' to discard changes\
        #             \nPress 'Cancel' to go back"
        #     )
        #     overwrite.addButton("Proceed", QtWidgets.QMessageBox.YesRole)
        #     overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        #     overwrite_reply = overwrite.exec()
        #     if overwrite_reply != 0:
        #         return

        self._project_data_loaded_id = data_table.selectionModel().currentIndex()

        # if project data not changed then load data
        # self.database_discard_edited_project_data()

    def database_save_edited_project_data(
        self, old_data: dict, project_data: dict
    ) -> None:
        """Saves the edited project data to the database."""

        update_return = self.main_view_model.update_project_data_entry(
            old_data, project_data
        )

        if update_return is not None:
            message_box = general_utils.MessageBox()
            message_box.title = "Update Project Data Error"
            message_box.icon = QtWidgets.QMessageBox.Warning
            message_box.text = f"There was an error updating project data for project: {project_data['project_number']}\n\n{update_return}"
            message_box.buttons = ["Close"]
            message_box.button_roles = [QtWidgets.QMessageBox.YesRole]
            message_box.callback = [None]

            self.main_view_model.display_message_box(message_box=message_box)
        else:
            self.update_data_table()

    def database_save_new_project_data(self, project_data: dict) -> None:
        """Saves the new project data to the database."""

        insert_return = self.main_view_model.add_new_project_data(project_data)

        if insert_return is not None:
            message_box = general_utils.MessageBox()
            message_box.title = "Insert Project Data Error"
            message_box.icon = QtWidgets.QMessageBox.Warning
            message_box.text = f"There was an error inserting project data for project: {project_data['project_number']}\n\n{insert_return}"
            message_box.buttons = ["Close"]
            message_box.button_roles = [QtWidgets.QMessageBox.YesRole]
            message_box.callback = [None]

            self.main_view_model.display_message_box(message_box=message_box)
        else:
            self.update_data_table()

    def display_warning_message(self, message: str) -> None:
        """Displays a warning message to the user."""

        message_box = general_utils.MessageBox()
        message_box.title = "Warning"
        message_box.icon = QtWidgets.QMessageBox.Warning
        message_box.text = f"{message}"
        message_box.buttons = ["Close"]
        message_box.button_roles = [QtWidgets.QMessageBox.YesRole]
        message_box.callback = [None]

        self.main_view_model.display_message_box(message_box=message_box)

    def set_email_profile_list(self, email_profiles: list[str]) -> None:
        """Sets the email profile list"""

        self._email_profile_list = email_profiles
        self.email_profile_list_update.emit()

    @property
    def email_profile_list(self) -> list[str]:
        """list[str]: Returns the email profile list"""

        return self._email_profile_list

    def display_tooltip(self, text: str) -> None:
        """Displays a tooltip to the user."""

        message_box = general_utils.MessageBox()
        message_box.title = "Email Information"
        message_box.icon = QtWidgets.QMessageBox.Information
        message_box.text = f"{text}"
        message_box.buttons = ["Close"]
        message_box.button_roles = [QtWidgets.QMessageBox.YesRole]
        message_box.callback = [None]

        self.main_view_model.display_message_box(message_box=message_box)
