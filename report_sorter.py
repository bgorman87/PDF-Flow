import ctypes
import io
import os
import re
import shutil
from collections import namedtuple

import regex as re
import win32com.client as win32
from pdf2image import convert_from_path
from PySide6 import QtCore, QtGui, QtWebEngineCore, QtWebEngineWidgets, QtWidgets

from functions.analysis import WorkerAnalyzeThread, detect_package_number
from functions.data_handler import *
from widgets.apply_data_type_dialog import ApplyFoundData
from widgets.email_list_widget import EmailListWidget
from widgets.email_widget import EmailWidget
from widgets.file_template_creation import TemplateWidget
from widgets.loading_widget import LoadingWidget

# set current working directory to variable to save files to
home_dir = os.getcwd()

# hard coded poppler path from current working directory
poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.screen()
        self.start_position = None
        self.rect = QtCore.QRect()
        self.drawing = False

        initialize_database()
        self.file_profiles_data = fetch_file_profiles()
        self.profile_names = [s[0] for s in self.file_profiles_data]
        self.profile_find_text = [s[1] for s in self.file_profiles_data]
        self.setObjectName("MainWindow")
        self.project_data_changed = False
        self.project_data_loaded_data = {
            "project_number": None,
            "directory": None,
            "email_to": None,
            "email_cc": None,
            "email_bcc": None,
            "email_subject": None,
        }
        self.project_data_loaded_id = None
        screen = QtGui.QGuiApplication.primaryScreen().size()
        self.resize(screen.width() // 2, screen.height())
        self.center_application(screen)
        self.processed_files = 0
        self.importing = False
        self.test = False
        self.unseen_console_alerts = 0
        self.current_file_profile = 0
        self.analyze_worker = None  # Worker
        self.thread = None  # Thread
        self.file_names = None  # Stores sleected file paths
        self.profile_file_loaded = False
        self.info_area_too_small = False
        self.active_params_data = None
        self.analyzed = False  # Stores analyzed state.
        self.progress = 0  # Initilize progress bar at 0
        self.project_numbers = []
        self.adding_new = True
        self.project_numbers_short = []
        # Displays how many threads can be utilized
        self.thread_pool = QtCore.QThreadPool()
        print(
            "Multithreading with maximum %d threads" % self.thread_pool.maxThreadCount()
        )
        QtCore.QMetaObject.connectSlotsByName(self)

        # Used to place Tab Widget, Central Widget, and Creator Label
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setObjectName("centralwidget")

        # self.status_bar = QtWidgets.QStatusBar()
        # self.status_bar.setObjectName("status bar")
        # self.statusBar().setSizeGripEnabled(False)
        # self.setStatusBar(self.status_bar)

        # -# Start of Tab Initialization #-#

        # Stores different tabs
        self.stacked_layout = QtWidgets.QStackedWidget(self.central_widget)
        self.stacked_layout.setObjectName("tabWidget")
        self.stacked_layout.setCurrentIndex(0)
        self.stacked_layout.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Input Tab (file_input_tab_layout)
        self.file_input_tab = QtWidgets.QWidget()
        self.file_input_tab.setObjectName("input")

        # Layout for file_input_tab_layout
        self.file_input_tab_layout = QtWidgets.QVBoxLayout()
        self.file_input_tab_layout.setObjectName("processing_layout")

        # Line above action buttons
        self.input_tab_line_1 = QtWidgets.QFrame()
        self.input_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.input_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.input_tab_line_1.setObjectName("line")
        self.input_tab_line_1_qh = QtWidgets.QHBoxLayout()
        self.input_tab_line_1_qh.addWidget(self.input_tab_line_1)

        self.file_input_tab_layout.addLayout(self.input_tab_line_1_qh)

        self.input_tab_action_buttons = QtWidgets.QHBoxLayout()
        # Action buttons on Input tab
        self.select_files = QtWidgets.QPushButton(self.file_input_tab)
        self.select_files.clicked.connect(self.open_file_dialog)
        self.select_files.setObjectName("Select_files")
        self.dialog = QtWidgets.QFileDialog()  # Used for file dialog popup
        self.input_tab_action_buttons.addWidget(self.select_files)

        # Action button to start file analysis
        self.process_button = QtWidgets.QPushButton(self.file_input_tab)
        self.process_button.clicked.connect(self.analyze_button_handler)
        self.process_button.setObjectName("analyze_button")
        self.process_button.setEnabled(False)
        self.input_tab_action_buttons.addWidget(self.process_button)

        # Action button to start email process
        self.email_button = QtWidgets.QPushButton(self.file_input_tab)
        self.email_button.clicked.connect(self.email_button_handler)
        self.email_button.setObjectName("email_button")
        self.email_button.setEnabled(False)
        self.input_tab_action_buttons.addWidget(self.email_button)

        # Drop list box to choose analysis type (Live/Test)
        # Live uses real client info, test uses dummy/local info
        self.test_box = QtWidgets.QComboBox(self.file_input_tab)
        self.test_box.setObjectName("test_box")
        self.test_box.setEditable(True)
        self.test_box.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.test_box.addItems(["Test", "Live"])
        self.test_box.setEditable(False)
        self.input_tab_action_buttons.addWidget(self.test_box)

        self.file_input_tab_layout.addLayout(self.input_tab_action_buttons)

        self.line_below_action_buttons_layout = QtWidgets.QHBoxLayout()
        # Line below action buttons
        self.input_tab_line_2 = QtWidgets.QFrame(self.file_input_tab)
        self.input_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.input_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.input_tab_line_2.setObjectName("input_tab_line_2")
        self.line_below_action_buttons_layout.addWidget(self.input_tab_line_2)
        self.file_input_tab_layout.addLayout(self.line_below_action_buttons_layout)

        # Label for list widget below
        self.processed_files_label = QtWidgets.QLabel()
        self.processed_files_label.setGeometry(QtCore.QRect(10, 10, 81, 16))
        self.processed_files_label.setObjectName("processed_files_label")
        self.file_input_tab_layout.addWidget(self.processed_files_label)

        # Widget to hold analyzed files
        self.processed_files_list_widget = QtWidgets.QListWidget()
        self.processed_files_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.processed_files_list_widget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        self.processed_files_list_widget.setObjectName("processed_files_list_widget")
        self.file_input_tab_layout.addWidget(self.processed_files_list_widget)
        self.file_input_tab_layout.setStretch(
            self.file_input_tab_layout.indexOf(self.processed_files_list_widget), 2
        )

        # Lines within the analyzed files widget above
        self.processed_files_list_item = QtWidgets.QListWidgetItem()
        self.processed_files_list_widget.itemClicked.connect(self.list_widget_handler)
        self.processed_files_list_widget.itemDoubleClicked.connect(
            self.rename_file_handler
        )

        self.file_rename_layout = QtWidgets.QHBoxLayout()
        # Text editor line to edit file names
        self.file_rename_line_edit = QtWidgets.QLineEdit()
        self.file_rename_line_edit.setObjectName("file_rename_line_edit")
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

        self.file_input_tab_layout.addLayout(self.file_rename_layout)

        # Title for JPG/PDF preview below
        self.file_preview_label = QtWidgets.QLabel()
        self.file_preview_label.setGeometry(QtCore.QRect(10, 140, 100, 16))
        self.file_preview_label.setObjectName("file_preview_label")
        self.file_input_tab_layout.addWidget(self.file_preview_label)

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
        self.file_input_tab_layout.addWidget(self.file_preview)
        self.file_input_tab_layout.setStretch(
            self.file_input_tab_layout.indexOf(self.file_preview), 8
        )

        # Initialize a blank entry, otherwise GUI will reload upon choosing tab
        # initialized_pdf = "B:/Documents/Programming/GitHub/modular_report_sorter/assets/pdf/blank.pdf"
        self.file_preview.show()

        # Progress bar to show analyze progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Select Files to Begin...")
        self.file_input_tab_layout.addWidget(self.progress_bar)
        self.file_input_tab.setLayout(self.file_input_tab_layout)
        self.stacked_layout.addWidget(self.file_input_tab)

        # Output Tab (processed_files_tab)
        self.processed_files_tab = QtWidgets.QWidget()
        self.processed_files_tab.setObjectName("console")

        # Layout for processed_files_tab
        self.processed_files_tab_layout = QtWidgets.QVBoxLayout(
            self.processed_files_tab
        )
        self.processed_files_tab_layout.setObjectName("processed_files_tab_layout")

        # Output box to display info to user
        self.status_output_box = QtWidgets.QPlainTextEdit(self.file_input_tab)
        self.status_output_box.setObjectName("status_output_box")
        self.status_output_box.setReadOnly(True)
        self.processed_files_tab_layout.addWidget(self.status_output_box)
        self.processed_files_tab.setLayout(self.processed_files_tab_layout)
        self.stacked_layout.addWidget(self.processed_files_tab)

        # Database Tab (database_viewer_tab)
        self.database_viewer_tab = QtWidgets.QWidget()
        self.database_viewer_tab.setObjectName("database_viewer")

        # Layout for database_viewer_tab
        self.database_viewer_tab_layout = QtWidgets.QVBoxLayout(
            self.database_viewer_tab
        )
        self.database_viewer_tab_layout.setObjectName("database_viewer_tab_layout")

        # Line above action buttons
        self.project_data_line_above_cta_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_1 = QtWidgets.QFrame(self.database_viewer_tab)
        self.database_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.database_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.database_tab_line_1.setObjectName("database_tab_line_1")
        self.project_data_line_above_cta_layout.addWidget(self.database_tab_line_1)

        self.database_viewer_tab_layout.addLayout(
            self.project_data_line_above_cta_layout
        )

        self.project_data_cta_layout = QtWidgets.QHBoxLayout()

        # Add new data button
        self.project_data_add_new_button = QtWidgets.QPushButton()
        self.project_data_add_new_button.clicked.connect(self.project_data_add_new)
        self.project_data_cta_layout.addWidget(self.project_data_add_new_button)

        # Import project data button
        self.import_project_data_button = QtWidgets.QPushButton()
        self.import_project_data_button.clicked.connect(self.import_project_data)
        self.project_data_cta_layout.addWidget(self.import_project_data_button)

        # Export project data button
        self.export_project_data_button = QtWidgets.QPushButton()
        self.export_project_data_button.clicked.connect(self.export_project_data)
        self.project_data_cta_layout.addWidget(self.export_project_data_button)

        # Delete all project data button
        self.delete_all_project_data_button = QtWidgets.QPushButton()
        self.delete_all_project_data_button.clicked.connect(
            self.delete_all_project_data
        )
        self.delete_all_project_data_button.setProperty("class", "delete-button")
        self.project_data_cta_layout.addWidget(self.delete_all_project_data_button)

        self.database_viewer_tab_layout.addLayout(self.project_data_cta_layout)

        # Line below action buttons
        self.project_data_line_below_cta_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_2 = QtWidgets.QFrame(self.database_viewer_tab)
        self.database_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.database_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.database_tab_line_2.setObjectName("database_tab_line_2")
        self.project_data_line_below_cta_layout.addWidget(self.database_tab_line_2)

        self.database_viewer_tab_layout.addLayout(
            self.project_data_line_below_cta_layout
        )

        self.database_search_layout = QtWidgets.QHBoxLayout()
        self.database_search_layout.addStretch(2)

        self.database_search_icon = QtWidgets.QLabel()
        self.database_search_icon.setPixmap(QtGui.QPixmap("assets/icons/search.svg"))
        self.database_search_icon.setScaledContents(True)

        self.database_search_bar = QtWidgets.QLineEdit()
        self.database_search_bar.textChanged.connect(self.filter_table)
        self.database_search_bar.setPlaceholderText("Filter...")

        self.database_search_icon.setFixedSize(20, 20)
        self.database_search_layout.addWidget(self.database_search_icon)
        self.database_search_layout.addWidget(self.database_search_bar)
        self.database_search_layout.setStretch(
            self.database_search_layout.indexOf(self.database_search_bar), 1
        )
        self.database_viewer_tab_layout.addLayout(self.database_search_layout)

        # Table widget to display DB results
        self.database_viewer_table = QtWidgets.QTableWidget()
        # Enable sorting for table widget
        # self.database_viewer_table.setSortingEnabled(True)
        self.database_viewer_table.setSelectionMode(
            QtWidgets.QTableWidget.SingleSelection
        )
        self.database_viewer_table.setEditTriggers(
            QtWidgets.QTableWidget.NoEditTriggers
        )
        # self.database_viewer_table.setModel(QtCore.QSortFilterProxyModel())
        self.database_viewer_table.currentItemChanged.connect(
            self.database_populate_project_edit_fields
        )

        self.database_viewer_tab_layout.addWidget(self.database_viewer_table)

        # Line below table
        self.project_data_line_below_table_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_3 = QtWidgets.QFrame(self.database_viewer_tab)
        self.database_tab_line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.database_tab_line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.database_tab_line_3.setObjectName("database_tab_line_3")
        self.project_data_line_below_table_layout.addWidget(self.database_tab_line_3)
        self.database_viewer_tab_layout.addLayout(
            self.project_data_line_below_table_layout
        )

        # Line below table
        self.project_data_line_below_table_2_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_4 = QtWidgets.QFrame(self.database_viewer_tab)
        self.database_tab_line_4.setFrameShape(QtWidgets.QFrame.HLine)
        self.database_tab_line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.database_tab_line_4.setObjectName("database_tab_line_4")
        self.project_data_line_below_table_2_layout.addWidget(self.database_tab_line_4)
        self.database_viewer_tab_layout.addLayout(
            self.project_data_line_below_table_2_layout
        )

        self.project_data_project_number_line_layout = QtWidgets.QHBoxLayout()

        # Label for project number line edit
        self.database_project_number_label = QtWidgets.QLabel()
        self.database_project_number_label.setObjectName(
            "database_project_number_label"
        )
        self.project_data_project_number_line_layout.addWidget(
            self.database_project_number_label
        )

        # Project number line edit
        self.database_project_number_line_edit = QtWidgets.QLineEdit()
        self.database_project_number_line_edit.setObjectName(
            "database_project_number_line_edit"
        )
        self.database_project_number_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.database_project_number_line_edit, "project_number"
            )
        )
        self.project_data_project_number_line_layout.addWidget(
            self.database_project_number_line_edit
        )

        self.database_viewer_tab_layout.addLayout(
            self.project_data_project_number_line_layout
        )

        self.project_data_directory_layout = QtWidgets.QHBoxLayout()

        # Label for directory line edit
        self.database_directory_label = QtWidgets.QLabel()
        self.database_directory_label.setObjectName("database_directory_label")
        self.project_data_directory_layout.addWidget(self.database_directory_label)

        # Project directory line edit
        self.database_project_directory_line_edit = QtWidgets.QLineEdit()
        self.database_project_directory_line_edit.setObjectName(
            "database_project_directory_line_edit"
        )
        self.database_project_directory_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.database_project_directory_line_edit, "directory"
            )
        )
        self.project_data_directory_layout.addWidget(
            self.database_project_directory_line_edit
        )

        # Action button to call rename function
        self.database_project_directory_button = QtWidgets.QPushButton()
        self.database_project_directory_button.clicked.connect(
            self.database_project_directory
        )
        self.database_project_directory_button.setObjectName(
            "database_project_directory_button"
        )
        self.project_data_directory_layout.addWidget(
            self.database_project_directory_button
        )

        self.project_data_directory_layout.setStretch(0, 1)
        self.project_data_directory_layout.setStretch(1, 10)
        self.project_data_directory_layout.setStretch(2, 2)
        self.database_viewer_tab_layout.addLayout(self.project_data_directory_layout)

        self.project_data_email_subject_layout = QtWidgets.QHBoxLayout()

        # Label for email subject line edit
        self.database_email_subject_label = QtWidgets.QLabel()
        self.database_email_subject_label.setObjectName("database_email_subject_label")
        self.project_data_email_subject_layout.addWidget(
            self.database_email_subject_label
        )

        # Project email subject line edit
        self.database_project_email_subject_line_edit = QtWidgets.QLineEdit()
        self.database_project_email_subject_line_edit.setObjectName(
            "database_project_email_subject_line_edit"
        )
        self.database_project_email_subject_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.database_project_email_subject_line_edit, "email_subject"
            )
        )
        self.project_data_email_subject_layout.addWidget(
            self.database_project_email_subject_line_edit
        )
        self.database_viewer_tab_layout.addLayout(
            self.project_data_email_subject_layout
        )

        self.project_data_email_lists_layout = QtWidgets.QHBoxLayout()
        self.project_data_email_to_layout = QtWidgets.QVBoxLayout()

        # Label for email to list widget
        self.database_email_to_label = QtWidgets.QLabel()
        self.database_email_to_label.setObjectName("database_email_to_label")
        self.project_data_email_to_layout.addWidget(self.database_email_to_label)

        # Email to list widget
        self.database_email_to_list_widget = EmailListWidget()
        # Enable dragging and dropping of items within the list widget
        # self.database_email_to_list_widget.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        # Enable editing of items by double-clicking on them
        # self.database_email_to_list_widget.setEditTriggers(QtWidgets.QListWidget.DoubleClicked)
        self.database_email_to_list_widget.itemClicked.connect(
            lambda: self.database_list_widget_add_blank(
                self.database_email_to_list_widget
            )
        )
        self.database_email_to_list_widget.itemChanged.connect(
            lambda: self.project_data_change_check(
                self.database_email_to_list_widget, "email_to"
            )
        )
        self.project_data_email_to_layout.addWidget(self.database_email_to_list_widget)

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_to_layout
        )

        self.project_data_email_cc_layout = QtWidgets.QVBoxLayout()
        # Label for email cc list widget
        self.database_email_cc_label = QtWidgets.QLabel()
        self.database_email_cc_label.setObjectName("database_email_tcc_label")
        self.project_data_email_cc_layout.addWidget(self.database_email_cc_label)

        # Email cc list widget
        self.database_email_cc_list_widget = EmailListWidget()
        # Enable dragging and dropping of items within the list widget
        self.database_email_cc_list_widget.setDragDropMode(
            QtWidgets.QListWidget.InternalMove
        )
        # Enable editing of items by double-clicking on them
        self.database_email_cc_list_widget.setEditTriggers(
            QtWidgets.QListWidget.DoubleClicked
        )
        self.database_email_cc_list_widget.itemChanged.connect(
            lambda: self.project_data_change_check(
                self.database_email_cc_list_widget, "email_cc"
            )
        )
        self.project_data_email_cc_layout.addWidget(self.database_email_cc_list_widget)

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_cc_layout
        )

        self.project_data_email_bcc_layout = QtWidgets.QVBoxLayout()
        # Label for email bcc list widget
        self.database_email_bcc_label = QtWidgets.QLabel()
        self.database_email_bcc_label.setObjectName("database_email_bcc_label")
        self.project_data_email_bcc_layout.addWidget(self.database_email_bcc_label)

        # Email bcc list widget
        self.database_email_bcc_list_widget = EmailListWidget()
        # Enable dragging and dropping of items within the list widget
        self.database_email_bcc_list_widget.setDragDropMode(
            QtWidgets.QListWidget.InternalMove
        )
        # Enable editing of items by double-clicking on them
        self.database_email_bcc_list_widget.setEditTriggers(
            QtWidgets.QListWidget.DoubleClicked
        )
        self.database_email_bcc_list_widget.itemChanged.connect(
            lambda: self.project_data_change_check(
                self.database_email_bcc_list_widget, "email_bcc"
            )
        )
        self.project_data_email_bcc_layout.addWidget(
            self.database_email_bcc_list_widget
        )

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_bcc_layout
        )
        self.database_viewer_tab_layout.addLayout(self.project_data_email_lists_layout)

        self.project_data_bottom_cta_layout = QtWidgets.QHBoxLayout()

        # Action button to save manual changes
        self.database_save_edited_project_data_button = QtWidgets.QPushButton()
        self.database_save_edited_project_data_button.clicked.connect(
            self.project_data_save_new
        )
        self.database_save_edited_project_data_button.setObjectName(
            "database_save_edited_project_data_button"
        )
        self.database_save_edited_project_data_button.setEnabled(False)
        self.project_data_bottom_cta_layout.addWidget(
            self.database_save_edited_project_data_button
        )

        # Action button to discard manual changes
        self.database_discard_edited_project_data_button = QtWidgets.QPushButton()
        self.database_discard_edited_project_data_button.clicked.connect(
            self.database_populate_project_edit_fields
        )
        self.database_discard_edited_project_data_button.setObjectName(
            "database_discard_edited_project_data_button"
        )
        self.database_discard_edited_project_data_button.setEnabled(False)
        self.project_data_bottom_cta_layout.addWidget(
            self.database_discard_edited_project_data_button
        )

        # Action button to delete database entry
        self.database_delete_project_data_button = QtWidgets.QPushButton()
        self.database_delete_project_data_button.clicked.connect(
            self.database_delete_project_data
        )
        self.database_delete_project_data_button.setObjectName(
            "database_delete_project_data_button"
        )
        self.database_delete_project_data_button.setProperty("class", "delete-button")
        self.database_delete_project_data_button.setEnabled(False)
        self.project_data_bottom_cta_layout.addWidget(
            self.database_delete_project_data_button
        )

        self.database_viewer_tab_layout.addLayout(self.project_data_bottom_cta_layout)
        self.database_viewer_tab.setLayout(self.database_viewer_tab_layout)
        self.stacked_layout.addWidget(self.database_viewer_tab)

        self.database_fetch("project_data")

        # Profile/Data Section Tab (file_template_tab)
        self.file_template_tab = QtWidgets.QWidget()
        self.file_template_tab.setObjectName("file_template")

        # Layout for file_template_tab
        self.file_template_tab_layout = QtWidgets.QVBoxLayout(self.file_template_tab)
        self.file_template_tab_layout.setObjectName("file_template_tab_layout")

        self.file_template_tab_line_above_cta_layout = QtWidgets.QHBoxLayout()
        # Line above action buttons
        self.file_template_tab_line_1 = QtWidgets.QFrame(self.file_input_tab)
        self.file_template_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.file_template_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.file_template_tab_line_1.setObjectName("file_template_tab_line_1")
        self.file_template_tab_line_above_cta_layout.addWidget(
            self.file_template_tab_line_1
        )

        self.file_template_tab_layout.addLayout(
            self.file_template_tab_line_above_cta_layout
        )

        self.file_template_tab_cta_button_layout = QtWidgets.QHBoxLayout()

        # Button to load template file
        self.select_template_file = QtWidgets.QPushButton()
        self.select_template_file.setObjectName("select_template_file")
        self.select_template_file.clicked.connect(self.file_profile_template_dialog)
        self.select_template_file_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(self.select_template_file)

        # Label for profile name
        self.file_template_profile_name_label = QtWidgets.QLabel()
        self.file_template_tab_cta_button_layout.addWidget(
            self.file_template_profile_name_label
        )

        # Button to apply selection as co-ords for unique file identifier
        self.apply_unique_file_identifier_button = QtWidgets.QPushButton()
        self.apply_unique_file_identifier_button.setObjectName(
            "apply_unique_file_identifier_button"
        )
        self.apply_unique_file_identifier_button.clicked.connect(
            self.apply_unique_file_indentifier
        )
        self.apply_unique_file_identifier_button.setEnabled(False)
        self.apply_unique_file_identifier_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(
            self.apply_unique_file_identifier_button
        )

        # Button to apply selection as co-ords for project number
        self.apply_unique_profile_project_number_button = QtWidgets.QPushButton()
        self.apply_unique_profile_project_number_button.setObjectName(
            "apply_unique_profile_project_number_button"
        )
        self.apply_unique_profile_project_number_button.clicked.connect(
            lambda: self.apply_unique_profile_parameter(project_number=True)
        )
        self.apply_unique_profile_project_number_button.setEnabled(False)
        self.apply_unique_profile_project_number_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(
            self.apply_unique_profile_project_number_button
        )

        # Button to apply selection as co-ords for unique data information
        self.apply_unique_profile_parameter_button = QtWidgets.QPushButton()
        self.apply_unique_profile_parameter_button.setObjectName(
            "apply_unique_profile_parameter_button"
        )
        self.apply_unique_profile_parameter_button.clicked.connect(
            self.apply_unique_profile_parameter
        )
        self.apply_unique_profile_parameter_button.setEnabled(False)
        self.apply_unique_profile_parameter_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(
            self.apply_unique_profile_parameter_button
        )

        self.file_template_tab_layout.addLayout(
            self.file_template_tab_cta_button_layout
        )

        # Line below action buttons
        self.file_template_tab_line_below_cta_layout = QtWidgets.QHBoxLayout()
        self.file_template_tab_line_2 = QtWidgets.QFrame(self.file_input_tab)
        self.file_template_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.file_template_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.file_template_tab_line_2.setObjectName("file_template_tab_line_2")
        self.file_template_tab_line_below_cta_layout.addWidget(
            self.file_template_tab_line_2
        )

        self.file_template_tab_layout.addLayout(
            self.file_template_tab_line_below_cta_layout
        )

        # Custom template display widget
        self.template_display = TemplateWidget()
        self.file_template_tab_layout.addWidget(self.template_display)
        self.file_template_tab.setLayout(self.file_template_tab_layout)
        self.stacked_layout.addWidget(self.file_template_tab)

        # Settings Tab (settings_tab)
        self.settings_tab = QtWidgets.QWidget()
        self.settings_tab.setObjectName("settings")

        # Layout for settings_tab
        self.setting_tab_layout = QtWidgets.QVBoxLayout(self.settings_tab)
        self.setting_tab_layout.setObjectName("setting_tab_layout")

        # Line above action buttons
        self.settings_tab_line_1 = QtWidgets.QFrame()
        self.settings_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.settings_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.settings_tab_line_1.setObjectName("settings_tab_line_1")
        self.setting_tab_layout.addWidget(self.settings_tab_line_1)

        self.settings_profile_choices_label_layout = QtWidgets.QHBoxLayout()

        # Label to display active parameters
        self.settings_profile_template_label = QtWidgets.QLabel()
        self.settings_profile_template_label.setObjectName(
            "settings_profile_template_label"
        )
        self.settings_profile_choices_label_layout.addWidget(
            self.settings_profile_template_label
        )

        # Label to display active parameters
        self.settings_profile_parameters_label = QtWidgets.QLabel()
        self.settings_profile_parameters_label.setObjectName(
            "settings_profile_parameters_label"
        )
        self.settings_profile_choices_label_layout.addWidget(
            self.settings_profile_parameters_label
        )

        self.setting_tab_layout.addLayout(self.settings_profile_choices_label_layout)

        self.settings_profile_choices_layout = QtWidgets.QHBoxLayout()

        # List widget to display profiles
        self.settings_profile_templates_list_widget = QtWidgets.QListWidget()
        self.settings_profile_templates_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.settings_profile_templates_list_widget.setObjectName(
            "settings_profile_templates_list_widget"
        )
        self.settings_profile_templates_list_widget.addItems(
            self.format_file_profile_dropdown()
        )
        self.settings_profile_templates_list_widget.itemClicked.connect(
            self.display_active_parameters
        )
        self.settings_profile_choices_layout.addWidget(
            self.settings_profile_templates_list_widget
        )

        # List widget to display active parameters
        self.settings_profile_parameters_list_widget = QtWidgets.QListWidget()
        self.settings_profile_parameters_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.settings_profile_parameters_list_widget.setObjectName(
            "settings_profile_parameters_list_widget"
        )
        self.settings_profile_parameters_list_widget.itemClicked.connect(
            self.add_active_param_line_edit
        )
        self.settings_profile_choices_layout.addWidget(
            self.settings_profile_parameters_list_widget
        )

        self.setting_tab_layout.addLayout(self.settings_profile_choices_layout)

        # Line below action buttons
        self.settings_tab_line_2 = QtWidgets.QFrame()
        self.settings_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.settings_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.settings_tab_line_2.setObjectName("settings_tab_line_2")
        self.setting_tab_layout.addWidget(self.settings_tab_line_2)

        # Label for file rename parameter input
        self.settings_profile_naming_scheme_label = QtWidgets.QLabel()
        self.settings_profile_naming_scheme_label.setObjectName(
            "settings_profile_naming_scheme_label"
        )
        self.setting_tab_layout.addWidget(self.settings_profile_naming_scheme_label)

        self.settings_file_name_pattern_layout = QtWidgets.QHBoxLayout()
        # Line edit for user to type in format with parameters
        self.settings_profile_naming_scheme_line_edit = QtWidgets.QLineEdit(
            self.settings_tab
        )
        self.settings_profile_naming_scheme_line_edit.setObjectName(
            "settings_profile_naming_scheme_line_edit"
        )
        self.settings_profile_naming_scheme_line_edit.textChanged.connect(
            self.display_example_file_name
        )
        self.settings_file_name_pattern_layout.addWidget(
            self.settings_profile_naming_scheme_line_edit
        )

        # Button to apply selection as co-ords for unique data information
        self.settings_profile_naming_scheme_button = QtWidgets.QPushButton()
        self.settings_profile_naming_scheme_button.setObjectName(
            "settings_profile_naming_scheme_button"
        )
        self.settings_profile_naming_scheme_button.clicked.connect(
            self.apply_file_name_pattern
        )
        self.settings_file_name_pattern_layout.addWidget(
            self.settings_profile_naming_scheme_button
        )

        self.setting_tab_layout.addLayout(self.settings_file_name_pattern_layout)

        # Label for file rename example output
        self.settings_profile_naming_scheme_example_label = QtWidgets.QLabel()
        self.settings_profile_naming_scheme_example_label.setObjectName(
            "settings_profile_naming_scheme_example_label"
        )
        self.setting_tab_layout.addWidget(
            self.settings_profile_naming_scheme_example_label
        )

        # Line edit to display an example of data shown
        self.settings_profile_naming_scheme_example_line_edit = QtWidgets.QLineEdit()
        self.settings_profile_naming_scheme_example_line_edit.setEnabled(False)
        self.settings_profile_naming_scheme_example_line_edit.setObjectName(
            "settings_profile_naming_scheme_example_line_edit"
        )
        self.setting_tab_layout.addWidget(
            self.settings_profile_naming_scheme_example_line_edit
        )

        # Line to split sections
        self.settings_tab_line_3 = QtWidgets.QFrame()
        self.settings_tab_line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.settings_tab_line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.settings_tab_line_3.setObjectName("settings_tab_line_3")
        self.setting_tab_layout.addWidget(self.settings_tab_line_3)

        # Line to split sections
        self.settings_tab_line_4 = QtWidgets.QFrame()
        self.settings_tab_line_4.setFrameShape(QtWidgets.QFrame.HLine)
        self.settings_tab_line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.settings_tab_line_4.setObjectName("settings_tab_line_4")
        self.setting_tab_layout.addWidget(self.settings_tab_line_4)

        # signature text edit
        self.settings_email_text_edit = EmailWidget()
        self.settings_email_text_edit.setObjectName("settings_email_text_edit")
        self.setting_tab_layout.addWidget(self.settings_email_text_edit)
        self.setting_tab_layout.setStretch(
            self.setting_tab_layout.indexOf(self.settings_email_text_edit), 1
        )
        self.settings_tab.setLayout(self.setting_tab_layout)
        self.stacked_layout.addWidget(self.settings_tab)

        self.navigation_layout = QtWidgets.QVBoxLayout()
        self.navigation_layout.setSpacing(5)
        self.navigation_layout.setContentsMargins(0, 100, 0, 0)

        self.input_nav_button = QtWidgets.QPushButton()
        self.input_nav_button.setProperty(
            "index", self.stacked_layout.indexOf(self.file_input_tab)
        )
        self.input_nav_button.clicked.connect(self.on_nav_button_clicked)
        self.input_nav_button.setProperty("class", "nav-button")

        self.console_nav_button = QtWidgets.QPushButton()
        self.console_nav_button.setProperty(
            "index", self.stacked_layout.indexOf(self.processed_files_tab)
        )
        self.console_nav_button.clicked.connect(self.on_nav_button_clicked)
        self.console_nav_button.setProperty("class", "nav-button")

        self.project_data_nav_button = QtWidgets.QPushButton()
        self.project_data_nav_button.setProperty(
            "index", self.stacked_layout.indexOf(self.database_viewer_tab)
        )
        self.project_data_nav_button.clicked.connect(self.on_nav_button_clicked)
        self.project_data_nav_button.setProperty("class", "nav-button")

        self.template_nav_button = QtWidgets.QPushButton()
        self.template_nav_button.setProperty(
            "index", self.stacked_layout.indexOf(self.file_template_tab)
        )
        self.template_nav_button.clicked.connect(self.on_nav_button_clicked)
        self.template_nav_button.setProperty("class", "nav-button")

        self.settings_nav_button = QtWidgets.QPushButton()
        self.settings_nav_button.setProperty(
            "index", self.stacked_layout.indexOf(self.settings_tab)
        )
        self.settings_nav_button.clicked.connect(self.on_nav_button_clicked)
        self.settings_nav_button.setProperty("class", "nav-button")

        self.loaded_file_button = QtWidgets.QPushButton()
        self.loaded_file_button.setProperty("class", "nav-button")
        self.loaded_file_button.setText("Loaded Files: 0")

        self.processed_file_button = QtWidgets.QPushButton()
        self.processed_file_button.setProperty("class", "nav-button")
        self.processed_file_button.setText("Processed Files: 0")

        self.emailed_files_button = QtWidgets.QPushButton()
        self.emailed_files_button.setProperty("class", "nav-button")
        self.emailed_files_button.setText("E-Mailed Files: 0")

        self.nav_button_list = [
            self.input_nav_button,
            self.console_nav_button,
            self.project_data_nav_button,
            self.template_nav_button,
            self.settings_nav_button,
        ]

        # self.navigation_layout.addSpacing(100)
        self.navigation_layout.addWidget(self.input_nav_button)
        self.navigation_layout.addWidget(self.console_nav_button)
        self.navigation_layout.addWidget(self.project_data_nav_button)
        self.navigation_layout.addWidget(self.template_nav_button)
        self.navigation_layout.addWidget(self.settings_nav_button)
        self.navigation_layout.addStretch()
        self.navigation_layout.addWidget(self.loaded_file_button)
        self.navigation_layout.addWidget(self.processed_file_button)
        self.navigation_layout.addWidget(self.emailed_files_button)
        self.navigation_layout.addSpacing(50)
        self.navigation_widget = QtWidgets.QWidget()
        self.navigation_widget.setLayout(self.navigation_layout)
        self.navigation_widget.setProperty("class", "nav-widget")

        self.parent_widget = QtWidgets.QWidget()
        self.parent_layout = QtWidgets.QHBoxLayout()
        self.parent_layout.setContentsMargins(0, 0, 0, 0)
        # self.parent_layout.setSpacing(20)

        self.parent_layout.addWidget(self.navigation_widget)

        self.parent_layout.addWidget(self.stacked_layout)

        self.parent_layout.setStretch(0, 0)
        self.parent_layout.setStretch(1, 1)

        self.parent_widget.setLayout(self.parent_layout)
        self.setCentralWidget(self.parent_widget)

        # Style the current nav button for the shown stacked item
        self.on_nav_button_clicked(self.input_nav_button)

        # Creator Label
        self.label = QtWidgets.QLabel(self.central_widget)
        self.label.setObjectName("creatorLabel")
        # self.central_layout.addWidget(self.label)

        # Translate UI if in another language
        self.translate_ui()

        # Set tab order (Can probably include more in future)
        # self.setTabOrder(self.select_files, self.process_button)
        # self.setTabOrder(self.process_button, self.status_output_box)
        # self.setTabOrder(self.status_output_box, self.file_input_tab)
        # self.setTabOrder(self.file_input_tab, self.processed_files_tab)
        # self.setTabOrder(self.processed_files_tab, self.database_viewer_tab)
        # self.setTabOrder(self.database_viewer_tab, self.file_template_tab)

        # Once finished initializing, show
        self.stacked_layout.currentChanged.connect(self.tab_clicked_handler)
        self.show()

    progress_update = QtCore.Signal(int)

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate

        self.setWindowTitle(_translate("MainWindow", "Report Sorter"))
        self.settings_profile_naming_scheme_label.setText(
            _translate("MainWindow", "File Name Template:")
        )
        self.settings_profile_naming_scheme_example_label.setText(
            _translate("MainWindow", "File Name Preview:")
        )
        self.label.setText(
            _translate("MainWindow", "© 2023 Brandon Gorman. All rights reserved.")
        )
        self.file_preview_label.setText(_translate("MainWindow", "File Output Viewer:"))
        self.processed_files_label.setText(_translate("MainWindow", "Processed Files:"))
        self.settings_profile_parameters_label.setText(
            _translate("MainWindow", "Available Profile Parameters:")
        )
        self.settings_profile_template_label.setText(
            _translate("MainWindow", "Choose Profile:")
        )
        self.database_email_to_label.setText(_translate("MainWindow", "Email TO List:"))
        self.database_email_cc_label.setText(_translate("MainWindow", "Email CC List:"))
        self.database_email_bcc_label.setText(
            _translate("MainWindow", "Email BCC List:")
        )
        self.database_project_number_label.setText(
            _translate("MainWindow", "Project Number:")
        )
        self.database_directory_label.setText(_translate("MainWindow", "Directory:"))
        self.database_email_subject_label.setText(
            _translate("MainWindow", "Email Subject:")
        )

        self.select_files.setText(_translate("MainWindow", "Select Files"))
        self.file_rename_button.setWhatsThis(
            _translate("MainWindow", "Rename the currently selected file")
        )
        self.select_template_file.setText(
            _translate("MainWindow", "Open Template File")
        )
        self.apply_unique_file_identifier_button.setText(
            _translate("MainWindow", "Set Unique Profile Identifier")
        )
        self.apply_unique_profile_parameter_button.setText(
            _translate("MainWindow", "Add Data Parameter")
        )
        self.apply_unique_profile_project_number_button.setText(
            _translate("MainWindow", "Add Project Number")
        )
        self.database_project_directory_button.setText(
            _translate("MainWindow", "Select Folder")
        )
        self.import_project_data_button.setText(
            _translate("MainWindow", "Import Project Data")
        )
        self.export_project_data_button.setText(
            _translate("MainWindow", "Export Project Data")
        )
        self.project_data_add_new_button.setText(_translate("MainWindow", "New Entry"))
        self.delete_all_project_data_button.setText(
            _translate("MainWindow", "Delete ALL Project Data")
        )
        self.file_rename_button.setText(_translate("MainWindow", "Rename"))
        self.process_button.setText(_translate("MainWindow", "Process"))
        self.email_button.setText(_translate("MainWindow", "E-Mail"))
        self.settings_profile_naming_scheme_button.setText(
            _translate("MainWindow", "Save Filename Pattern")
        )
        self.database_discard_edited_project_data_button.setText(
            _translate("MainWindow", "Discard Changes")
        )
        self.database_save_edited_project_data_button.setText(
            _translate("MainWindow", "Save New")
        )
        self.database_delete_project_data_button.setText(
            _translate("MainWindow", "Delete Entry")
        )

        self.input_nav_button.setText(_translate("MainWindow", "Process"))
        self.console_nav_button.setText(_translate("MainWindow", "Console"))
        self.project_data_nav_button.setText(_translate("MainWindow", "Project Data"))
        self.template_nav_button.setText(_translate("MainWindow", "Templates"))
        self.settings_nav_button.setText(_translate("MainWindow", "Settings"))

        # self.stacked_layout.setTabText(self.stacked_layout.indexOf(
        #     self.file_input_tab), _translate("MainWindow", "Processing"))
        # self.stacked_layout.setTabText(self.stacked_layout.indexOf(
        #     self.processed_files_tab), _translate("MainWindow", "Console"))
        # self.stacked_layout.setTabText(self.stacked_layout.indexOf(
        #     self.database_viewer_tab), _translate("MainWindow", "Project Data"))
        # self.stacked_layout.setTabText(self.stacked_layout.indexOf(
        #     self.file_template_tab), _translate("MainWindow", "Template Input"))
        # self.stacked_layout.setTabText(self.stacked_layout.indexOf(
        #     self.settings_tab), _translate("MainWindow", "Settings"))

    def on_nav_button_clicked(self, sender_button=None):
        if not sender_button:
            sender_button = self.sender()
        self.stacked_layout.setCurrentIndex(sender_button.property("index"))

        for button in self.nav_button_list:
            button.setProperty("class", "nav-button")
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

        sender_button.setProperty("class", "chosen-nav-button")

        sender_button.style().unpolish(sender_button)
        sender_button.style().polish(sender_button)
        sender_button.update()

    def center_application(self, screen):
        # get the size of the main window
        windowWidth = self.frameGeometry().width()
        windowHeight = self.frameGeometry().height()

        # calculate the top-left corner of the main window
        x = screen.width() // 2 - windowWidth // 2
        y = screen.height() // 2 - windowHeight // 2

        # set the position of the main window
        self.move(x, y)
        self.resize(screen.width() // 2, screen.height() / 1.1)

    def database_delete_project_data(self):
        if self.project_data_loaded_id is None:
            return

        delete_return = delete_project_data_entry(
            self.project_data_loaded_data["project_number"]
        )

        if delete_return == None:
            # self.project_data_loaded_id = None
            self.database_fetch("project_data")
            self.clear_project_data_entry_fields()
            row_count = 0
            index_in_shown = False
            first_index = None
            item = self.database_viewer_table.item(
                self.project_data_loaded_id.row(), self.project_data_loaded_id.column()
            )
            for row in range(self.database_viewer_table.rowCount()):
                if not self.database_viewer_table.isRowHidden(row):
                    row_count += 1
                    for col in range(self.database_viewer_table.columnCount()):
                        shown_item = self.database_viewer_table.item(row, col)
                        if first_index is None:
                            first_index = self.database_viewer_table.indexFromItem(
                                shown_item
                            )
                        if item.text() == shown_item.text():
                            index_in_shown = True

            if row_count > 0:
                if index_in_shown:
                    self.database_viewer_table.setCurrentIndex(
                        self.project_data_loaded_id
                    )
                else:
                    self.project_data_loaded_id = first_index
                    self.database_viewer_table.setCurrentIndex(first_index)
                self.database_populate_project_edit_fields()
                return
            self.database_delete_project_data_button.setEnabled(False)
            self.project_data_loaded_id = None
            return

        # Return any errors and display to user, leaving data as is if any occurs
        delete_error_dialog = QtWidgets.QMessageBox()
        delete_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        delete_error_dialog.setWindowTitle("Project Data Delete Error")
        delete_error_dialog.setText(
            f"Error occured delete project data\n\n \
            {delete_return}"
        )
        delete_error_dialog.exec()

    def database_fetch(self, table_name):
        """Handles threading database fetching and passing results to display to user"""

        # Database may get large so start seperate thread to handle fetching
        self.database_table_data = fetch_data(table_name)
        self.database_viewer_table.currentItemChanged.disconnect()
        self.database_viewer_table.clear()
        self.display_data_as_table()
        self.database_viewer_table.currentItemChanged.connect(
            self.database_populate_project_edit_fields
        )
        self.database_viewer_table.sortItems(0, QtCore.Qt.AscendingOrder)
        self.update()

        # If there is no project_data, dont let the user export nothing.
        if not self.database_table_data[0]:
            self.export_project_data_button.setEnabled(False)

    def project_data_add_new(self) -> None:
        self.project_data_loaded_data = {
            "project_number": None,
            "directory": None,
            "email_to": None,
            "email_cc": None,
            "email_bcc": None,
            "email_subject": None,
        }
        self.adding_new = True
        self.database_discard_edited_project_data()
        self.clear_project_data_entry_fields()
        self.database_save_edited_project_data_button.setText("Save New")
        self.database_save_edited_project_data_button.clicked.disconnect()
        self.database_save_edited_project_data_button.clicked.connect(
            self.project_data_save_new
        )

        return None

    def project_data_save_new(self):
        new_project_data = {}

        for col_name, widget in zip(
            ["email_to", "email_cc", "email_bcc"],
            [
                self.database_email_to_list_widget,
                self.database_email_cc_list_widget,
                self.database_email_bcc_list_widget,
            ],
        ):
            item_texts = []
            for i in range(widget.count()):
                if widget.item(i).text():
                    item_texts.append(widget.item(i).text())
            new_text = "; ".join(item_texts)
            new_project_data[col_name] = new_text

        new_project_data[
            "project_number"
        ] = self.database_project_number_line_edit.text()
        new_project_data[
            "directory"
        ] = self.database_project_directory_line_edit.text().replace("\\", "/")
        new_project_data[
            "email_subject"
        ] = self.database_project_email_subject_line_edit.text()

        new_entry_return = add_new_project_data(new_project_data)

        if new_entry_return is None:
            self.database_fetch("project_data")
            self.database_discard_edited_project_data()
            self.adding_new = False
            found_items = self.database_viewer_table.findItems(
                new_project_data["project_number"], QtCore.Qt.MatchExactly
            )
            if found_items:
                index_in_shown = None
                found_item = found_items[0]
                found_item_index = self.database_viewer_table.indexFromItem(found_item)
                first_index = None
                row_count = 0
                for row in range(self.database_viewer_table.rowCount()):
                    if not self.database_viewer_table.isRowHidden(row):
                        row_count += 1
                        for col in range(self.database_viewer_table.columnCount()):
                            shown_item = self.database_viewer_table.item(row, col)
                            index = self.database_viewer_table.indexFromItem(shown_item)
                            if first_index is None:
                                first_index = index
                            if found_item.text() == shown_item.text():
                                index_in_shown = True
                                break
                    if index_in_shown:
                        break
                if row_count == 0:
                    # If user currently has a filter with no results, and they add a new entry, remove their filter and show new entry
                    self.database_search_bar.setText("")
                    self.database_viewer_table.setCurrentIndex(found_item_index)
                elif index_in_shown is not None:
                    self.database_viewer_table.setCurrentIndex(found_item_index)
                else:
                    self.database_viewer_table.setCurrentIndex(first_index)
                self.database_save_edited_project_data_button.setText("Save Changes")
                self.database_save_edited_project_data_button.clicked.disconnect()
                self.database_save_edited_project_data_button.clicked.connect(
                    self.database_save_edited_project_data
                )
                self.database_populate_project_edit_fields()
            return

        # Return any errors and display to user, leaving data as is if any occurs
        add_new_error_dialog = QtWidgets.QMessageBox()
        add_new_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        add_new_error_dialog.setWindowTitle("Project Data Entry Error")
        add_new_error_dialog.setText(f"{new_entry_return}")
        add_new_error_dialog.exec()

    def import_project_data(self):

        self.importing = True
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            caption="Open Project Data File",
            dir="../../",
            filter="Comma Seperated Values (*.csv *.txt)",
        )

        if not file_name:
            return

        with open(file_name, "r") as imported_file:
            try:
                reader = csv.reader(imported_file)
                data_to_import = []
                for row in reader:
                    data_to_import.append(row)
            except csv.Error as e:
                try:
                    import_error_dialog = QtWidgets.QMessageBox()
                    import_error_dialog.setIcon(QtWidgets.QMessageBox.Information)
                    import_error_dialog.setWindowTitle("Invalid Import File")
                    import_error_dialog.setText(
                        f"File unable to be read as a csv.\n\n \
                        {e}"
                    )
                    import_error_dialog.exec()
                except:
                    pass
                finally:
                    self.importing = False
                    return

        # remove headers if present
        if "project_number" in data_to_import[0]:
            data_to_import = data_to_import[1:]

        # Display invalid data to user somehow so theyre aware not all data was imported properly
        # valid_data_to_import, _ = self.validate_data(data_to_import)

        valid_data_to_import = data_to_import

        self.process_button.setEnabled(False)
        self.export_project_data_button.setEnabled(False)
        self.export_project_data_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Importing...")
        )
        self.process_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Importing...")
        )
        self.progress_popup = LoadingWidget(
            title="Importing", text="Importing Project Data..."
        )
        self.import_worker = ImportProjectDataThread(valid_data_to_import)
        self.import_worker.signals.progress.connect(self.evt_loading_widget_progress)
        self.import_worker.signals.result.connect(self.evt_import_complete)
        self.thread_pool.start(self.import_worker)

    def validate_data(self, data: list) -> list[list, list]:
        valid_data = []
        invalid_data = []
        for data_row in data:
            data_is_valid = True
            for [
                project_number,
                directory,
                email_to,
                email_cc,
                email_bcc,
                email_subject,
            ] in data_row:
                project_number = scrub(project_number)
                directory = os.path.abspath(directory.replace("\\", "/"))
                email_subject = scrub(email_subject)
                for i, email_list in enumerate([email_to, email_cc, email_bcc]):
                    temp_emails = []
                    email_list = [email.strip() for email in email_list.split(";")]
                    for email in email_list:
                        # If email is a blank string just ignore, dont need to raise invalid_data
                        if not email:
                            continue

                        # If email is valid, add to temp list
                        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                            temp_emails.append(email)
                        # If email not valid, change bool so whole row will get added to invalid data list to show user after validation finished
                        else:
                            data_is_valid = False
                    if i == 0:
                        email_to = ";".join(temp_emails)
                    elif i == 1:
                        email_cc = ";".join(temp_emails)
                    elif i == 2:
                        email_bcc = ";".join(temp_emails)
            if data_is_valid:
                valid_data.append(
                    [
                        project_number,
                        directory,
                        email_to,
                        email_cc,
                        email_bcc,
                        email_subject,
                    ]
                )
            else:
                invalid_data.append(
                    [
                        project_number,
                        directory,
                        email_to,
                        email_cc,
                        email_bcc,
                        email_subject,
                    ]
                )
        return valid_data, invalid_data

    def delete_all_project_data(self):

        if self.database_viewer_table.rowCount() == 0:
            return

        delete_all_dialog = QtWidgets.QMessageBox()
        delete_all_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        delete_all_dialog.setWindowTitle("Delete All Project Data?")
        delete_all_dialog.setText(
            f"Are you sure you want to delete all project data?.\
                \n \
                \nPress 'Proceed' to delete all\
                \nPress 'Cancel' to go back"
        )
        delete_all_dialog.addButton("Proceed", QtWidgets.QMessageBox.YesRole)
        delete_all_dialog.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        delete_all_reply = delete_all_dialog.exec()
        if delete_all_reply != 0:
            return

        self.process_button.setEnabled(False)
        self.import_project_data_button.setEnabled(False)
        self.export_project_data_button.setEnabled(False)
        self.progress_popup = LoadingWidget(
            title="Deleting", text="Deleting Project Data..."
        )
        self.delete_worker = DeleteProjectDataThread()
        self.delete_worker.signals.progress.connect(self.evt_loading_widget_progress)
        self.delete_worker.signals.result.connect(self.evt_delete_all_complete)
        self.thread_pool.start(self.delete_worker)

    def export_project_data(self):

        export_location = QtWidgets.QFileDialog.getExistingDirectory(
            caption="Select Export Location", dir="../../"
        )

        if not export_location:
            return

        self.process_button.setEnabled(False)
        self.import_project_data_button.setEnabled(False)
        self.import_project_data_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Exporting...")
        )
        self.process_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Exporting...")
        )
        self.progress_popup = LoadingWidget(
            title="Exporting", text="Exporting Project Data..."
        )
        self.export_worker = ExportProjectDataThread(export_location)
        self.export_worker.signals.progress.connect(self.evt_loading_widget_progress)
        self.export_worker.signals.result.connect(self.evt_export_complete)
        self.thread_pool.start(self.export_worker)

    def database_project_directory(self):
        project_directory_location = QtWidgets.QFileDialog.getExistingDirectory(
            caption="Select Export Location", dir="../../"
        )

        if not project_directory_location:
            return None

        self.database_project_directory_line_edit.setText(project_directory_location)

        self.project_data_change_check(
            self.database_project_directory_line_edit, "directory"
        )

    def database_discard_edited_project_data(self):
        self.project_data_changed = False
        self.database_discard_edited_project_data_button.setEnabled(False)
        self.database_save_edited_project_data_button.setEnabled(False)
        if not self.adding_new:
            self.database_viewer_table.setCurrentIndex(self.project_data_loaded_id)

    def database_save_edited_project_data(self):
        # check each field to validate input data
        # Look into QValidator

        # If selected row is same as one already loaded, do nothing

        # whichever ones arent valid, notify user and return data as is

        # If all is valid, send to data_handler to update the row
        new_project_data = {}

        for col_name, widget in zip(
            ["email_to", "email_cc", "email_bcc"],
            [
                self.database_email_to_list_widget,
                self.database_email_cc_list_widget,
                self.database_email_bcc_list_widget,
            ],
        ):
            item_texts = []
            for i in range(widget.count()):
                if widget.item(i).text():
                    item_texts.append(widget.item(i).text())
            new_text = "; ".join(item_texts)
            new_project_data[col_name] = new_text

        new_project_data[
            "project_number"
        ] = self.database_project_number_line_edit.text()
        new_project_data[
            "directory"
        ] = self.database_project_directory_line_edit.text().replace("\\", "/")
        new_project_data[
            "email_subject"
        ] = self.database_project_email_subject_line_edit.text()

        update_return = update_project_data(
            self.project_data_loaded_data, new_project_data
        )

        if update_return is None:
            self.database_fetch("project_data")
            self.database_discard_edited_project_data()
            return

        # Return any errors and display to user, leaving data as is if any occurs
        update_error_dialog = QtWidgets.QMessageBox()
        update_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        update_error_dialog.setWindowTitle("Project Data Update Error")
        update_error_dialog.setText(
            f"Error occured updating project data\n\n \
            {update_return}"
        )
        update_error_dialog.exec()

    def project_data_change_check(self, widget, project_data_type):
        # Multiple widgets need to be chacked so if the passed widget is a QtLineEdit then just get the text
        # If it is a QtListWidget then it is the e-mail field, so join each list item together into a string
        # to compare to the database/table result
        if isinstance(widget, QtWidgets.QLineEdit):
            new_text = widget.text()
        else:
            item_texts = []
            for i in range(widget.count()):
                if widget.item(i).text():
                    item_texts.append(widget.item(i).text())
            new_text = "; ".join(item_texts)

        # If there isnt any loaded data yet then user is entering new data. Check if field has any value as well.
        # If they do, then dont set project_data_changed because no data has been changed, we are creating new data
        # Check new_text first to short circuit check
        if new_text and self.project_data_loaded_data.get(project_data_type) is None:
            self.database_discard_edited_project_data_button.setEnabled(True)
            self.database_save_edited_project_data_button.setEnabled(True)
        elif self.project_data_loaded_data.get(project_data_type) != new_text:
            self.project_data_changed = True
            self.database_discard_edited_project_data_button.setEnabled(True)
            self.database_save_edited_project_data_button.setEnabled(True)

    def clear_project_data_entry_fields(self):
        self.database_email_to_list_widget.clear()
        self.database_email_cc_list_widget.clear()
        self.database_email_bcc_list_widget.clear()
        self.database_project_number_line_edit.clear()
        self.database_project_directory_line_edit.clear()
        self.database_project_email_subject_line_edit.clear()

    def database_populate_project_edit_fields(self):

        self.database_save_edited_project_data_button.setText("Save Changes")
        self.database_save_edited_project_data_button.clicked.disconnect()
        self.database_save_edited_project_data_button.clicked.connect(
            self.database_save_edited_project_data
        )
        # If user is creating a new entry and they decide to clik away into the table.
        # Just discard changes and load data from the table
        if self.adding_new:
            # If user clicks a new row, reset the save new/save changes button
            self.project_data_changed = False
            if self.project_data_loaded_id is not None:
                self.database_viewer_table.setCurrentIndex(self.project_data_loaded_id)
            self.adding_new = False

        self.database_delete_project_data_button.setEnabled(True)
        # if self.project_data_loaded_id == self.database_viewer_table.selectionModel().currentIndex():
        #     return

        # If user edited the project data ask if they want to discard or cancel
        if self.project_data_changed:
            overwrite = QtWidgets.QMessageBox()
            overwrite.setIcon(QtWidgets.QMessageBox.Warning)
            overwrite.setWindowTitle("Project Data Changed")
            overwrite.setText(
                f"Project Data has been changed.\
                    \n \
                    \nPress 'Proceed' to discard changes\
                    \nPress 'Cancel' to go back"
            )
            overwrite.addButton("Proceed", QtWidgets.QMessageBox.YesRole)
            overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
            overwrite_reply = overwrite.exec()
            if overwrite_reply != 0:
                return

        self.project_data_loaded_id = (
            self.database_viewer_table.selectionModel().currentIndex()
        )

        # if project data not changed then load data
        self.database_discard_edited_project_data()
        self.clear_project_data_entry_fields()

        if self.database_viewer_table.rowCount() > 0:
            self.database_project_number_line_edit.setText(
                self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 0
                ).text()
            )
            self.database_project_directory_line_edit.setText(
                self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 1
                ).text()
            )
            self.database_project_email_subject_line_edit.setText(
                self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 5
                ).text()
            )

            self.project_data_loaded_data = {
                "project_number": self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 0
                ).text(),
                "directory": self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 1
                ).text(),
                "email_to": self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 2
                ).text(),
                "email_cc": self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 3
                ).text(),
                "email_bcc": self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 4
                ).text(),
                "email_subject": self.database_viewer_table.item(
                    self.database_viewer_table.currentRow(), 5
                ).text(),
            }

            for i in [2, 3, 4]:
                email_addresses = (
                    self.database_viewer_table.item(
                        self.database_viewer_table.currentRow(), i
                    )
                    .text()
                    .split(";")
                )
                email_addresses = [address.strip() for address in email_addresses]

                for email_address in email_addresses:
                    # Dont add blank emails to list (sometimes users add rogue ; to email list)
                    if email_address is None or email_address == "":
                        continue
                    email_address_item = QtWidgets.QListWidgetItem(email_address)
                    email_address_item.setFlags(
                        email_address_item.flags() | QtCore.Qt.ItemIsEditable
                    )
                    if i == 2:
                        self.database_email_to_list_widget.addItem(email_address_item)
                    elif i == 3:
                        self.database_email_cc_list_widget.addItem(email_address_item)
                    elif i == 4:
                        self.database_email_bcc_list_widget.addItem(email_address_item)

    def filter_table(self):
        # Get search term from search bar
        search_term = self.database_search_bar.text()

        # Hide all rows and columns in the table
        for row in range(self.database_viewer_table.rowCount()):
            self.database_viewer_table.setRowHidden(row, True)
        for column in range(self.database_viewer_table.columnCount()):
            self.database_viewer_table.setColumnHidden(column, True)
        row_count = 0
        # Show rows and columns that contain the search term
        for row in range(self.database_viewer_table.rowCount()):
            for column in range(self.database_viewer_table.columnCount()):
                try:
                    item_text = self.database_viewer_table.item(row, column).text()
                    if search_term in item_text:
                        # If the search term is found, show the entire row and break out of the loop
                        self.database_viewer_table.setRowHidden(row, False)
                        # Show all cells in the row
                        for column in range(self.database_viewer_table.columnCount()):
                            self.database_viewer_table.setColumnHidden(column, False)
                        row_count += 1
                        break
                except AttributeError:
                    pass

        if row_count > 0 and self.project_data_loaded_id is not None:
            self.database_delete_project_data_button.setEnabled(True)

    def display_data_as_table(self):
        """Displays the fetched data into a table format for users to see

        Args:
            data (list): database/table data in format [[data], [headers]]
        """
        self.database_viewer_table.setSortingEnabled(False)
        # self.database_viewer_table.clear()
        self.database_viewer_table.setRowCount(0)
        table_widget_item = QtWidgets.QTableWidgetItem
        # try to assign data to variables
        try:
            [data, headers] = [self.database_table_data[0], self.database_table_data[1]]
            _ = len(data)
        except (IndexError, ValueError):
            self.database_viewer_table.setColumnCount(1)
            self.database_viewer_table.setItem(0, 0, table_widget_item("No Data"))
            return

        self.database_viewer_table.setColumnCount(len(headers))
        self.database_viewer_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        # self.database_viewer_table.horizontalHeader().setSectionResizeMode(
        #     QtWidgets.QHeaderView.Interactive)
        # Add headers to table
        for col, header_text in enumerate(headers):
            self.database_viewer_table.setHorizontalHeaderItem(
                col, table_widget_item(header_text)
            )
        # Add data to table
        for row, row_data in enumerate(data):
            self.database_viewer_table.insertRow(row)
            for column, item in enumerate(row_data):
                self.database_viewer_table.setItem(
                    row, column, table_widget_item(str(item))
                )
        self.filter_table()
        self.database_viewer_table.setSortingEnabled(True)

    def format_file_profile_dropdown(self):
        """Transforms profiles into a list with profile name and identifier text. profiles list comes from fetch_file_profiles from data_handler.

        Returns:
            list: Items to display in profiles dropdown
        """
        dropdown_items = []
        results = fetch_file_profiles()
        if results:
            dropdown_items = ["".join([s[0], " - ", s[1]]) for s in results]
        return dropdown_items

    def display_active_parameters(self, file_profile_item):
        """Fills in active parameters list based off the currently chosen file_profile dropdown item.

        Args:
            file_profile_text (str): file_profile text as format "file_profile - example text"
        """
        file_profile_text = file_profile_item.text()
        self.settings_profile_parameters_list_widget.clear()
        self.settings_profile_naming_scheme_line_edit.clear()
        if not file_profile_text.split(" - ")[-1]:
            return
        self.active_params_data, self.active_file_naming_scheme = fetch_active_params(
            file_profile_text.split(" - ")[0]
        )
        self.settings_profile_naming_scheme_line_edit.setText(
            self.active_file_naming_scheme
        )
        for [param_id, param_name, example] in self.active_params_data:
            self.active_param_list_item = QtWidgets.QListWidgetItem(param_name)
            self.active_param_list_item.setData(QtCore.Qt.UserRole, param_id)
            self.settings_profile_parameters_list_widget.addItem(
                self.active_param_list_item
            )

    def apply_file_name_pattern(self):
        """Handles the saving of a file profile's file naming pattern to the database"""

        connection, cursor = db_connect(db_file_path)

        try:
            profile_name = (
                self.settings_profile_templates_list_widget.currentText().split(" - ")[
                    0
                ]
            )
            file_profile_filename_pattern = cursor.execute(
                """SELECT file_naming_format FROM profiles WHERE unique_profile_name = ?""",
                (scrub(profile_name),),
            ).fetchone()

            # If file_profile already has a naming pattern, ask if user wants ot overwrite
            if file_profile_filename_pattern[0] is not None:
                overwrite = QtWidgets.QMessageBox()
                overwrite.setIcon(QtWidgets.QMessageBox.Warning)
                overwrite.setWindowTitle("Filename Pattern Already Found")
                overwrite.setText(
                    f"Unique identifier already in database \
                        \n \
                        \n{file_profile_filename_pattern[0]} \
                        \n "
                )
                overwrite.addButton("Overwrite", QtWidgets.QMessageBox.YesRole)
                overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                overwrite_reply = overwrite.exec()
                if overwrite_reply == 0:
                    update_file_profile_file_name_pattern(
                        profile_name,
                        self.settings_profile_naming_scheme_line_edit.text(),
                        connection,
                        cursor,
                    )
            else:
                update_file_profile_file_name_pattern(
                    profile_name,
                    self.settings_profile_naming_scheme_line_edit.text(),
                    connection,
                    cursor,
                )
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            db_disconnect(connection, cursor)

    def intersects_or_enclosed(self, rec1, rec2):
        """Checks whether two bounding boxes intersect or are enclosed by one another.

        Args:
            rec1 (NamedTuple): first bounding box = namedtuple('RECTANGLE', 'x1 x2 y1 y2')
            rec2 (NamedTuple): second bounding box = namedtuple('RECTANGLE', 'x1 x2 y1 y2')

        Returns:
            boolean: True if intersecting or enclosed by one another, False if completely seperate.
        """

        # Could simplify all x and y checks into single if statement but easier to read this way
        # Future me will appreciate

        def intersects():
            # Check if rec1 intersects rec2 or rec2 intersects rec1
            if (
                (rec2.x2 >= rec1.x1 and rec2.x2 <= rec1.x2)
                or (rec2.x1 >= rec1.x1 and rec2.x1 <= rec1.x2)
                or (
                    (rec1.x2 >= rec2.x1 and rec1.x2 <= rec2.x2)
                    or (rec1.x1 >= rec2.x1 and rec1.x1 <= rec2.x2)
                )
            ):
                x_match = True
            else:
                x_match = False
            if (
                (rec2.y2 >= rec1.y1 and rec2.y2 <= rec1.y2)
                or (rec2.y1 >= rec1.y1 and rec2.y1 <= rec1.y2)
            ) or (
                (rec1.y2 >= rec2.y1 and rec1.y2 <= rec2.y2)
                or (rec1.y1 >= rec2.y1 and rec1.y1 <= rec2.y2)
            ):
                y_match = True
            else:
                y_match = False
            if x_match and y_match:
                return True
            else:
                return False

        def enclosed():
            # Check if rec1 is enclosed by rec2 or rec2 is enclosed by rec1
            if (rec2.x1 >= rec1.x1 and rec2.x2 <= rec1.x2) or (
                rec1.x1 >= rec2.x1 and rec1.x2 <= rec2.x2
            ):
                x_match = True
            else:
                x_match = False
            if (rec2.y1 >= rec1.y1 and rec2.y2 <= rec1.y2) or (
                rec1.y1 >= rec2.y1 and rec1.y2 <= rec2.y2
            ):
                y_match = True
            else:
                y_match = False
            if x_match and y_match:
                return True
            else:
                return False

        return intersects() or enclosed()

    def display_example_file_name(self):
        """When file name line edit is changed, replace any instance of '{parameter}' with an example string from that parameter and replace the example line edit with that text."""
        replace_result = self.settings_profile_naming_scheme_line_edit.text()
        if r"{doc_num}" in replace_result[len(r"{doc_num}") :]:
            replace_result = replace_result.replace(r"{doc_num}", "")
            replace_result = r"{doc_num}" + replace_result
            self.settings_profile_naming_scheme_line_edit.setText(replace_result)
        for [param_id, param_name, example] in self.active_params_data:
            replace_result = replace_result.replace(
                "".join(["{", param_name, "}"]), example
            )
        self.settings_profile_naming_scheme_example_line_edit.setText(replace_result)

    def add_active_param_line_edit(self):
        """Upon clicking a parameter in the parameter list, {parameter}' gets inserted to the line edit"""
        current_cursor_position = (
            self.settings_profile_naming_scheme_line_edit.cursorPosition()
        )
        active_param_name = (
            self.settings_profile_parameters_list_widget.currentItem().text()
        )
        # active_param_id = str(self.active_parameters_list_widget.currentItem().data(
        #     QtCore.Qt.UserRole))

        param = "{" + active_param_name + "}"
        chars = list(self.settings_profile_naming_scheme_line_edit.text())
        chars.insert(current_cursor_position, param)
        new_text = "".join(chars)
        self.settings_profile_naming_scheme_line_edit.setText(new_text)
        self.settings_profile_naming_scheme_line_edit.setFocus()
        self.settings_profile_naming_scheme_line_edit.setCursorPosition(
            current_cursor_position + len(param)
        )

    def apply_unique_file_indentifier(self):
        """Handles creating a new file_profile based off of the bounding box for identifiable text"""
        if self.template_display.begin.isNull():
            return

        # If a pdf file isnt opened, then warn user and return
        if not self.profile_file_loaded:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("No Profile Loaded")
            no_file_profile.setText("You must first select a template file to open.")
            no_file_profile.exec()
            return

        # Bounding box can be too small and cause issues when analyzing text
        # If width and height less than 5 pixels, warn user and return
        if self.template_display.image_area_too_small:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("Area Too Small")
            no_file_profile.setText("Data area too small. Please choose a larger area.")
            no_file_profile.exec()
            return

        # If there is no bounding box, let user know to draw one
        if self.template_display.begin.isNull():
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("Select Identifier")
            no_file_profile.setText(
                "Use the mouse to click and drag a bounding box around the desired profile identifier."
            )
            no_file_profile.exec()
            return

        requirements_met = False
        cancelled = False
        # Make sure the file_profile_field is not left blank
        # Display an error if left blank and bring the button box back up to retry.
        # If cancelled or requirements met, exit loop
        while not requirements_met and not cancelled:
            self.apply_unique_file_identifier_dialog = ApplyFoundData(
                self.template_display.true_coords(),
                self.template_display.found_text,
                dialog_type={"file_profile": True},
            )
            if self.apply_unique_file_identifier_dialog.exec():

                if (
                    self.apply_unique_file_identifier_dialog.description.text()
                    .strip()
                    .lower()
                    .replace(" ", "_")
                    == ""
                ):
                    no_file_profile = QtWidgets.QMessageBox()
                    no_file_profile.setIcon(QtWidgets.QMessageBox.Critical)
                    no_file_profile.setWindowTitle("No Profile Name")
                    no_file_profile.setText("Please enter a profile name.")
                    no_file_profile.exec()
                else:
                    requirements_met = True
            else:
                cancelled = True

        if not cancelled:

            unique_file_type_identifier = (
                self.apply_unique_file_identifier_dialog.text_input.text().replace(
                    "\n", " "
                )
            )
            file_profile_name = (
                self.apply_unique_file_identifier_dialog.description.text()
                .strip()
                .lower()
                .replace(" ", "_")
            )
            [x_1, x_2, y_1, y_2] = self.template_display.true_coords()

            # check if identiying text can be found in any of the existing profiles
            connection, cursor = db_connect(db_file_path)
            indentifier_text_found = False
            try:
                unique_texts_query = """SELECT profile_id, profile_identifier_text, unique_profile_name FROM profiles"""
                unique_texts = cursor.execute(unique_texts_query).fetchall()
                for profile_id, unique_text, profile_name in unique_texts:
                    if (
                        unique_file_type_identifier.replace("\n", " ").strip().lower()
                        in unique_text.replace("\n", " ").strip().lower()
                        or unique_text.replace("\n", " ").strip().lower()
                        in unique_file_type_identifier.replace("\n", " ")
                        .strip()
                        .lower()
                    ):
                        indentifier_text_found = True
                        break
            except Exception as e:
                print(e)
            finally:
                db_disconnect(connection, cursor)

            identifier_intersects = False
            # if identifier already in database, check if current rect bounds intersects with matching profile entry
            if indentifier_text_found:
                connection, cursor = db_connect(db_file_path)
                try:
                    prof_txt_loc_query = (
                        """SELECT x_1, x_2, y_1, y_2 FROM profiles WHERE profile_id=?"""
                    )
                    [db_x_1, db_x_2, db_y_1, db_y_2] = cursor.execute(
                        prof_txt_loc_query, (profile_id,)
                    ).fetchone()

                    RECTANGLE = namedtuple("RECTANGLE", "x1 x2 y1 y2")
                    current_box = RECTANGLE(x_1, x_2, y_1, y_2)
                    db_box = RECTANGLE(db_x_1, db_x_2, db_y_1, db_y_2)

                    if self.intersects_or_enclosed(current_box, db_box):
                        identifier_intersects = True
                except Exception as e:
                    print(e)
                finally:
                    db_disconnect(connection, cursor)

            # If identifer text found and intersects warn user

            if indentifier_text_found and identifier_intersects:
                profile_issue = QtWidgets.QMessageBox()
                profile_issue.setIcon(QtWidgets.QMessageBox.Warning)
                profile_issue.setWindowTitle("Problematic Text and Location")
                profile_issue.setText(
                    f"Potential profile conflict:\
                        \n\nThe location you chose produces identifying text '{unique_file_type_identifier}'.\nExisting profile with name '{profile_name}' has identidying text '{unique_text}' near the same location.\
                        \n\nIf you continue these profiles may get mis-detected as eachother during processing\
                        \n\nSelect Continue to add entry into database \
                        \nSelect Cancel to choose another unique identifier"
                )
                profile_issue.addButton("Continue", QtWidgets.QMessageBox.YesRole)
                profile_issue.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                profile_issue_reply = profile_issue.exec()
                if profile_issue_reply != 0:
                    return

            # At this point the user will have an identifying text that may or may not be unique, and a location that may or may not be unique but they want to enter it

            add_data = """INSERT INTO profiles(profile_identifier_text, unique_profile_name, x_1, x_2, y_1, y_2) VALUES(?,?,?,?,?,?)"""
            data = (unique_file_type_identifier, file_profile_name, x_1, x_2, y_1, y_2)
            connection, cursor = db_connect(db_file_path)
            try:
                cursor.execute(add_data, data)
                connection.commit()
                file_profile_id = cursor.execute(
                    """SELECT profile_id FROM profiles WHERE unique_profile_name=?""",
                    (file_profile_name,),
                ).fetchone()[0]
                self.current_file_profile = file_profile_id
                self.apply_unique_profile_project_number_button.setEnabled(True)
                self.apply_unique_profile_parameter_button.setEnabled(True)

            except Exception as e:
                print(f"Error inserting data: {e}")
                overwrite = QtWidgets.QMessageBox()
                overwrite.setIcon(QtWidgets.QMessageBox.Warning)
                overwrite.setWindowTitle("File Profile Name Not Unique")
                overwrite.setText(
                    "Profile name already in database \
                        \n\nSelect Overwrite to overwrite existing file profile and its data \
                        \nSelect Show Existing to see and/or add data for the existing file profile \
                        \nSelect Cancel to choose another unique identifier"
                )
                overwrite.addButton("Overwrite", QtWidgets.QMessageBox.YesRole)
                overwrite.addButton("See Existing", QtWidgets.QMessageBox.NoRole)
                overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                overwrite_reply = overwrite.exec()
                if overwrite_reply == 0:
                    try:
                        file_profile_id = cursor.execute(
                            """SELECT profile_id FROM profiles WHERE unique_profile_name=?""",
                            (file_profile_name,),
                        ).fetchone()[0]
                        cursor.execute(
                            """DELETE FROM profiles WHERE profile_id=?""",
                            (file_profile_id,),
                        )
                        print("Deleted Entry from profiles")
                        cursor.execute(add_data, data)
                        connection.commit()
                        print("Created New profiles Entry")
                        file_profile_id = cursor.execute(
                            """SELECT profile_id FROM profiles WHERE unique_profile_name=?""",
                            (file_profile_name,),
                        ).fetchone()[0]
                        self.current_file_profile = file_profile_id
                        self.apply_unique_profile_project_number_button.setEnabled(True)
                        self.apply_unique_profile_parameter_button.setEnabled(True)

                    except Exception as e:
                        print(f"Error overwriting existing entry. {e}")
                        overwrite_error = QtWidgets.QMessageBox()
                        overwrite_error.setIcon(QtWidgets.QMessageBox.Critical)
                        overwrite_error.setWindowTitle("Overwrite Error")
                        overwrite_error.setText(
                            "Error overwriting existing entry. Please try again or submit an issue if problem persists."
                        )
                        overwrite_error.exec()
                elif overwrite_reply == 1:
                    file_profile_id = cursor.execute(
                        """SELECT profile_id FROM profiles WHERE unique_profile_name=?""",
                        (file_profile_name,),
                    ).fetchone()[0]
                    self.current_file_profile = file_profile_id
                    self.apply_unique_profile_project_number_button.setEnabled(True)
                    self.apply_unique_profile_parameter_button.setEnabled(True)

                    try:
                        self.template_display.reset_rect()
                        self.paint_existing_data_rects()
                    except Exception as e:
                        print(e)
                        pass
            finally:
                db_disconnect(connection, cursor)
                self.settings_profile_templates_list_widget.clear()
                self.settings_profile_templates_list_widget.addItems(
                    self.format_file_profile_dropdown()
                )
            try:
                self.template_display.reset_rect()
                self.paint_existing_data_rects()
            except Exception as e:
                print(e)
                pass
        else:
            print("cancelled")

    def apply_unique_profile_parameter(self, project_number=False):
        """Handles the inserting of a new profile parameter into the database."""

        # If a profile isn't loaded yet, warn user and return
        if self.current_file_profile == 0:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Critical)
            no_file_profile.setWindowTitle("No Profile Loaded")
            no_file_profile.setText(
                "Please create a new file profile in order to add data locations."
            )
            no_file_profile.exec()
            return

        if self.template_display.begin.isNull():
            return

        # If bounding box area too small, warn user and return
        if self.template_display.image_area_too_small:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("Area Too Small")
            no_file_profile.setText("Data area too small. Please choose a larger area.")
            no_file_profile.exec()
            return
        if project_number:
            dialog = "project_number"
        else:
            dialog = "parameter"
        # Show user found text and let them choose a unique parameter name for the profile
        unique_profile_parameter = False
        while not unique_profile_parameter:
            self.apply_unique_profile_parameter_dialog = ApplyFoundData(
                self.template_display.true_coords(),
                self.template_display.found_text,
                dialog_type={dialog: True},
            )
            if self.apply_unique_profile_parameter_dialog.exec():

                # If clicked confirm, then add project_number or parameter to database, if exists ask user to overwrite?
                unique_file_data_information = (
                    self.apply_unique_profile_parameter_dialog.text_input.text()
                )
                if project_number:
                    description = "project_number"
                    regex = None
                else:
                    description = (
                        self.apply_unique_profile_parameter_dialog.description.text()
                        .strip()
                        .lower()
                        .replace(" ", "_")
                    )

                    if "project_number" in description:
                        add_data_error = QtWidgets.QMessageBox()
                        add_data_error.setIcon(QtWidgets.QMessageBox.Critical)
                        add_data_error.setWindowTitle("Parameter Name Error")
                        add_data_error.setText(
                            f"project_number is a reserved parameter name. To set the project_number paramater, use the 'Apply Project Number' button."
                        )
                        add_data_error.exec()
                        continue

                    regex = self.apply_unique_profile_parameter_dialog.regex.text()
                    if not regex:
                        regex = None
                example_text = (
                    self.apply_unique_profile_parameter_dialog.text_input.text()
                    .strip()
                    .replace(" ", "-")
                    .replace("---", "-")
                    .replace("--", "-")
                )

                [x_1, x_2, y_1, y_2] = self.template_display.true_coords()
                try:
                    connection, cursor = db_connect(db_file_path)
                    unique_parameter_query_result = cursor.execute(
                        """SELECT * FROM profile_parameters WHERE profile_id=? and description=?;""",
                        (self.current_file_profile, description),
                    ).fetchone()
                except Exception:
                    pass
                finally:
                    db_disconnect(connection, cursor)

                add_data = """INSERT INTO profile_parameters(profile_id, description, regex, x_1, x_2, y_1, y_2, example_text) VALUES(?,?,?,?,?,?,?,?)"""
                data = (
                    self.current_file_profile,
                    description,
                    regex,
                    x_1,
                    x_2,
                    y_1,
                    y_2,
                    scrub(example_text),
                )

                # if the parameter name is not unique, warn user and let them try again (could do a textChanged.connect and check then, may be too slow)
                if unique_parameter_query_result is not None:
                    overwrite = QtWidgets.QMessageBox()
                    overwrite.setIcon(QtWidgets.QMessageBox.Warning)
                    if project_number:
                        overwrite.setWindowTitle("Project Number Already Set")
                        overwrite_dialog_text = "Project number location already chosen"
                    else:
                        overwrite.setWindowTitle("Parameter Name Already Used")
                        overwrite_dialog_text = "Parameter name already used"
                    overwrite_dialog_text += "\n\nSelect Overwrite to overwrite existing \
                            \nSelect Cancel to return"
                    overwrite.setText(overwrite_dialog_text)
                    overwrite.addButton("Overwrite", QtWidgets.QMessageBox.YesRole)
                    overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                    overwrite_reply = overwrite.exec()
                    if overwrite_reply == 0:
                        try:
                            connection, cursor = db_connect(db_file_path)
                            parameter_id = cursor.execute(
                                """SELECT parameter_id FROM profile_parameters WHERE description=? AND profile_id=?""",
                                (description, self.current_file_profile),
                            ).fetchone()[0]
                            cursor.execute(
                                """DELETE FROM profile_parameterss WHERE parameter_id=?""",
                                (parameter_id,),
                            )
                            print("Deleted Entry from profile_parameters")
                            cursor.execute(add_data, data)
                            connection.commit()
                            print("Created New profiles Entry")
                        except Exception as e:
                            print(f"Error overwriting existing entry. {e}")
                            overwrite_error = QtWidgets.QMessageBox()
                            overwrite_error.setIcon(QtWidgets.QMessageBox.Critical)
                            overwrite_error.setWindowTitle("Overwrite Error")
                            overwrite_error.setText(
                                "Error overwriting existing entry. Please try again or submit an issue if problem persists."
                            )
                            overwrite_error.exec()
                        finally:
                            db_disconnect(connection, cursor)
                            unique_profile_parameter = True
                    else:
                        # cancelled
                        if project_number:
                            break
                # if parameter name is unique, insert into parameter table
                else:
                    add_data = """INSERT INTO profile_parameters(profile_id, description, regex, x_1, x_2, y_1, y_2, example_text) VALUES(?,?,?,?,?,?,?,?)"""
                    data = (
                        self.current_file_profile,
                        description,
                        regex,
                        x_1,
                        x_2,
                        y_1,
                        y_2,
                        scrub(example_text),
                    )
                    try:
                        connection, cursor = db_connect(db_file_path)
                        cursor.execute(add_data, data)
                        connection.commit()
                    except Exception as e:
                        print(f"Error inserting data: {e}")
                        add_data_error = QtWidgets.QMessageBox()
                        add_data_error.setIcon(QtWidgets.QMessageBox.Critical)
                        add_data_error.setWindowTitle("Add Data Error")
                        add_data_error.setText(
                            f"Error occured when adding data to database: {e}"
                        )
                        add_data_error.exec()
                    finally:
                        db_disconnect(connection, cursor)
                        self.apply_unique_profile_parameter_button.setEnabled(True)
                        unique_profile_parameter = True
            else:
                print("cancelled")
                break
        # After clicking button, draw existing parameter bounding boxes on top of template file
        try:
            self.template_display.reset_rect()
            self.paint_existing_data_rects()
        except Exception as e:
            print(e)
            pass

    def paint_existing_data_rects(self):
        """Draws bounding boxes on top of loaded template file for user to see which data is already being analyzed for each profile"""
        connection, cursor = db_connect(db_file_path)
        try:
            select_rects = """SELECT x_1, x_2, y_1, y_2, description FROM profile_parameters WHERE profile_id=?;"""
            rects_data = cursor.execute(
                select_rects, (self.current_file_profile,)
            ).fetchall()
            select_profile_rect = """SELECT x_1, x_2, y_1, y_2, unique_profile_name FROM profiles WHERE profile_id=?;"""
            rects_profile_data = cursor.execute(
                select_profile_rect, (self.current_file_profile,)
            ).fetchone()
            # print(rects_data)
            if rects_data or rects_profile_data:
                try:
                    self.template_display.set_data_info(rects_data, rects_profile_data)
                    # TemplateWidget.coords = rects
                    # print(f"templatedisplay.coords = {self.template_display.data_info}")
                    self.template_display.update()
                except Exception as e:
                    print(e)
                    pass
        except Exception as e:
            print(e)
            pass
        finally:
            db_disconnect(connection, cursor)

    def file_profile_template_dialog(self):
        """Opens dialog to choose files"""
        self.current_file_profile = 0
        # TODO: Update default search location before creating prod file
        # self.dialog = QtWidgets.QFileDialog(directory=str(
        #     os.path.abspath(os.path.join(os.getcwd(), "test_files"))))
        self.file_profile_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            caption="Select a PDF To Use As Template", filter="PDF (*.pdf)"
        )
        if self.file_profile_path:
            self.file_template_profile_name_label.clear()
            self.analyze_worker = WorkerAnalyzeThread(
                file_name=self.file_profile_path,
                test=self.test,
                analyzed=self.analyzed,
                template=True,
            )
            self.progress_popup = LoadingWidget(
                title="Template Check", text="Comparing file to existing profiles..."
            )
            self.analyze_worker.signals.progress.connect(
                self.evt_loading_widget_progress
            )
            self.analyze_worker.signals.result.connect(self.evt_analyze_complete)
            self.thread_pool.start(self.analyze_worker)

    def evt_loading_widget_progress(self, value):
        self.progress_popup.update_val(value)

    def update_template_pixmap(self):
        """Displays PDF file to be used for updating/creating a file_profile"""

        image_jpeg = []
        try:
            image_jpeg = convert_from_path(
                self.file_profile_path,
                fmt="jpeg",
                poppler_path=poppler_path,
                single_file=True,
            )
            img_byte_arr = io.BytesIO()
            image_jpeg[0].save(img_byte_arr, format="jpeg")
            img_byte_arr = img_byte_arr.getvalue()

            self.template_display.deleteLater()
            self.template_display = TemplateWidget(img_byte_arr, image_jpeg[0])

            updated_width = self.template_display.scaled_width() + 25
            updated_height = (
                self.template_display.scaled_height()
                + self.select_template_file.height()
                + self.file_template_tab_line_1.height() * 3
                + 25
            )

            self.resize(int(updated_width), int(updated_height))

            self.file_template_tab_layout.addWidget(self.template_display)
            self.update()

            self.profile_file_loaded = True
        except Exception as e:
            print(e)

    # TODO: Update this function
    def email_button_handler(self):
        return
        # signature_path = os.path.abspath(os.path.join(
        #     home_dir + r"\\Signature\\concrete.htm"))
        # signature_path_28 = os.path.abspath(os.path.join(
        #     home_dir + r"\\Signature\\concrete28.htm"))
        # if not self.analyzed and self.file_names:
        #     if os.path.isfile(signature_path):
        #         with open(signature_path, "r") as file:
        #             body_text = file.read()
        #         with open(signature_path_28, "r") as file:
        #             body_text_28 = file.read()

        #     else:
        #         # print("Signature File Not Found")
        #         body_text = ""
        #         pass
        #     msg = QtWidgets.QMessageBox()
        #     button_reply = msg.question(msg, "", "Do you want to create e-mails for non-analyzed files?",
        #                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        #     if button_reply == QtWidgets.QMessageBox.No:
        #         self.status_output_box.appendPlainText(
        #             "E-Mails not generated\n")
        #     elif button_reply == QtWidgets.QMessageBox.Yes:
        #         for file in self.file_names:
        #             description = file.split("_")
        #             description = description[1]
        #             project_number, _, _, _, _, email_recipient_to, email_recipient_cc, email_recipient_subject = project_info(
        #                 test=self.test, description=description)
        #             title = file.split("/").pop()
        #             attachment = file
        #             try:
        #                 outlook = win32.Dispatch('outlook.application')
        #                 mail = outlook.CreateItem(0)
        #                 mail.To = email_recipient_to
        #                 mail.CC = email_recipient_cc
        #                 mail.Subject = email_recipient_subject
        #                 if "28d" in title:
        #                     mail.HtmlBody = body_text_28
        #                 else:
        #                     mail.HtmlBody = body_text
        #                 mail.Attachments.Add(attachment)
        #                 mail.Save()
        #                 e = "Drafted email for: {0}".format(title)
        #                 self.status_output_box.appendPlainText(e)
        #             except Exception as e:
        #                 print(e)
        #                 self.status_output_box.appendPlainText(e)
        #                 pass
        # if self.analyzed:
        #     if os.path.isfile(signature_path):
        #         with open(signature_path, "r") as file:
        #             body_text = file.read()
        #         with open(signature_path_28, "r") as file:
        #             body_text_28 = file.read()
        #     else:
        #         # print("Signature File Not Found")
        #         body_text = ""
        #         pass
        #     all_list_titles = []
        #     all_list_data = []
        #     for i in range(self.processed_files_list_widget.count()):
        #         all_list_data.append(self.processed_files_list_widget.item(
        #             i).data(QtCore.Qt.UserRole).split("%%")[0])
        #         all_list_titles.append(
        #             self.processed_files_list_widget.item(i).text())
        #     for i, project_number in enumerate(self.project_numbers):
        #         if self.project_numbers_short[i][0] == "P":
        #             self.project_numbers_short[i] = self.project_numbers_short[i].replace(
        #                 "P-", "P-00")
        #         project_number, _, _, _, _, email_recipient_to, email_recipient_cc, email_recipient_subject = project_info(project_number=project_number, project_number_short=self.project_numbers_short[i],
        #                                                                                                                    test=self.test)
        #         attachment = all_list_data[i]
        #         try:
        #             outlook = win32.Dispatch('outlook.application')
        #             mail = outlook.CreateItem(0)
        #             mail.To = email_recipient_to
        #             mail.CC = email_recipient_cc
        #             mail.Subject = email_recipient_subject
        #             if "28d" in attachment:
        #                 mail.HtmlBody = body_text_28
        #             else:
        #                 mail.HtmlBody = body_text
        #             mail.Attachments.Add(attachment)
        #             mail.Save()
        #             e = "Drafted email for: {0}".format(all_list_titles[i])
        #             self.status_output_box.appendPlainText(e)
        #         except Exception as e:
        #             print(e)
        #             self.status_output_box.appendPlainText(str(e))
        #             pass

    def test_check(self):
        """Checks for 'Test Mode'.\n
        Mainly used for testing file analysis without saving to server locations or e-mailing to clients.\n
        Files will be saved to original location instead and e-mails will be blank.
        """
        if "test" in self.test_box.currentText().lower():
            self.test = True
        else:
            self.test = False

    def tab_clicked_handler(self, tab_index):

        if tab_index != self.stacked_layout.indexOf(self.processed_files_tab):
            return

        self.console_nav_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Console")
        )

        self.unseen_console_alerts = 0

    def output_to_console(self, msgs, alerts=1):
        """Outputs a message for user to see. If user is not currently viewing console tab, tab name will display number of important messages.

        Args:
            msgs (list): list of messages. Each list item will display on a new line.
            alerts (int, optional): Number of alerts to add to unseen amount. Defaults to 1.
        """

        for msg in msgs:
            self.status_output_box.appendPlainText(msg)
        self.status_output_box.appendPlainText("")

        # If user is not currently in the console tab, add number of alerts to tab title
        # If user is in the console tab, then reset the number of unseen alerts to 0 and do not update title
        if self.stacked_layout.currentIndex() != self.stacked_layout.indexOf(
            self.processed_files_tab
        ):
            self.unseen_console_alerts += alerts
            self.console_nav_button.setText(
                QtCore.QCoreApplication.translate(
                    "MainWindow", f"Console ({self.unseen_console_alerts})"
                )
            )
            return

        self.unseen_console_alerts = 0

    def open_file_dialog(self):
        """Opens a file dialog to select files for input"""

        # When clicking Select Files, clear any previously selected files, and reset the file status box
        self.file_names = None
        self.loaded_file_button.setText("Loaded Files: 0")

        self.dialog = QtWidgets.QFileDialog(
            directory=str(os.path.abspath(os.path.join(os.getcwd(), "test_files")))
        )
        self.file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            caption="Select Files to Process", filter="PDF (*.pdf)"
        )

        self.progress_bar.setValue(0)
        if not self.file_names:
            self.process_button.setEnabled(False)
            self.progress_bar.setFormat("Select Files to Begin...")
            return

        self.progress_bar.setFormat(
            "Press 'Process' Button to Start Processing Files..."
        )
        self.process_button.setText(
            QtCore.QCoreApplication.translate(
                "MainWindow", f"Process ({len(self.file_names)} Selected)"
            )
        )
        file_names_strings = []
        if len(self.file_names) == 1:
            file_names_string = (
                "New Selection of (" + str(len(self.file_names)) + ")" + " file:"
            )
        else:
            file_names_string = (
                "New Selection of (" + str(len(self.file_names)) + ")" + " files:"
            )

        file_names_strings.append(file_names_string)
        for item in self.file_names:
            file_names_strings.append(item)
        self.loaded_file_button.setText(f"Loaded Files: {len(self.file_names)}")
        self.process_button.setEnabled(True)
        self.output_to_console(file_names_strings, alerts=len(file_names_strings) - 1)

    def rename_file_handler(self):
        """Upon double clicking a list item, it can leave it open for some reason and not allow it to be clicked again, so close persistant editor upon double click."""

        if self.processed_files_list_widget.isPersistentEditorOpen(
            self.processed_files_list_widget.currentItem()
        ):
            self.processed_files_list_widget.closePersistentEditor(
                self.processed_files_list_widget.currentItem()
            )
        self.processed_files_list_widget.editItem(
            self.processed_files_list_widget.currentItem()
        )

    def file_rename_button_handler(self):
        """Renames the currently selected file from its original location, as well as in the directory specified in project_data"""

        current_item = self.processed_files_list_widget.currentItem()
        current_name = current_item.text()
        new_name = self.file_rename_line_edit.text()

        if new_name == current_name:
            return

        file_dirs = current_item.data(QtCore.Qt.UserRole)
        source_path = file_dirs["source"]
        project_data_path = file_dirs["project_data"]

        renamed_source_path = source_path.replace(current_name, new_name)
        renamed_project_data_path = project_data_path.replace(current_name, new_name)

        try:
            os.rename(source_path, renamed_source_path)
        except WindowsError as e:
            # Display a message to user once simplified
            print(e)
            pass

        try:
            os.rename(project_data_path, renamed_project_data_path)
        except WindowsError as e:
            print(e)
            pass

        self.processed_files_list_widget.currentItem().setText(
            self.file_rename_line_edit.text()
        )
        file_dirs = {
            "source": renamed_source_path,
            "project_data": renamed_project_data_path,
        }
        self.processed_files_list_widget.currentItem().setData(
            QtCore.Qt.UserRole, file_dirs
        )

    def evt_analyze_complete(self, results):
        """Appends processed files list widget with new processed file data

        Args:
            results (list): processed file list
        """
        if results[0]:  # Template analysis result

            self.apply_unique_file_identifier_button.setEnabled(True)

            if results[-1] is None:  # No file type detected therefore new template
                self.apply_unique_profile_project_number_button.setEnabled(False)
                self.apply_unique_profile_parameter_button.setEnabled(False)
                self.update_template_pixmap()
                return

            self.apply_unique_profile_project_number_button.setEnabled(True)
            self.apply_unique_profile_parameter_button.setEnabled(True)
            profile_name = results[1]
            profile_type = results[2]
            self.current_file_profile = profile_type
            self.file_template_profile_name_label.setText(profile_name)
            self.update_template_pixmap()
            self.paint_existing_data_rects()

        else:  # normal analysis result
            print_string = results[1]
            file_name = results[2]
            file_path = results[3]
            project_data_dir = results[5]
            file_dirs = {"source": file_path, "project_data": project_data_dir}
            self.output_to_console([print_string])
            self.processed_files_list_item = QtWidgets.QListWidgetItem(file_name)
            self.processed_files_list_item.setData(QtCore.Qt.UserRole, file_dirs)
            self.processed_files_list_widget.addItem(self.processed_files_list_item)
        self.processed_files += 1
        self.processed_file_button.setText(f"Processed Files: {self.processed_files}")
        self.process_button.setEnabled(False)

    def evt_export_complete(self, results):
        """Displays error message to user if one is present in results otherwise does nothing.

        Args:
            results (list): return message
        """

        self.process_button.setEnabled(True)
        self.process_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Process Files")
        )
        self.import_project_data_button.setEnabled(True)
        self.import_project_data_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Import Project Data")
        )
        if results and results[0] is not None:
            export_error_dialog = QtWidgets.QMessageBox()
            export_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
            export_error_dialog.setWindowTitle("Project Data Export Error")
            export_error_dialog.setText(
                f"Error when trying to export values from database.\n\n \
                {results[0]}"
            )
            export_error_dialog.exec()
        else:
            self.progress_popup.setValue(100)

    def evt_delete_all_complete(self, results):
        """Displays error message to user if one is present in results otherwise does nothing.

        Args:
            results (list): return message
        """

        self.process_button.setEnabled(True)
        self.import_project_data_button.setEnabled(True)
        if results and results[0] is not None:
            export_error_dialog = QtWidgets.QMessageBox()
            export_error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
            export_error_dialog.setWindowTitle("Project Data Delete Error")
            export_error_dialog.setText(
                f"Error when trying to delete all values from database.\n\n \
                {results[0]}"
            )
            export_error_dialog.exec()
        else:
            self.progress_popup.setValue(100)
            self.database_fetch("project_data")
            self.database_discard_edited_project_data()
            self.clear_project_data_entry_fields()

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
            QtCore.QCoreApplication.translate("MainWindow", "Export Project Data")
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

    def evt_analyze_progress(self, val):
        """Updates main progress bar based off of emitted progress values.

        Args:
            val (int): Current progress level of file being analyzed
        """

        # Since val is progress of each individual file, need to ensure whole progress accounts for all files
        self.progress += val
        self.progress_bar.setValue(int(self.progress / len(self.file_names)))
        if self.progress == 100:
            self.progress_bar.setFormat("Processing Complete.")

    def analyze_button_handler(self):
        """Handles the initialization for processing selected files."""

        if self.file_names is not None:
            self.process_button.setEnabled(False)
            self.test_check()
            self.analyzed = False
            self.progress = 0
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Processing... %p%")
            self.output_to_console(["Analysis Started..."])
            self.data_processing()
            self.analyzed = True
        else:
            self.output_to_console(["Please select at least 1 file to analyze..."])
        self.process_button.setEnabled(True)

    def list_widget_handler(self):
        """Displays the currently selected list widget item"""

        file_dirs = self.processed_files_list_widget.currentItem().data(
            QtCore.Qt.UserRole
        )
        source_dir = file_dirs["source"].replace("\\", "/")
        if not os.path.exists(source_dir):
            self.processed_files_list_widget.takeItem(
                self.processed_files_list_widget.currentRow()
            )
            self.processed_files_list_widget.setCurrentRow(0)
            set_text = self.processed_files_list_widget.currentItem().text()
            self.file_rename_line_edit.setText(set_text)
            return
        self.file_preview.load(QtCore.QUrl(f"file:{source_dir}"))
        self.file_preview.show()
        set_text = self.processed_files_list_widget.currentItem().text()
        self.file_rename_line_edit.setText(set_text)

    def data_processing(self):
        """Processes the selected files"""
        self.progress_bar.setFormat("Processing... %p%")
        # For each file create a new thread to increase performance
        for file_name in self.file_names:
            self.analyze_worker = WorkerAnalyzeThread(
                file_name=file_name, test=self.test, analyzed=self.analyzed
            )
            self.analyze_worker.signals.progress.connect(self.evt_analyze_progress)
            self.analyze_worker.signals.result.connect(self.evt_analyze_complete)
            self.thread_pool.start(self.analyze_worker)
            self.evt_analyze_progress(10)
        self.process_button.setText(
            QtCore.QCoreApplication.translate("MainWindow", "Process")
        )


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    # # Open the qss styles file and read in the css-alike styling code
    with open("style/styles.qss", "r") as f:
        style = f.read()

    # Set the stylesheet of the application
    app.setStyleSheet(style)
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(QtCore.Qt.white))
    app.setPalette(palette)
    QtGui.QFontDatabase.addApplicationFont("assests/Roboto-Regular.ttf")
    window = MainWindow()
    window.setWindowTitle("PDF Processor")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#6a6a6a"))
    window.setPalette(palette)
    app.exec()
