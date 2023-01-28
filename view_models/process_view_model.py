import os

from PySide6 import QtCore, QtWidgets

from view_models import main_view_model


class ProcessViewModel(QtCore.QObject):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._file_names = None

    def get_files(self):
        """Opens a file dialog to select files for input"""
        # When clicking Select Files, clear any previously selected files, and reset the file status box
        self._file_names = None
        self.main_view_model.set_loaded_files(0)

        self._file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            caption="Select Files to Process", filter="PDF (*.pdf)"
        )

        self.main_view_model.set_process_progress_value(0)
        if not self._file_names:
            self.main_view_model.set_process_button_state(False)
            self.main_view_model.set_process_progress_text("Select Files to Begin...")
            return

        self.main_view_model.set_process_progress_text(
            "Press 'Process' Button to Start Processing Files..."
        )

        number_files = len(self._file_names)

        file_names_string = f"New Selection of ({number_files}) file"
        if number_files == 0:
            file_names_string += ":"
        else:
            file_names_string += "s:"

        for item in self._file_names:
            file_names_string += f"\n{item}"

        # TODO: make these signals just occur here to not make main_view_model so confusing and loaded with signals
        # also make all the values needed @property and stoee them locally in private variables similar to settings_view_model
        self.main_view_model.set_process_button_count(
            f"Process ({len(self._file_names)} Selected)"
        )
        self.main_view_model.add_console_text(file_names_string)
        self.main_view_model.add_console_alerts(number_files)
        self.main_view_model.set_loaded_files(number_files)
        self.main_view_model.set_process_button_state(True)
        self.main_view_model.set_process_button_count(number_files)
