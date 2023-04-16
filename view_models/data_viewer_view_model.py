import csv

from PySide6 import QtCore, QtWidgets

from view_models import main_view_model
from widgets import loading_widget


class DataViewerViewModel(QtCore.QObject):
    export_project_data_button_enabled = QtCore.Signal(int)
    data_table_update = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._project_data = None
        self._project_data_headers = None

    def update_data_table(self):
        self._project_data = self.main_view_model.fetch_all_project_data()
        self._project_data_headers = self.main_view_model.fetch_project_data_table_headers()

        # If there is no project_data, dont let the user export nothing.
        if not self._project_data:
            self.export_project_data_button_enabled.emit(False)

        self.data_table_update.emit()

    @property
    def project_data(self) -> list[str]:
        return self._project_data

    @property
    def project_data_headers(self) -> list[str]:
        return self._project_data_headers

    def get_project_data_import_file(self):

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

            message_box_window_title = "Invalid Import File"
            severity_icon = QtWidgets.QMessageBox.Information
            text_body = f"File unable to be read as a csv.\n\n{e}"
            buttons = ["Okay",]
            button_roles = [QtWidgets.QMessageBox.RejectRole,]
            callback = [None,]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }

            self.main_view_model.display_message_box(
                message_box_dict=message_box_dict)

    def import_project_data(self, data_to_import: list[str]):

        # remove headers if present
        while "project_number" in data_to_import[0]:
            data_to_import = data_to_import[1:]

        # Display invalid data to user somehow so they're aware not all data was imported properly
        # valid_data_to_import, _ = self.validate_data(data_to_import)
        valid_data_to_import = data_to_import
        self.main_view_model.main_model.import_result.connect(self.import_data_handler)
        self.main_view_model.import_project_data_thread(project_data=valid_data_to_import)
        
    def import_data_handler(self, error_message: str):
        if not error_message:
            self.update_data_table()
            return
        self.main_view_model.add_console_alerts(1)
        self.main_view_model.add_console_text(f"Import {error_message}")

    def evt_import_complete(self, results):
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
            QtCore.QCoreApplication.translate(
                "MainWindow", "Export Project Data")
        )
        if results and results[0] is not None:
            import_error_dialog = QtWidgets.QMessageBox()
            import_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
            import_error_dialog.setWindowTitle("Project Data Import Error")
            import_error_dialog.setText(
                f"Error when trying to import values into database.\n\n \
                {results[0]}"
            )
            import_error_dialog.exec()
        else:
            self.progress_popup.setValue(100)
            self.database_fetch("project_data")

    def get_project_data_export_location(self):
        
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

    def export_project_data(self, export_location: str):
        self.main_view_model.main_model.export_result.connect(self.export_data_handler)
        self.main_view_model.export_project_data_thread(export_location=export_location)

    def export_data_handler(self, error_message: str):
        self.main_view_model.add_console_alerts(1)
        if not error_message:
            self.main_view_model.add_console_text(f"Export Complete.")
            return
        
        self.main_view_model.add_console_text(f"Export {error_message}")
