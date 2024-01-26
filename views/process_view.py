from PySide6 import QtCore, QtGui, QtWebEngineCore, QtWebEngineWidgets, QtWidgets

from utils.enums import EmailProvider
from utils.path_utils import resource_path
from view_models import process_view_model
from widgets import utility_widgets
from widgets.utility_widgets import HorizontalLine


class ProcessView(QtWidgets.QWidget):
    def __init__(self, view_model: process_view_model.ProcessViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()

        self.input_tab_action_buttons = QtWidgets.QHBoxLayout()
        # Action buttons on Input tab
        # self.import_files = QtWidgets.QPushButton()
        # self.import_files.clicked.connect(self.get_files)
        # self.import_files.setObjectName("Select_files")
        # self.dialog = QtWidgets.QFileDialog()
        # self.input_tab_action_buttons.addWidget(self.import_files)

        self.import_files = QtWidgets.QPushButton()
        self.import_files.setMaximumSize(QtCore.QSize(28, 28))
        icon = QtGui.QIcon()
        icon.addFile(resource_path(u"assets/icons/import.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.import_files.setIcon(icon)
        self.import_files.setProperty("class", "invert-icon")
        self.import_files.setObjectName("import_files")
        self.import_files.setToolTip("Import Files")
        self.import_files.setIconSize(QtCore.QSize(12, 12))
        self.import_files.setCheckable(False)
        self.import_files.clicked.connect(self.get_files)
        self.input_tab_action_buttons.addWidget(self.import_files)

        self.input_tab_action_buttons.addSpacing(10)

        # Action button to select all files
        self.select_all = QtWidgets.QPushButton()
        self.select_all.setMaximumSize(QtCore.QSize(28, 28))
        icon = QtGui.QIcon()
        icon.addFile(resource_path(u"assets/icons/select_all.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.select_all.setIcon(icon)
        self.select_all.setProperty("class", "invert-icon")
        self.select_all.setObjectName("select_all")
        self.select_all.setToolTip("Select All")
        self.select_all.setIconSize(QtCore.QSize(12, 12))
        self.select_all.setCheckable(False)
        self.select_all.clicked.connect(lambda: self.view_model.check_selection(True))
        self.input_tab_action_buttons.addWidget(self.select_all)

        # Action button to deselect all files
        self.deselect_all = QtWidgets.QPushButton()
        self.deselect_all.setMaximumSize(QtCore.QSize(28, 28))
        icon = QtGui.QIcon()
        icon.addFile(resource_path(u"assets/icons/deselect_all.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.deselect_all.setIcon(icon)
        self.deselect_all.setProperty("class", "invert-icon")
        self.deselect_all.setObjectName("deselect_all")
        self.deselect_all.setToolTip("Deselect All")
        self.deselect_all.setIconSize(QtCore.QSize(12, 12))
        self.deselect_all.setCheckable(False)
        self.deselect_all.clicked.connect(lambda: self.view_model.check_selection(False))
        self.input_tab_action_buttons.addWidget(self.deselect_all)

        # Action button to delete selected files
        self.delete = QtWidgets.QPushButton()
        self.delete.setMaximumSize(QtCore.QSize(28, 28))
        icon = QtGui.QIcon()
        icon.addFile(resource_path(u"assets/icons/delete.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delete.setIcon(icon)
        self.delete.setProperty("class", "invert-icon")
        self.delete.setObjectName("delete")
        self.delete.setToolTip("Remove Selected")
        self.delete.setIconSize(QtCore.QSize(12, 12))
        self.delete.setCheckable(False)
        self.delete.clicked.connect(self.view_model.remove_selected_files)
        self.input_tab_action_buttons.addWidget(self.delete)
        self.view_model.remove_selected_items.connect(self.remove_deleted_rows)

        self.input_tab_action_buttons.addStretch()

        self.process_button = QtWidgets.QPushButton()
        self.process_button.setMaximumSize(QtCore.QSize(28, 28))
        icon = QtGui.QIcon()
        icon.addFile(resource_path(u"assets/icons/process.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.process_button.setIcon(icon)
        self.process_button.setProperty("class", "invert-icon")
        self.process_button.setObjectName("analyze_button")
        self.process_button.setToolTip("Process Selected Files")
        self.process_button.setIconSize(QtCore.QSize(12, 12))
        self.process_button.setCheckable(False)
        self.process_button.clicked.connect(self.view_model.process_files)
        self.process_button.setEnabled(False)
        self.view_model.main_view_model.process_button_state_update.connect(
            lambda: self.process_button.setEnabled(
                self.view_model.main_view_model.process_button_state
            )
        )
        # self.view_model.main_view_model.process_button_count_update.connect(
        #     lambda: self.process_button_text_update(
        #         self.view_model.main_view_model.process_button_count
        #     )
        # )
        self.input_tab_action_buttons.addWidget(self.process_button)

        # # Action button to start file analysis
        # self.process_button = QtWidgets.QPushButton()
        # self.process_button.clicked.connect(self.view_model.process_files)
        # self.process_button.setObjectName("analyze_button")
        # self.process_button.setEnabled(False)
        # self.view_model.main_view_model.process_button_state_update.connect(
        #     lambda: self.process_button.setEnabled(
        #         self.view_model.main_view_model.process_button_state
        #     )
        # )
        # self.view_model.main_view_model.process_button_count_update.connect(
        #     lambda: self.process_button_text_update(
        #         self.view_model.main_view_model.process_button_count
        #     )
        # )
        # self.input_tab_action_buttons.addWidget(self.process_button)

        # Action button to start email process
        self.email_button = QtWidgets.QPushButton()
        self.email_button.setMaximumSize(QtCore.QSize(30, 28))
        icon = QtGui.QIcon()
        icon.addFile(resource_path(u"assets/icons/email.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.email_button.setIcon(icon)
        self.email_button.setProperty("class", "invert-icon")
        self.email_button.setObjectName("email_button")
        self.email_button.setToolTip("Email Selected Files")
        self.email_button.setIconSize(QtCore.QSize(24, 18))
        self.email_button.setCheckable(False)
        self.email_button.setEnabled(False)

        self.view_model.main_view_model.email_button_state_update.connect(
            lambda: self.email_button.setEnabled(
                self.view_model.main_view_model.email_button_state
            )
        )

        self.email_button.clicked.connect(self.email_unprocessed_processed_handler)
        self.input_tab_action_buttons.addWidget(self.email_button)

        # self.email_button = QtWidgets.QPushButton()
        # self.email_button.clicked.connect(self.email_unprocessed_processed_handler)
        # self.email_button.setObjectName("email_button")
        # self.email_button.setEnabled(False)
        # self.input_tab_action_buttons.addWidget(self.email_button)

        # # Drop list box to choose analysis type (Live/Test)
        # # Live uses real client info, test uses dummy/local info
        # self.test_box = QtWidgets.QComboBox()
        # self.test_box.setObjectName("test_box")
        # self.test_box.setEditable(True)
        # self.test_box.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # self.test_box.addItems(["Test", "Live"])
        # self.test_box.setEditable(False)
        # self.input_tab_action_buttons.addWidget(self.test_box)

        self.main_layout.addLayout(self.input_tab_action_buttons)

        # Table to hold all of the files
        self.files_table = utility_widgets.MyTableWidget()
        self.files_table.setObjectName("files_table")
        self.files_table.setColumnCount(4)
        self.files_table.setRowCount(0)

        self.header_select = QtWidgets.QTableWidgetItem()
        self.files_table.setHorizontalHeaderItem(0, self.header_select)

        self.header_file_name = QtWidgets.QTableWidgetItem()
        self.header_file_name.setText("File Name")
        self.files_table.setHorizontalHeaderItem(1, self.header_file_name)

        self.header_processed = QtWidgets.QTableWidgetItem()
        self.header_processed.setText("Processed")
        self.files_table.setHorizontalHeaderItem(2, self.header_processed)

        self.header_email = QtWidgets.QTableWidgetItem()
        self.header_email.setText("Emailed")
        self.files_table.setHorizontalHeaderItem(3, self.header_email)

        self.files_table.setSortingEnabled(True)
        self.files_table.setSelectionMode(QtWidgets.QTableWidget.SingleSelection)
        self.files_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        header = self.files_table.horizontalHeader()

        # Set the first column to resize to its contents
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

        # Set the second column to stretch
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        # Set the remaining columns to resize to their contents
        for i in range(2, self.files_table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)

        self.files_table.currentItemChanged.connect(
            lambda: self.view_model.table_widget_handler(
                self.files_table.item(self.files_table.currentRow(), 1)
            )
        )

        self.files_table.itemChanged.connect(self.table_state_handler)

        self.view_model.active_files_update.connect(self.update_table_data)

        self.main_layout.addWidget(self.files_table)

        # Add splitter to separate analyzed files from file preview

        # # Widget to hold analyzed files
        # self.processed_files_list_widget = QtWidgets.QListWidget()
        # self.processed_files_list_widget.setSelectionMode(
        #     QtWidgets.QAbstractItemView.SingleSelection
        # )
        # self.processed_files_list_widget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        # self.processed_files_list_widget.setObjectName("processed_files_list_widget")
        # self.main_layout.addWidget(self.processed_files_list_widget)
        # self.main_layout.setStretch(
        #     self.main_layout.indexOf(self.processed_files_list_widget), 2
        # )
        # self.view_model.processed_files_list_widget_update.connect(
        #     self.add_processed_list_widget_item
        # )

        # # Lines within the analyzed files widget above
        # self.processed_files_list_item = QtWidgets.QListWidgetItem()
        # self.processed_files_list_widget.itemClicked.connect(
        #     lambda: self.view_model.list_widget_handler(
        #         self.processed_files_list_widget.currentItem()
        #     )
        # )
        # self.processed_files_list_widget.itemDoubleClicked.connect(
        #     self.rename_file_handler
        # )

        self.file_rename_layout = QtWidgets.QHBoxLayout()
        # Text editor line to edit file names
        self.file_rename_line_edit = QtWidgets.QLineEdit()
        self.file_rename_line_edit.setObjectName("file_rename_line_edit")
        self.view_model.display_file_name.connect(self.display_file_name)
        self.file_rename_layout.addWidget(self.file_rename_line_edit)
        self.file_rename_layout.setStretch(
            self.file_rename_layout.indexOf(self.file_rename_line_edit), 5
        )

        # Action button to call rename function
        self.file_rename_button = QtWidgets.QPushButton()
        self.file_rename_button.clicked.connect(self.file_rename_button_handler)
        self.file_rename_button.setObjectName("file_rename_button")
        self.file_rename_layout.addWidget(self.file_rename_button)
        self.file_rename_layout.setStretch(
            self.file_rename_layout.indexOf(self.file_rename_button), 1
        )

        self.main_layout.addLayout(self.file_rename_layout)

        # Title for JPG/PDF preview below
        self.file_preview_label = QtWidgets.QLabel()
        self.file_preview_label.setGeometry(QtCore.QRect(10, 140, 100, 16))
        self.file_preview_label.setObjectName("file_preview_label")
        self.main_layout.addWidget(self.file_preview_label)

        # Displays PDF
        self.file_preview = QtWebEngineWidgets.QWebEngineView()
        _qtweb_settings = QtWebEngineCore.QWebEngineSettings
        self.file_preview.settings().setAttribute(_qtweb_settings.PluginsEnabled, True)
        # self.file_preview.settings().setAttribute(_qtweb_settings.WebGLEnabled, True)
        self.file_preview.settings().setAttribute(
            _qtweb_settings.PdfViewerEnabled, True
        )
        self.file_preview.settings().setAttribute(
            _qtweb_settings.SpatialNavigationEnabled, True
        )       

        self.clear_pdf_viewer()
        self.view_model.display_pdf_preview.connect(self.display_pdf_preview)
        self.main_layout.addWidget(self.file_preview)
        self.main_layout.setStretch(self.main_layout.indexOf(self.file_preview), 8)

        # self.file_preview.show()

        # Progress bar to show analyze progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Select Files to Begin...")
        self.view_model.main_view_model.process_progress_value_update.connect(
            lambda: self.progress_bar.setValue(
                self.view_model.main_view_model.process_progress_value
            )
        )
        self.view_model.main_view_model.process_progress_text_update.connect(
            lambda: self.progress_bar.setFormat(
                self.view_model.main_view_model.process_progress_text
            )
        )
        self.view_model.processed_file_rename.connect(self.update_table_item_source)
        self.main_layout.addWidget(self.progress_bar)
        self.setLayout(self.main_layout)

        self.translate_ui()

    def translate_ui(self):
        """Translates UI"""

        _translate = QtCore.QCoreApplication.translate
        self.file_rename_button.setText(_translate("ProcessView", "Rename"))
        self.file_preview_label.setText(_translate("ProcessView", "File Previewer"))

    def clear_pdf_viewer(self):
        initialized_pdf = ""
        self.file_preview.load(QtCore.QUrl(initialized_pdf))
        self.file_preview.setHtml("<body bgcolor='#4a4a4a'></body>")

    def on_load_finished(self, ok):
            if ok:
                self.file_preview.page().runJavaScript("document.querySelector('pdf-sidebar').removeAttribute('opened');")

    def update_active_files(self):
        active_files = []
        for i in range(self.files_table.rowCount()):
            file_path = self.files_table.item(i, 1).data(QtCore.Qt.UserRole)
            file_path = file_path["source"]
            active_files.append(file_path)
        self.view_model.update_active_files(active_files)

    def display_pdf_preview(self):
        """Displays PDF preview in webview"""

        pdf_dir = self.view_model.selected_file_dir
        if not pdf_dir:
            self.clear_pdf_viewer()
            return
        
        self.file_preview.load(QtCore.QUrl(f"file:{pdf_dir}"))

    def display_file_name(self):
        """Displays file name in line edit"""

        pdf_name = self.view_model.selected_file_name
        self.file_rename_line_edit.setText(pdf_name)

    def rename_file_handler(self):
        """Closes persistent editor if open"""

        if self.processed_files_list_widget.isPersistentEditorOpen(
            self.processed_files_list_widget.currentItem()
        ):
            self.processed_files_list_widget.closePersistentEditor(
                self.processed_files_list_widget.currentItem()
            )
        self.processed_files_list_widget.editItem(
            self.processed_files_list_widget.currentItem()
        )

    def get_files(self):
        self.view_model.get_files()
        self.email_button_handler()

    def table_state_handler(self, item: QtWidgets.QTableWidgetItem):
        """Handles table widget state changes

        Args:
            item (QtWidgets.QTableWidgetItem): Item that was changed
        """

        if item.column() == 0:
            data = self.files_table.item(item.row(), 1).data(QtCore.Qt.UserRole)
            self.view_model.table_state_handler(item, data)

    def process_button_text_update(self, value: int) -> None:
        """Updates process button text

        Args:
            value (int): Number of files available to process
        """
        if value == 0:
            button_text = "Process"
        elif value == 1:
            button_text = f"Process ({value}) File"
        else:
            button_text = f"Process ({value}) Files"

        self.process_button.setText(button_text)

    # def add_processed_list_widget_item(self, list_item: QtWidgets.QListWidgetItem):
    #     """Adds item to list widget

    #     Args:
    #         list_item (QtWidgets.QListWidgetItem): Item to add to list widget
    #     """
    #     self.processed_files_list_widget.addItem(list_item)
    #     self.email_button_handler()

    def file_rename_button_handler(self):
        """Renames file in list widget and on disk"""

        current_item = self.files_table.currentItem()
        file_name_item = self.files_table.item(self.files_table.row(current_item), 1)
        current_name = file_name_item.text()
        new_name = self.file_rename_line_edit.text()

        # Do nothing if name not changed
        if new_name == current_name:
            return

        file_data = current_item.data(QtCore.Qt.UserRole)
        source_path = str(file_data["source"])
        renamed_source_path = source_path.replace(current_name, new_name)
        renamed = self.view_model.rename_file(source_path, renamed_source_path)

        if renamed:
            file_data["source"] = renamed_source_path

        project_data_path = file_data["metadata"]["project_data"]
        if project_data_path:
            renamed_project_data_path = project_data_path.replace(
                current_name, new_name
            )
            renamed = self.view_model.rename_file(
                project_data_path, renamed_project_data_path
            )

            if renamed:
                file_data["metadata"]["project_data"] = renamed_project_data_path
        
        self.update_table_item_source(source_path, renamed_source_path)
        self.view_model.update_file_data_item(source_path, file_data)

    def update_table_item_source(self, source_path: str, renamed_path: str):
        """Updates table item data

        Args:
            source_path (str): Source path of file
            file_data (dict): File data
        """
        for row in range(self.files_table.rowCount()):
            item = self.files_table.item(row, 1)
            existing_data = item.data(QtCore.Qt.UserRole)
            if existing_data["source"] == source_path:
                existing_data["source"] = renamed_path
                item.setData(QtCore.Qt.UserRole, existing_data)

    def email_button_handler(self):
        """Enables email button if there are files selected, disables if not"""

        if self.view_model.selected_file_count > 0:
            self.email_button.setEnabled(True)
        else:
            self.email_button.setEnabled(False)

        return

    def email_processed_files(self):
        """Emails processed files

        Args:
            email_provider (EmailProvider): Email provider chosen by user
        """
        email_items = []
        for index in range(self.processed_files_list_widget.count()):
            email_items.append(self.processed_files_list_widget.item(index))
        self.view_model.email_files(email_items)

    def get_email_provider(self):
        """Displays a popup for user to choose email client to send emails with"""

        # Display a popup to choose between outlook or gmail with the logos
        # the two buttons should be vertically stacked

        popup = QtWidgets.QDialog()
        popup.setWindowTitle("Choose Email Provider")

        popup_layout = QtWidgets.QVBoxLayout()
        popup.setLayout(popup_layout)

        outlook_button = QtWidgets.QPushButton()
        outlook_button.setIcon(QtGui.QIcon(resource_path("assets/icons/outlook.png")))
        outlook_button.setIconSize(QtCore.QSize(215, 41))
        outlook_button.clicked.connect(
            lambda: self.email_provider_handler(EmailProvider.OUTLOOK)
        )
        outlook_button.clicked.connect(popup.accept)
        popup_layout.addWidget(outlook_button)

        gmail_button = QtWidgets.QPushButton()
        gmail_button.setIcon(QtGui.QIcon(resource_path("assets/icons/gmail.png")))
        gmail_button.setIconSize(QtCore.QSize(215, 46))
        gmail_button.clicked.connect(
            lambda: self.email_provider_handler(EmailProvider.GMAIL)
        )
        gmail_button.clicked.connect(popup.accept)
        popup_layout.addWidget(gmail_button)

        local_button = QtWidgets.QPushButton()
        local_button.setIcon(
            QtGui.QIcon(resource_path(self.view_model.get_local_email_icon_path()))
        )
        local_button.setIconSize(QtCore.QSize(215, 41))
        local_button.clicked.connect(
            lambda: self.email_provider_handler(EmailProvider.LOCAL)
        )
        local_button.clicked.connect(popup.accept)
        popup_layout.addWidget(local_button)

        popup_layout.addWidget(HorizontalLine())

        # Display batch email checkbox
        batch_email_checkbox = QtWidgets.QCheckBox()
        batch_email_checkbox.setText("Combine similar e-mails?")
        batch_email_checkbox.setToolTip(
            "Will combine similar e-mails to prevent spamming recipients."
        )
        batch_email_checkbox.setChecked(self.view_model.get_batch_email_state())
        batch_email_checkbox.stateChanged.connect(self.view_model.toggle_batch_email)
        popup_layout.addWidget(batch_email_checkbox)

        popup.exec()

    def email_provider_handler(self, email_provider: EmailProvider):
        """Handles which email provider to use to send emails

        Args:
            email_provider (EmailProvider): Email provider chosen by user
        """
        self.view_model.email_provider = email_provider
        token_success = self.view_model.get_email_token()
        if token_success:
            self.view_model.email_files_handler()

    def email_unprocessed_processed_handler(self):
        """Checks if all files have been processed, if not, emails unprocessed files, if so, gets email provider"""

        # If files havent been processed then we need the metadata to determine who to email and with what template
        selected_files = self.view_model.get_selected_files()
        if not selected_files:
            return
        
        unprocessed_files = [file for file in selected_files if not self.view_model.active_files_data[file]["processed"]]
        if unprocessed_files:
            self.view_model.unprocessed_email_check(self.get_email_provider)
            return
        # if (
        #     self.view_model.selected_file_count
        #     > self.processed_files_list_widget.count()
        # ):
        #     self.view_model.unprocessed_email_check(
        #         lambda: self.get_email_provider(processed=False)
        #     )
        #     return

        self.get_email_provider()

    def table_widget_connect(self):
        """Connects table widget to view model"""

        self.files_table.currentItemChanged.connect(
            lambda: self.view_model.table_widget_handler(
                self.files_table.item(self.files_table.currentRow(), 1)
            )
        )
        self.files_table.itemChanged.connect(self.table_state_handler)

    def table_widget_disconnect(self):
        """Disconnects table widget from view model"""

        self.files_table.currentItemChanged.disconnect()
        self.files_table.itemChanged.disconnect()

    def update_table_data(self):
        """Updates table data by finding rows with existing data and updating them, then adding new rows"""
        current_item_index = self.files_table.currentRow()
        self.table_widget_disconnect()
        try:
            self.update_existing_entries()
            self.add_new_entries()
            self.resize_columns()
            self.update_current_item(current_item_index)
        finally:
            self.update()
            self.table_widget_connect()
            self.view_model.process_button_handler()
            self.view_model.update_loaded_files_count()

    def update_existing_entries(self):
        """Updates existing entries in the table with new data."""
        self.updated_files = []
        for row in range(self.files_table.rowCount()):
            item = self.files_table.item(row, 1)
            try:
                item_data = dict(item.data(QtCore.Qt.UserRole))
            except ValueError:
                continue
            file_path = item_data.pop("source", None)
            if file_path in self.view_model.active_files_data:
                self.updated_files.append(file_path)
                data = self.view_model.active_files_data[file_path]
                data["source"] = file_path
                self.update_row_items(row, data)

    def update_row_items(self, row, data):
        """Updates the items in a row with new data."""
        row_items = self.view_model.get_formatted_row_items(data)
        for col, col_item in enumerate(row_items):
            self.files_table.setItem(row, col, col_item)

    def add_new_entries(self):
        """Adds new entries to the table."""
        for row, (file_name, file_data) in enumerate(self.view_model.active_files_data.items()):
            if file_name in self.updated_files:
                continue
            self.files_table.insertRow(self.files_table.rowCount())
            data = dict(file_data)
            data["source"] = file_name
            self.update_row_items(row, data)

    def resize_columns(self):
        """Resizes the columns to fit their contents."""
        for col in range(self.files_table.columnCount()):
            self.files_table.resizeColumnToContents(col)
        self.files_table.verticalHeader().setVisible(False)

    def update_current_item(self, current_item_index):
        """Updates the current item in the table."""
        if current_item_index >= 0:
            self.files_table.setCurrentCell(current_item_index, 1)
        if self.files_table.currentItem():
            self.view_model.table_widget_handler(
                self.files_table.item(self.files_table.currentRow(), 1)
            )

    def remove_deleted_rows(self):
        """Removes rows from the table that correspond to files deleted from active_files_data."""
        current_row = self.files_table.currentRow()
        for row in reversed(range(self.files_table.rowCount())):
            item = self.files_table.item(row, 1)
            try:
                item_data = dict(item.data(QtCore.Qt.UserRole))
            except ValueError:
                continue
            file_path = item_data.get("source")
            if file_path not in self.view_model.active_files_data:
                self.files_table.removeRow(row)
                if row == current_row:
                    self.files_table.setCurrentItem(None)
                    self.view_model.table_widget_handler()
        self.update_table_data()
    


        

