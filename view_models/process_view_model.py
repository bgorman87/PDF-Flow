import os

from PySide6 import QtCore, QtWidgets

from functions import analysis
from view_models import main_view_model


class ProcessViewModel(QtCore.QObject):
    processed_files_list_widget_update = QtCore.Signal(
        QtWidgets.QListWidgetItem)
    display_pdf_preview = QtCore.Signal()
    display_file_name = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._file_names = None
        self._selected_file_dir = None
        self._selected_file_name = None
        self._progress = 0
        self._thread_pool = QtCore.QThreadPool()

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
            self.main_view_model.set_process_progress_text(
                "Select Files to Begin...")
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

        self.main_view_model.set_process_button_count(
            f"Process ({len(self._file_names)} Selected)"
        )

        # Signals for this are defined in main_view_model because nav needs the info as well
        self.main_view_model.add_console_text(file_names_string)
        self.main_view_model.add_console_alerts(number_files)
        self.main_view_model.set_loaded_files(number_files)
        self.main_view_model.set_process_button_state(True)
        self.main_view_model.set_process_button_count(number_files)

    # For each file in self._file_names create a thread to process
    def process_files(self):
        """Processes the selected files"""
        self.main_view_model.set_process_progress_text("Processing... %p%")
        # For each file create a new thread to increase performance
        for file_name in self._file_names:
            self.analyze_worker = analysis.WorkerAnalyzeThread(
                file_name=file_name, test=True, analyzed=False, main_view_model=self.main_view_model
            )
            self.analyze_worker.signals.progress.connect(
                self.evt_analyze_progress)
            self.analyze_worker.signals.result.connect(
                self.evt_analyze_complete)
            self._thread_pool.start(self.analyze_worker)
            self.evt_analyze_progress(10)
        self.main_view_model.set_process_button_count(0)

    def list_widget_handler(self, list_widget_item: QtWidgets.QListWidgetItem):
        """Displays the currently selected list widget item"""

        file_dirs = list_widget_item.data(QtCore.Qt.UserRole)
        source_dir = file_dirs["source"].replace("\\", "/")
        # TODO: If doesnt exist remove from list widget and add
        # notice to the console
        # if not os.path.exists(source_dir):
        # self.processed_files_list_widget.takeItem(
        #     self.processed_files_list_widget.currentRow()
        # )
        # self.processed_files_list_widget.setCurrentRow(0)
        # set_text = self.processed_files_list_widget.currentItem().text()
        # self.file_rename_line_edit.setText(set_text)
        # return
        self._selected_file_dir = source_dir
        self.display_pdf_preview.emit()

        self._selected_file_name = list_widget_item.text()
        self.display_file_name.emit()

    @property
    def selected_file_dir(self) -> str:
        return self._selected_file_dir

    @property
    def selected_file_name(self) -> str:
        return self._selected_file_name

    def evt_analyze_progress(self, val: int):
        """Updates main progress bar based off of emitted progress values.

        Args:
            val (int): Current progress level of file being analyzed
        """

        # Since val is progress of each individual file, need to ensure whole progress accounts for all files
        self._progress += val
        self.main_view_model.set_process_progress_value(
            int(self._progress / len(self._file_names)))
        if self._progress >= 100:
            self.main_view_model.set_process_progress_text(
                "Processing Complete.")

    def evt_analyze_complete(self, results: list[str]):
        """Appends processed files list widget with new processed file data

        Args:
            results (list): processed file list
        """
        print_string = results[0]
        file_name = results[1]
        file_path = results[2]
        project_data_dir = results[3]

        file_dirs = {"source": file_path, "project_data": project_data_dir}
        self.main_view_model.add_console_text(print_string)
        processed_files_list_item = QtWidgets.QListWidgetItem(file_name)
        processed_files_list_item.setData(QtCore.Qt.UserRole, file_dirs)
        self.processed_files_list_widget_update.emit(processed_files_list_item)
        self.main_view_model.update_processed_files_count(1)
        self.main_view_model.set_process_button_state(False)
        self.main_view_model.set_process_button_count(0)
