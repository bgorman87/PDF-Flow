from PySide6 import QtCore, QtWebEngineCore, QtWebEngineWidgets, QtWidgets

from view_models import process_view_model
from widgets import utility_widgets


class ProcessView(QtWidgets.QWidget):
    def __init__(self, view_model: process_view_model.ProcessViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()

        self.input_tab_action_buttons = QtWidgets.QHBoxLayout()
        # Action buttons on Input tab
        self.select_files = QtWidgets.QPushButton()
        self.select_files.clicked.connect(self.view_model.get_files)
        self.select_files.setObjectName("Select_files")
        self.dialog = QtWidgets.QFileDialog()
        self.input_tab_action_buttons.addWidget(self.select_files)

        # Action button to start file analysis
        self.process_button = QtWidgets.QPushButton()
        self.process_button.clicked.connect(self.view_model.process_files)
        self.process_button.setObjectName("analyze_button")
        self.process_button.setEnabled(False)
        self.view_model.main_view_model.process_button_state_update.connect(
            lambda: self.process_button.setEnabled(self.view_model.main_view_model.process_button_state))
        self.view_model.main_view_model.process_button_count_update.connect(
            lambda: self.process_button_text_update(self.view_model.main_view_model.process_button_count))
        self.input_tab_action_buttons.addWidget(self.process_button)

        # Action button to start email process
        self.email_button = QtWidgets.QPushButton()
        # self.email_button.clicked.connect(self.email_button_handler)
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

        # Label for list widget below
        self.processed_files_label = QtWidgets.QLabel()
        self.processed_files_label.setGeometry(QtCore.QRect(10, 10, 81, 16))
        self.processed_files_label.setObjectName("processed_files_label")
        self.main_layout.addWidget(self.processed_files_label)

        # Widget to hold analyzed files
        self.processed_files_list_widget = QtWidgets.QListWidget()
        self.processed_files_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.processed_files_list_widget.setGeometry(
            QtCore.QRect(10, 30, 320, 100))
        self.processed_files_list_widget.setObjectName(
            "processed_files_list_widget")
        self.main_layout.addWidget(self.processed_files_list_widget)
        self.main_layout.setStretch(
            self.main_layout.indexOf(self.processed_files_list_widget), 2
        )
        self.view_model.processed_files_list_widget_update.connect(
            self.add_processed_list_widget_item)

        # Lines within the analyzed files widget above
        self.processed_files_list_item = QtWidgets.QListWidgetItem()
        self.processed_files_list_widget.itemClicked.connect(
            lambda: self.view_model.list_widget_handler(self.processed_files_list_widget.currentItem()))
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
        # self.file_rename_button.clicked.connect(self.file_rename_button_handler)
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
        self.main_layout.setStretch(
            self.main_layout.indexOf(self.file_preview), 8
        )

        self.file_preview.show()

        # Progress bar to show analyze progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Select Files to Begin...")
        self.view_model.main_view_model.process_progress_value_update.connect(
            lambda: self.progress_bar.setValue(self.view_model.main_view_model.process_progress_value))
        self.view_model.main_view_model.process_progress_text_update.connect(
            lambda: self.progress_bar.setFormat(self.view_model.main_view_model.process_progress_text))
        self.main_layout.addWidget(self.progress_bar)
        self.setLayout(self.main_layout)

        self.translate_ui()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.select_files.setText(
            _translate("SettingsView", "Select Files")
        )
        self.process_button.setText(
            _translate("SettingsView", "Process")
        )
        self.email_button.setText(_translate("SettingsView", "Email"))
        self.processed_files_label.setText(
            _translate("SettingsView", "Processed Files"))
        self.file_rename_button.setText(_translate("SettingsView", "Rename"))
        self.file_preview_label.setText(
            _translate("SettingsView", "File Previewer"))

    def display_pdf_preview(self):
        pdf_dir = self.view_model.selected_file_dir
        self.file_preview.load(QtCore.QUrl(f"file:{pdf_dir}"))
        self.file_preview.show()

    def display_file_name(self):
        pdf_name = self.view_model.selected_file_name
        self.file_rename_line_edit.setText(pdf_name)

    def rename_file_handler(self):
        """Closes persistant editor if open"""

        if self.processed_files_list_widget.isPersistentEditorOpen(
            self.processed_files_list_widget.currentItem()
        ):
            self.processed_files_list_widget.closePersistentEditor(
                self.processed_files_list_widget.currentItem()
            )
        self.processed_files_list_widget.editItem(
            self.processed_files_list_widget.currentItem()
        )

    def process_button_text_update(self, value: int) -> None:
        if value == 0:
            button_text = "Process"
        elif value == 1:
            button_text = f"Process ({value}) File"
        else:
            button_text = f"Process ({value}) Files"

        self.process_button.setText(button_text)

    def add_processed_list_widget_item(self, list_item: QtWidgets.QListWidgetItem):
        self.processed_files_list_widget.addItem(list_item)
