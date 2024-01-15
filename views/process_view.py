from PySide6 import QtCore, QtGui, QtWebEngineCore, QtWebEngineWidgets, QtWidgets

from utils.enums import EmailProvider
from utils.image_utils import resource_path
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
        self.select_files = QtWidgets.QPushButton()
        self.select_files.clicked.connect(self.get_files)
        self.select_files.setObjectName("Select_files")
        self.dialog = QtWidgets.QFileDialog()
        self.input_tab_action_buttons.addWidget(self.select_files)

        # Action button to start file analysis
        self.process_button = QtWidgets.QPushButton()
        self.process_button.clicked.connect(self.view_model.process_files)
        self.process_button.setObjectName("analyze_button")
        self.process_button.setEnabled(False)
        self.view_model.main_view_model.process_button_state_update.connect(
            lambda: self.process_button.setEnabled(
                self.view_model.main_view_model.process_button_state
            )
        )
        self.view_model.main_view_model.process_button_count_update.connect(
            lambda: self.process_button_text_update(
                self.view_model.main_view_model.process_button_count
            )
        )
        self.input_tab_action_buttons.addWidget(self.process_button)

        # Action button to start email process
        self.email_button = QtWidgets.QPushButton()
        self.email_button.clicked.connect(self.email_unprocessed_processed_handler)
        self.email_button.setObjectName("email_button")
        self.email_button.setEnabled(False)
        self.input_tab_action_buttons.addWidget(self.email_button)

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

        self.line_below_action_buttons_layout = QtWidgets.QHBoxLayout()
        # Line below action buttons
        self.input_tab_line_2 = utility_widgets.HorizontalLine()
        self.line_below_action_buttons_layout.addWidget(self.input_tab_line_2)
        self.main_layout.addLayout(self.line_below_action_buttons_layout)

        # Table to hold all of the files
        self.files_table = QtWidgets.QTableWidget()
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

        self.view_model.active_files_update.connect(self.update_table_data)

        self.main_layout.addWidget(self.files_table)

        # Widget to hold analyzed files
        self.processed_files_list_widget = QtWidgets.QListWidget()
        self.processed_files_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.processed_files_list_widget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        self.processed_files_list_widget.setObjectName("processed_files_list_widget")
        self.main_layout.addWidget(self.processed_files_list_widget)
        self.main_layout.setStretch(
            self.main_layout.indexOf(self.processed_files_list_widget), 2
        )
        self.view_model.processed_files_list_widget_update.connect(
            self.add_processed_list_widget_item
        )

        # Lines within the analyzed files widget above
        self.processed_files_list_item = QtWidgets.QListWidgetItem()
        self.processed_files_list_widget.itemClicked.connect(
            lambda: self.view_model.list_widget_handler(
                self.processed_files_list_widget.currentItem()
            )
        )
        self.processed_files_list_widget.itemDoubleClicked.connect(
            self.rename_file_handler
        )

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
        self.file_preview.settings().setAttribute(_qtweb_settings.WebGLEnabled, True)
        self.file_preview.settings().setAttribute(
            _qtweb_settings.PdfViewerEnabled, True
        )
        self.file_preview.settings().setAttribute(
            _qtweb_settings.SpatialNavigationEnabled, True
        )

        initialized_pdf = ""
        self.file_preview.load(QtCore.QUrl(initialized_pdf))
        self.file_preview.setHtml("<body bgcolor='#4a4a4a'></body>")
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
        self.main_layout.addWidget(self.progress_bar)
        self.setLayout(self.main_layout)

        self.translate_ui()

    def translate_ui(self):
        """Translates UI"""

        _translate = QtCore.QCoreApplication.translate
        self.select_files.setText(_translate("ProcessView", "Import Files"))
        self.process_button.setText(_translate("ProcessView", "Process"))
        self.email_button.setText(_translate("ProcessView", "Email"))
        self.file_rename_button.setText(_translate("ProcessView", "Rename"))
        self.file_preview_label.setText(_translate("ProcessView", "File Previewer"))

    def check_selection_handler(self, state: bool):
        for i in range(1, self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(i, 0)
            checkbox.setChecked(state)

    def delete_selected(self):
        for i in range(1, self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(i, 0)
            if checkbox.isChecked():
                # Delete the row
                self.files_table.removeRow(i)
                self.update_active_files()

    def update_active_files(self):
        active_files = []
        for i in range(1, self.files_table.rowCount()):
            file_path = self.files_table.item(i, 1).data(QtCore.Qt.UserRole)
            file_path = file_path["source"]
            active_files.append(file_path)
        self.view_model.update_active_files(active_files)

    def display_pdf_preview(self):
        """Displays PDF preview in webview"""

        pdf_dir = self.view_model.selected_file_dir
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

    def add_processed_list_widget_item(self, list_item: QtWidgets.QListWidgetItem):
        """Adds item to list widget

        Args:
            list_item (QtWidgets.QListWidgetItem): Item to add to list widget
        """
        self.processed_files_list_widget.addItem(list_item)
        self.email_button_handler()

    def file_rename_button_handler(self):
        """Renames file in list widget and on disk"""

        current_item = self.processed_files_list_widget.currentItem()
        current_name = current_item.text()
        new_name = self.file_rename_line_edit.text()

        if new_name == current_name:
            return

        file_data = current_item.data(QtCore.Qt.UserRole)

        source_path = str(file_data["source"])
        renamed_source_path = source_path.replace(current_name, new_name)
        renamed = self.view_model.rename_file(source_path, renamed_source_path)

        if renamed:
            file_data["source"] = renamed_source_path

        project_data_path = file_data["project_data"]
        if project_data_path:
            renamed_project_data_path = project_data_path.replace(
                current_name, new_name
            )
            renamed = self.view_model.rename_file(
                project_data_path, renamed_project_data_path
            )

            if renamed:
                file_data["project_data"] = renamed_project_data_path

        self.processed_files_list_widget.currentItem().setText(
            self.file_rename_line_edit.text()
        )
        self.processed_files_list_widget.currentItem().setData(
            QtCore.Qt.UserRole, file_data
        )

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

    def get_email_provider(self, processed: bool):
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
            lambda: self.email_handler(EmailProvider.OUTLOOK, processed)
        )
        outlook_button.clicked.connect(popup.accept)
        popup_layout.addWidget(outlook_button)

        gmail_button = QtWidgets.QPushButton()
        gmail_button.setIcon(QtGui.QIcon(resource_path("assets/icons/gmail.png")))
        gmail_button.setIconSize(QtCore.QSize(215, 46))
        gmail_button.clicked.connect(
            lambda: self.email_handler(EmailProvider.GMAIL, processed)
        )
        gmail_button.clicked.connect(popup.accept)
        popup_layout.addWidget(gmail_button)

        local_button = QtWidgets.QPushButton()
        local_button.setIcon(
            QtGui.QIcon(resource_path(self.view_model.get_local_email_icon_path()))
        )
        local_button.setIconSize(QtCore.QSize(215, 41))
        local_button.clicked.connect(
            lambda: self.email_handler(EmailProvider.LOCAL, processed)
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

    def email_handler(self, email_provider: EmailProvider, processed: bool):
        """Handles which email provider to use to send emails

        Args:
            email_provider (EmailProvider): Email provider chosen by user
        """
        self.view_model.email_provider = email_provider
        token_success = self.view_model.get_email_token()
        if token_success:
            if processed:
                self.email_processed_files()
            else:
                self.view_model.email_unprocessed_files()

    def email_unprocessed_processed_handler(self):
        """Checks if all files have been processed, if not, emails unprocessed files, if so, gets email provider"""

        # If files havent been processed then we need the metadata to determine who to email and with what template
        if (
            self.view_model.selected_file_count
            > self.processed_files_list_widget.count()
        ):
            self.view_model.unprocessed_email_check(
                lambda: self.get_email_provider(processed=False)
            )
            return

        self.get_email_provider(processed=True)

    def update_table_data(self):
        """Updates table data"""

        self.files_table.setRowCount(0)

        for row, row_items in enumerate(self.view_model.active_files_table_items):
            self.files_table.insertRow(row)
            for col, col_item in enumerate(row_items):
                self.files_table.setItem(row, col, col_item)

        for col in range(self.files_table.columnCount()):
            self.files_table.resizeColumnToContents(col)

        metrics = QtGui.QFontMetrics(self.files_table.font())
        metrics.setEllipsisMode(QtCore.Qt.ElideLeft)
        
        self.files_table.verticalHeader().setVisible(False)
        
        self.update()
