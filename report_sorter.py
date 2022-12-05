import os
from re import A
import shutil
import ctypes
import time
import io

import regex as re
import win32com.client as win32
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from PyQt5.QtGui import QImage, QPainter
from pdf2image import convert_from_path
from collections import namedtuple

from functions.analysis import WorkerAnalyzeThread, detect_package_number
from functions.data_handler import *
from functions.project_info import project_info
from widgets.file_template_creation import TemplateWidget
from widgets.apply_data_type_dialog import ApplyFoundData

# set current working directory to variable to save files to
home_dir = os.getcwd()

# hard coded poppler path from current working directory
poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


def output(self):
    self.outputBox.appendPlainText("Analyzing...\n")

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        # self.showFullScreen()
        self.start_position = None
        self.rect = QtCore.QRect()
        self.drawing = False

        initialize_database()
        self.file_profiles_data = fetch_file_profiles()
        self.profile_names = [s[0] for s in self.file_profiles_data]
        self.profile_find_text = [s[1] for s in self.file_profiles_data]
        self.setObjectName("MainWindow")
        self.resize(850, 850)
        self.test = False
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
        self.project_numbers_short = []
        # Displays how many threads can be utilized
        self.thread_pool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" %
              self.thread_pool.maxThreadCount())
        QtCore.QMetaObject.connectSlotsByName(self)

        # Used to place Tab Widget, Central Widget, and Creator Label
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setObjectName("centralwidget")
        self.central_layout = QtWidgets.QGridLayout(self.central_widget)

        self.setCentralWidget(self.central_widget)
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setObjectName("status bar")
        self.statusBar().setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)

        # -# Start of Tab Initialization #-#

        # Stores different tabs
        self.tab_widget = QtWidgets.QTabWidget(self.central_widget)
        self.tab_widget.setObjectName("tabWidget")
        self.tab_widget.setCurrentIndex(0)
        self.tab_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.central_layout.addWidget(self.tab_widget, 0, 0, 1, 1)

        # Creator Label
        self.label = QtWidgets.QLabel(self.central_widget)
        self.label.setObjectName("creatorLabel")
        self.central_layout.addWidget(self.label, 1, 0, 1, 3)

        # Input Tab (file_input_tab_layout)
        self.file_input_tab = QtWidgets.QWidget()
        self.file_input_tab.setObjectName("tab")
        self.tab_widget.addTab(self.file_input_tab, "")

        # Layout for file_input_tab_layout
        self.file_input_tab_layout = QtWidgets.QGridLayout(self.file_input_tab)
        self.file_input_tab_layout.setObjectName("grid_layout")

        # Line above action buttons
        self.input_tab_line_1 = QtWidgets.QFrame(self.file_input_tab)
        self.input_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.input_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.input_tab_line_1.setObjectName("line")
        self.file_input_tab_layout.addWidget(self.input_tab_line_1, 2, 0, 1, 8)

        # Action buttons on Input tab
        self.select_files = QtWidgets.QPushButton(self.file_input_tab)
        self.select_files.clicked.connect(self.open_file_dialog)
        self.select_files.setObjectName("Select_files")
        self.dialog = QtWidgets.QFileDialog()  # Used for file dialog popup
        self.file_input_tab_layout.addWidget(self.select_files, 3, 0, 1, 2)

        # Action button to start file analysis
        self.analyze_button = QtWidgets.QPushButton(self.file_input_tab)
        self.analyze_button.clicked.connect(self.analyze_button_handler)
        self.analyze_button.setObjectName("analyze_button")
        self.file_input_tab_layout.addWidget(self.analyze_button, 3, 2, 1, 2)

        # Action button to start email process
        self.email_button = QtWidgets.QPushButton(self.file_input_tab)
        self.email_button.clicked.connect(self.email_button_handler)
        self.email_button.setObjectName("email_button")
        self.file_input_tab_layout.addWidget(self.email_button, 3, 4, 1, 2)

        # Drop list box to choose analysis type (Live/Test)
        # Live uses real client info, test uses dummy/local info
        self.test_box = QtWidgets.QComboBox(self.file_input_tab)
        self.test_box.setObjectName("test_box")
        self.file_input_tab_layout.addWidget(self.test_box, 3, 6, 1, 1)
        self.test_box.setEditable(True)
        self.test_box.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.test_box.addItems(["Test", "Live"])
        self.test_box.setEditable(False)

        # Line below action buttons
        self.input_tab_line_2 = QtWidgets.QFrame(self.file_input_tab)
        self.input_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.input_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.input_tab_line_2.setObjectName("input_tab_line_2")
        self.file_input_tab_layout.addWidget(self.input_tab_line_2, 4, 0, 1, 8)

        # Output box to display info to user
        self.status_output_box = QtWidgets.QPlainTextEdit(self.file_input_tab)
        self.status_output_box.setObjectName("status_output_box")
        self.status_output_box.setReadOnly(True)
        self.file_input_tab_layout.addWidget(self.status_output_box, 5, 0, 1, 8)

        # Progress bar to show analyze progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setStyle(QtWidgets.QStyleFactory.create("GTK"))
        self.progress_bar.setTextVisible(False)
        self.file_input_tab_layout.addWidget(self.progress_bar, 6, 0, 1, 8)

        # Output Tab (processed_files_tab)
        self.processed_files_tab = QtWidgets.QWidget()
        self.processed_files_tab.setObjectName("tab_2")
        self.tab_widget.addTab(self.processed_files_tab, "")

        # Layout for processed_files_tab
        self.processed_files_tab_layout = QtWidgets.QGridLayout(self.processed_files_tab)
        self.processed_files_tab_layout.setObjectName("processed_files_tab_layout")

        # Label for list widget below
        self.processed_files_label = QtWidgets.QLabel(self.processed_files_tab)
        self.processed_files_label.setGeometry(QtCore.QRect(10, 10, 81, 16))
        self.processed_files_label.setObjectName("processed_files_label")
        self.processed_files_tab_layout.addWidget(self.processed_files_label, 0, 0, 1, 2)

        # Widget to hold analyzed files
        self.processed_files_list_widget = QtWidgets.QListWidget(self.processed_files_tab)
        self.processed_files_list_widget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        self.processed_files_list_widget.setObjectName("processed_files_list_widget")
        self.processed_files_tab_layout.addWidget(self.processed_files_list_widget, 1, 0, 5, 5)

        # Lines within the analyzed files widget above
        self.processed_files_list_item = QtWidgets.QListWidgetItem()
        self.processed_files_list_widget.itemClicked.connect(self.list_widget_handler)
        self.processed_files_list_widget.itemDoubleClicked.connect(self.rename_file_handler)

        # Text editor line to edit file names
        self.file_rename_line_edit = QtWidgets.QLineEdit(self.processed_files_tab)
        self.file_rename_line_edit.setObjectName("file_rename_line_edit")
        self.processed_files_tab_layout.addWidget(self.file_rename_line_edit, 6, 0, 1, 4)

        # Action button to call rename function
        self.file_rename_button = QtWidgets.QPushButton(self.processed_files_tab)
        self.file_rename_button.clicked.connect(self.file_rename_button_handler)
        self.file_rename_button.setObjectName("file_rename_button")
        self.processed_files_tab_layout.addWidget(self.file_rename_button, 6, 4, 1, 1)

        # Title for JPG/PDF preview below
        self.file_preview_label = QtWidgets.QLabel(self.processed_files_tab)
        self.file_preview_label.setGeometry(QtCore.QRect(10, 140, 100, 16))
        self.file_preview_label.setObjectName("file_preview_label")
        self.processed_files_tab_layout.addWidget(self.file_preview_label, 7, 0, 1, 2)

        # Displays JPG of entire PDF
        # self.graphicsView = QtWidgets.QGraphicsView(self.tab_2)
        # self.graphicsView.setGeometry(QtCore.QRect(10, 160, 320, 400))
        # self.graphicsView.setObjectName("graphicsView")
        # self.gridLayout_2.addWidget(self.graphicsView, 8, 0, 20, 5)
        # self.graphicsView.setViewportUpdateMode(
        #     QtWidgets.QGraphicsView.FullViewportUpdate)

        # Displays PDF
        self.file_preview = QtWebEngineWidgets.QWebEngineView()
        _qtweb_settings = QtWebEngineWidgets.QWebEngineSettings
        self.file_preview.settings().setAttribute(_qtweb_settings.PluginsEnabled, True)
        self.file_preview.settings().setAttribute(_qtweb_settings.PdfViewerEnabled, True)
        self.processed_files_tab_layout.addWidget(self.file_preview, 8, 0, 20, 5)

        # Database Tab (database_viewer_tab)
        self.database_viewer_tab = QtWidgets.QWidget()
        self.database_viewer_tab.setObjectName("database_viewer_tab")
        self.tab_widget.addTab(self.database_viewer_tab, "")

        # Layout for database_viewer_tab
        self.database_viewer_tab_layout = QtWidgets.QGridLayout(self.database_viewer_tab)
        self.database_viewer_tab_layout.setObjectName("database_viewer_tab_layout")

        # Table widget to display DB results
        self.database_viewer_table = QtWidgets.QTableWidget()
        self.database_viewer_tab_layout.addWidget(self.database_viewer_table, 1, 0, 5, 4)

        self.database_tables_combo_box = QtWidgets.QComboBox(self.database_viewer_tab)
        self.database_tables_combo_box.setObjectName("database_tables_combo_box")
        self.database_viewer_tab_layout.addWidget(self.database_tables_combo_box, 6, 0, 1, 1)
        self.database_tables_combo_box.setEditable(True)
        self.database_tables_combo_box.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.database_tables_combo_box.addItems(fetch_table_names())
        self.database_tables_combo_box.setEditable(False)

        self.database_results = QtWidgets.QPushButton(self.database_viewer_tab)
        self.database_results.setObjectName("database_results")
        self.database_results.clicked.connect(self.database_fetch)
        self.database_viewer_tab_layout.addWidget(self.database_results, 6, 1, 1, 3)

        # Profile/Data Section Tab (file_template_tab)
        self.file_template_tab = QtWidgets.QWidget()
        self.file_template_tab.setObjectName("file_template_tab")
        self.tab_widget.addTab(self.file_template_tab, "")

        # Layout for file_template_tab
        self.file_template_tab_layout = QtWidgets.QGridLayout(self.file_template_tab)
        self.file_template_tab_layout.setObjectName("file_template_tab_layout")

        # Line above action buttons
        self.file_template_tab_line_1 = QtWidgets.QFrame(self.file_input_tab)
        self.file_template_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.file_template_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.file_template_tab_line_1.setObjectName("file_template_tab_line_1")
        self.file_template_tab_layout.addWidget(self.file_template_tab_line_1, 0, 0, 1, 10)

        # Button to load template file
        self.select_template_file = QtWidgets.QPushButton()
        self.select_template_file.setObjectName("select_template_file")
        self.select_template_file.clicked.connect(self.file_profile_template_dialog)
        self.select_template_file_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_layout.addWidget(self.select_template_file, 1, 0, 1, 2)

        # Button to apply selection as co-ords for unique file identifier
        self.apply_unique_file_identifier_button = QtWidgets.QPushButton()
        self.apply_unique_file_identifier_button.setObjectName(
            "apply_unique_file_identifier_button")
        self.apply_unique_file_identifier_button.clicked.connect(
            self.apply_unique_file_indentifier)
        self.apply_unique_file_identifier_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_layout.addWidget(self.apply_unique_file_identifier_button, 1, 2, 1, 2)

        # Button to apply selection as co-ords for unique data information
        self.apply_unique_profile_paramater_button = QtWidgets.QPushButton()
        self.apply_unique_profile_paramater_button.setObjectName(
            "apply_unique_profile_paramater_button")
        self.apply_unique_profile_paramater_button.clicked.connect(
            self.apply_unique_profile_paramater)
        self.apply_unique_profile_paramater_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_layout.addWidget(
            self.apply_unique_profile_paramater_button, 1, 8, 1, 2)

        # Line below action buttons
        self.file_template_tab_line_2 = QtWidgets.QFrame(self.file_input_tab)
        self.file_template_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.file_template_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.file_template_tab_line_2.setObjectName("file_template_tab_line_2")
        self.file_template_tab_layout.addWidget(self.file_template_tab_line_2, 2, 0, 1, 10)

        # Custom template display widget
        self.template_display = QtWidgets.QLabel()
        self.file_template_tab_layout.addWidget(self.template_display, 3, 0, 20, 10)

        # Settings Tab (settings_tab)
        self.settings_tab = QtWidgets.QWidget()
        self.settings_tab.setObjectName("settings_tab")
        self.tab_widget.addTab(self.settings_tab, "")

        # Layout for settings_tab
        self.setting_tab_layout = QtWidgets.QGridLayout(self.settings_tab)
        self.setting_tab_layout.setObjectName("setting_tab_layout")

        # Line above action buttons
        self.settings_tab_line_1 = QtWidgets.QFrame(self.settings_tab)
        self.settings_tab_line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.settings_tab_line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.settings_tab_line_1.setObjectName("settings_tab_line_1")
        self.setting_tab_layout.addWidget(self.settings_tab_line_1, 0, 0, 1, 10)

        # Label to choose file profile
        self.settings_file_profile_names_label = QtWidgets.QLabel()
        self.settings_file_profile_names_label.setObjectName(
            "settings_file_profile_names_label")
        self.setting_tab_layout.addWidget(
            self.settings_file_profile_names_label, 1, 0, 1, 1)

        # dropdown of all profiles
        self.settings_file_profile_names_combo_box = QtWidgets.QComboBox(
            self.settings_tab)
        self.settings_file_profile_names_combo_box.setObjectName(
            "settings_file_profile_names_combo_box")
        self.setting_tab_layout.addWidget(
            self.settings_file_profile_names_combo_box, 1, 2, 1, 4)
        self.settings_file_profile_names_combo_box.setEditable(True)
        self.settings_file_profile_names_combo_box.lineEdit(
        ).setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.settings_file_profile_names_combo_box.addItems(
            self.format_file_profile_dropdown())
        self.settings_file_profile_names_combo_box.setEditable(False)
        self.settings_file_profile_names_combo_box.currentTextChanged.connect(
            self.display_active_paramaters)

        # Label to display active parameters
        self.settings_profile_paramaters_label = QtWidgets.QLabel()
        self.settings_profile_paramaters_label.setObjectName("settings_profile_paramaters_label")
        self.setting_tab_layout.addWidget(self.settings_profile_paramaters_label, 2, 0, 1, 4)

        # List widget to display active parameters
        self.settings_profile_paramaters_list_widget = QtWidgets.QListWidget(self.settings_tab)
        self.settings_profile_paramaters_list_widget.setObjectName(
            "settings_profile_paramaters_list_widget")
        self.settings_profile_paramaters_list_widget.itemClicked.connect(
            self.add_active_param_line_edit)
        self.setting_tab_layout.addWidget(
            self.settings_profile_paramaters_list_widget, 3, 0, 2, 10)

        # Line below action buttons
        self.settings_tab_line_2 = QtWidgets.QFrame(self.settings_tab)
        self.settings_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.settings_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.settings_tab_line_2.setObjectName("settings_tab_line_2")
        self.setting_tab_layout.addWidget(self.settings_tab_line_2, 14, 0, 1, 10)

        # Label for file rename paramater input
        self.settings_profile_naming_scheme_label = QtWidgets.QLabel()
        self.settings_profile_naming_scheme_label.setObjectName("settings_profile_naming_scheme_label")
        self.setting_tab_layout.addWidget(self.settings_profile_naming_scheme_label, 15, 0, 1, 4)

        # Line edit for user to type in format with parameters
        self.settings_profile_naming_scheme_line_edit = QtWidgets.QLineEdit(self.settings_tab)
        self.settings_profile_naming_scheme_line_edit.setObjectName(
            "settings_profile_naming_scheme_line_edit")
        self.settings_profile_naming_scheme_line_edit.textChanged.connect(
            self.display_example_file_name)
        self.setting_tab_layout.addWidget(
            self.settings_profile_naming_scheme_line_edit, 16, 0, 1, 8)

        # Button to apply selection as co-ords for unique data information
        self.settings_profile_naming_scheme_button = QtWidgets.QPushButton()
        self.settings_profile_naming_scheme_button.setObjectName(
            "settings_profile_naming_scheme_button")
        self.settings_profile_naming_scheme_button.clicked.connect(
            self.apply_file_name_pattern)
        self.setting_tab_layout.addWidget(
            self.settings_profile_naming_scheme_button, 16, 8, 1, 2)

        # Label for file rename example output
        self.settings_profile_naming_scheme_example_label = QtWidgets.QLabel()
        self.settings_profile_naming_scheme_example_label.setObjectName("settings_profile_naming_scheme_example_label")
        self.setting_tab_layout.addWidget(self.settings_profile_naming_scheme_example_label, 17, 0, 1, 4)

        # Line edit to display an example of data shown
        self.settings_profile_naming_scheme_example_line_edit = QtWidgets.QLineEdit(self.settings_tab)
        self.settings_profile_naming_scheme_example_line_edit.setEnabled(False)
        self.settings_profile_naming_scheme_example_line_edit.setObjectName(
            "settings_profile_naming_scheme_example_line_edit")
        self.setting_tab_layout.addWidget(
            self.settings_profile_naming_scheme_example_line_edit, 18, 0, 1, 10)

        # Label for empty space
        self.settings_empty_label = QtWidgets.QLabel()
        self.settings_empty_label.setObjectName("tab_5_empty_space_label")
        self.setting_tab_layout.addWidget(self.settings_empty_label, 19, 0, 10, 10)

        # Translate UI if in another language
        self.translate_ui()

        # Set tab order (Can probably include more in future)
        self.setTabOrder(self.select_files, self.analyze_button)
        self.setTabOrder(self.analyze_button, self.status_output_box)
        self.setTabOrder(self.status_output_box, self.file_input_tab)
        self.setTabOrder(self.file_input_tab, self.processed_files_tab)
        self.setTabOrder(self.processed_files_tab, self.database_viewer_tab)
        self.setTabOrder(self.database_viewer_tab, self.file_template_tab)

        # Once finished initializing, show
        self.show()

    progress_update = QtCore.pyqtSignal(int)

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate

        self.setWindowTitle(_translate("MainWindow", "Report Sorter"))
        self.database_results.setText(_translate(
            "MainWindow", "Fetch Table Results"))
        self.settings_profile_naming_scheme_label.setText(_translate("MainWindow", "Filename Template Creation:"))
        self.settings_profile_naming_scheme_example_label.setText(_translate("MainWindow", "Filename Example:"))
        self.label.setText(_translate(
            "MainWindow", "Created By Brandon Gorman"))
        self.file_preview_label.setText(_translate("MainWindow", "File Output Viewer:"))
        self.processed_files_label.setText(_translate("MainWindow", "Processed Files:"))
        self.settings_file_profile_names_label.setText(
            _translate("MainWindow", "Choose File Profile:"))
        self.settings_profile_paramaters_label.setText(_translate(
            "MainWindow", "Available Parameters For Chosen File Profile:"))

        self.select_files.setText(_translate("MainWindow", "Select Files"))
        self.file_rename_button.setWhatsThis(_translate(
            "MainWindow", "Rename the currently selected file"))
        self.select_template_file.setText(
            _translate("MainWindow", "New File Profile"))
        self.apply_unique_file_identifier_button.setText(_translate(
            "MainWindow", "Set Unique Profile Identifier"))
        self.apply_unique_profile_paramater_button.setText(_translate(
            "MainWindow", "Add Data Parameter"))
        self.file_rename_button.setText(_translate("MainWindow", "Rename"))
        self.analyze_button.setText(_translate("MainWindow", "Analyze"))
        self.email_button.setText(_translate("MainWindow", "E-Mail"))
        self.settings_profile_naming_scheme_button.setText(_translate("MainWindow", "Save Filename Pattern"))

        self.tab_widget.setTabText(self.tab_widget.indexOf(
            self.file_input_tab), _translate("MainWindow", "Input"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(
            self.processed_files_tab), _translate("MainWindow", "Output"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(
            self.database_viewer_tab), _translate("MainWindow", "Database"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(
            self.file_template_tab), _translate("MainWindow", "Template Input"))
        self.tab_widget.setTabText(self.tab_widget.indexOf(
            self.settings_tab), _translate("MainWindow", "Settings"))

    def database_fetch(self):
        """Handles threading database fetching and passing results to display to user"""
        
        # Database may get large so start seperate thread to handle fetching
        self.database_worker = fetch_data(self.database_tables_combo_box.currentText())

        # Once data returns display the data
        self.database_worker.signals.result.connect(
            self.display_data_as_table)
        self.thread_pool.start(self.database_worker)

    def display_data_as_table(self, data):
        """Displays the fetched data into a table format for users to see

        Args:
            data (list): database/table data in format [[data], [headers]]
        """
        
        self.database_viewer_table.setRowCount(0)
        table_widget_item = QtWidgets.QTableWidgetItem
        # try to assign data to variables
        try:
            [data, headers] = [data[0], data[1]]
            _ = len(data)
        except IndexError:
            self.database_viewer_table.setColumnCount(1)
            self.database_viewer_table.setItem(0, 0, table_widget_item("No Data"))
            return

        self.database_viewer_table.setColumnCount(len(headers))
        self.database_viewer_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        # Add headers to table
        for col, header_text in enumerate(headers):
            self.database_viewer_table.setHorizontalHeaderItem(
                col, table_widget_item(header_text))
        # Add data to table
        for row, row_data in enumerate(data):
            self.database_viewer_table.insertRow(row)
            for column, item in enumerate(row_data):
                self.database_viewer_table.setItem(row, column, table_widget_item(str(item)))

    def format_file_profile_dropdown(self):
        """Transforms profiles into a list with profile name and identifier text. profiles list comes from fetch_file_profiles from data_handler.

        Returns:
            list: Items to display in profiles dropdown
        """
        dropdown_items = ["".join([s[0], " - ", s[1]]) for s in fetch_file_profiles()]
        return dropdown_items

    def display_active_paramaters(self, file_profile_text):
        """Fills in active paramaters list based off the currently chosen file_profile dropdown item.

        Args:
            file_profile_text (str): file_profile text as format "file_profile - example text"
        """
        self.settings_profile_paramaters_list_widget.clear()
        if not file_profile_text.split(" - ")[-1]:
            return
        self.active_params_data = fetch_active_params(file_profile_text.split(" - ")[0])
        for [param_id, param_name, example] in self.active_params_data:
            self.active_param_list_item = QtWidgets.QListWidgetItem(param_name)
            self.active_param_list_item.setData(QtCore.Qt.UserRole, param_id)
            self.settings_profile_paramaters_list_widget.addItem(
                self.active_param_list_item)

    def apply_file_name_pattern(self):
        """Handles the saving of a file profile's file naming pattern to the database"""

        connection, cursor = db_connect(db_file_path)
        try:
            file_profile_filename_pattern = cursor.execute(
                """SELECT file_naming_format FROM profiles WHERE profile_identifier_text = ?""", (scrub(self.settings_file_profile_names_combo_box.currentText()),)).fetchone()[0]
            print(file_profile_filename_pattern)

            # If file_profile already has a naming pattern, ask if user wants ot overwrite
            if file_profile_filename_pattern:
                overwrite = QtWidgets.QMessageBox()
                overwrite.setIcon(QtWidgets.QMessageBox.Warning)
                overwrite.setWindowTitle("Filename Pattern Already Found")
                overwrite.setText(
                    f"Unique identifier already in database \
                        \n \
                        \n{file_profile_filename_pattern} \
                        \n ")
                overwrite.addButton("Overwrite", QtWidgets.QMessageBox.YesRole)
                overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                overwrite_reply = overwrite.exec_()
                if overwrite_reply == 0:
                    update_file_profile_file_name_pattern(self.settings_file_profile_names_combo_box.currentText(), self.settings_profile_naming_scheme_line_edit.text(), connection, cursor)
            else:
                update_file_profile_file_name_pattern(self.settings_file_profile_names_combo_box.currentText(), self.settings_profile_naming_scheme_line_edit.text(), connection, cursor)
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
            if ((rec2.x2 >= rec1.x1 and rec2.x2 <= rec1.x2) or (rec2.x1 >= rec1.x1 and rec2.x1 <= rec1.x2) or \
                ((rec1.x2 >= rec2.x1 and rec1.x2 <= rec2.x2) or (rec1.x1 >= rec2.x1 and rec1.x1 <= rec2.x2))):
                x_match = True
            else:
                x_match = False
            if ((rec2.y2 >= rec1.y1 and rec2.y2 <= rec1.y2) or (rec2.y1 >= rec1.y1 and rec2.y1 <= rec1.y2)) or \
                ((rec1.y2 >= rec2.y1 and rec1.y2 <= rec2.y2) or (rec1.y1 >= rec2.y1 and rec1.y1 <= rec2.y2)):
                y_match = True
            else:
                y_match = False
            if x_match and y_match:
                return True
            else:
                return False
        
        def enclosed():
            if (rec2.x1 >= rec1.x1 and rec2.x2 <= rec1.x2) or \
                (rec1.x1 >= rec2.x1 and rec1.x2 <= rec2.x2):
                x_match = True
            else:
                x_match = False
            if (rec2.y1 >= rec1.y1 and rec2.y2 <= rec1.y2) or \
                (rec1.y1 >= rec2.y1 and rec1.y2 <= rec2.y2):
                y_match = True
            else:
                y_match = False
            if x_match and y_match:
                return True
            else:
                return False

        return intersects() or enclosed()

    def display_example_file_name(self):
        """When file name line edit is changed, replace any instance of '{paramater}' with an example string form that paramater and replace the example line edit with that text."""        
        replace_result = self.settings_profile_naming_scheme_line_edit.text()
        for [param_id, param_name, example] in self.active_params_data:
            replace_result = replace_result.replace("".join(["{", param_name, "}"]), example)
        self.settings_profile_naming_scheme_example_line_edit.setText(replace_result)

    def add_active_param_line_edit(self):
        """Upon clicking a parameter in the paramater list, {paramater}' gets appended to the line edit"""

        active_param_name = self.settings_profile_paramaters_list_widget.currentItem().text()
        # active_param_id = str(self.active_parameters_list_widget.currentItem().data(
        #     QtCore.Qt.UserRole))

        current_text = self.settings_profile_naming_scheme_line_edit.text()
        self.settings_profile_naming_scheme_line_edit.setText(
            current_text + "{" + active_param_name + "}")
        self.settings_profile_naming_scheme_line_edit.setFocus()

    def apply_unique_file_indentifier(self):
        """Handles creating a new file_profile based off of the bounding box for identifiable text"""

        # If a pdf file isnt opened, then warn user and return      
        if not self.profile_file_loaded:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("No Profile Loaded")
            no_file_profile.setText(
                "You must first select a template file to open.")
            no_file_profile.exec_()
            return

        # Bounding box can be too small and cause issues when analyzing text
        # If width and height less than 5 pixels, warn user and return
        if self.template_display.image_area_too_small:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("Area Too Small")
            no_file_profile.setText(
                "Data area too small. Please choose a larger area.")
            no_file_profile.exec_()
            return
        
       

        requirements_met = False
        cancelled = False
        # Make sure the file_profile_field is not left blank
        # Display an error if left blank and bring the button box back up to retry.
        # If cancelled or requirements met, exit loop
        while not requirements_met and not cancelled:
            self.apply_unique_file_identifier_dialog = ApplyFoundData(
            self.template_display.true_coords(), self.template_display.found_text)
            if self.apply_unique_file_identifier_dialog.exec():
                if self.apply_unique_file_identifier_dialog.description.text().strip().replace(" ", "_") == "":
                    no_file_profile = QtWidgets.QMessageBox()
                    no_file_profile.setIcon(QtWidgets.QMessageBox.Critical)
                    no_file_profile.setWindowTitle("No Profile Name")
                    no_file_profile.setText(
                        "Please enter a profile name.")
                    no_file_profile.exec_()
                else:
                    requirements_met = True
            else:
                cancelled = True


        if not cancelled:
            
            unique_file_type_identifier = self.apply_unique_file_identifier_dialog.text_input.text()
            file_profile_name = self.apply_unique_file_identifier_dialog.description.text().strip().replace(" ", "_")
            [x_1, x_2, y_1, y_2] = self.template_display.true_coords()

            # check if identiying text can be found in any of the existing profiles
            connection, cursor = db_connect(db_file_path)
            indentifier_text_found = False
            try:
                unique_texts_query = """SELECT profile_id, profile_identifier_text, unique_profile_name FROM profiles"""
                unique_texts = cursor.execute(unique_texts_query).fetchall()
                for profile_id, unique_text, profile_name in unique_texts:
                    if unique_file_type_identifier.strip().lower() in unique_text.strip().lower() or unique_text.strip().lower() in unique_file_type_identifier.strip().lower():
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
                    prof_txt_loc_query = """SELECT x_1, x_2, y_1, y_2 FROM profiles WHERE profile_id=?"""
                    [db_x_1, db_x_2, db_y_1, db_y_2] = cursor.execute(prof_txt_loc_query, (profile_id,)).fetchone()

                    RECTANGLE = namedtuple('RECTANGLE', 'x1 x2 y1 y2')
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
                        \nSelect Cancel to choose another unique identifier")
                profile_issue.addButton("Continue", QtWidgets.QMessageBox.YesRole)
                profile_issue.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                profile_issue_reply = profile_issue.exec_()
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
                    """SELECT profile_id FROM profiles WHERE unique_profile_name=?""", (file_profile_name,)).fetchone()[0]
                self.current_file_profile = file_profile_id
            except Exception as e:
                print(f"Error inserting data: {e}")
                overwrite = QtWidgets.QMessageBox()
                overwrite.setIcon(QtWidgets.QMessageBox.Warning)
                overwrite.setWindowTitle("File Profile Name Not Unique")
                overwrite.setText(
                    "Profile name already in database \
                        \n\nSelect Overwrite to overwrite existing file profile and its data \
                        \nSelect Show Existing to see and/or add data for the existing file profile \
                        \nSelect Cancel to choose another unique identifier")
                overwrite.addButton("Overwrite", QtWidgets.QMessageBox.YesRole)
                overwrite.addButton(
                    "See Existing", QtWidgets.QMessageBox.NoRole)
                overwrite.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
                overwrite_reply = overwrite.exec_()
                if overwrite_reply == 0:
                    try:
                        file_profile_id = cursor.execute(
                            """SELECT profile_id FROM profiles WHERE unique_profile_name=?""", (file_profile_name,)).fetchone()[0]
                        cursor.execute(
                            """DELETE FROM profiles WHERE profile_id=?""", (file_profile_id,))
                        print("Deleted Entry from profiles")
                        cursor.execute(add_data, data)
                        connection.commit()
                        print("Created New profiles Entry")
                        file_profile_id = cursor.execute(
                            """SELECT profile_id FROM profiles WHERE unique_profile_name=?""", (file_profile_name,)).fetchone()[0]
                        self.current_file_profile = file_profile_id

                    except Exception as e:
                        print(f"Error overwriting existing entry. {e}")
                        overwrite_error = QtWidgets.QMessageBox()
                        overwrite_error.setIcon(QtWidgets.QMessageBox.Critical)
                        overwrite_error.setWindowTitle("Overwrite Error")
                        overwrite_error.setText(
                            "Error overwriting existing entry. Please try again or submit an issue if problem persists.")
                        overwrite_error.exec_()
                elif overwrite_reply == 1:
                    file_profile_id = cursor.execute(
                        """SELECT profile_id FROM profiles WHERE unique_profile_name=?""", (file_profile_name,)).fetchone()[0]
                    self.current_file_profile = file_profile_id
                    try:
                        self.paint_existing_data_rects()
                    except Exception as e:
                        print(e)
                        pass
            finally:
                db_disconnect(connection, cursor)
                self.settings_file_profile_names_combo_box.setEditable(True)
                self.settings_file_profile_names_combo_box.clear()
                self.settings_file_profile_names_combo_box.lineEdit(
                ).setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.settings_file_profile_names_combo_box.addItems(
                     self.format_file_profile_dropdown())
                self.settings_file_profile_names_combo_box.setEditable(False)
        else:
            print("cancelled")

    def apply_unique_profile_paramater(self):
        """Handles the inserting of a new profile parameter into the database."""

        # If a profile isn't loaded yet, warn user and return
        if self.current_file_profile == 0:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Critical)
            no_file_profile.setWindowTitle("No Profile Loaded")
            no_file_profile.setText(
                "Please create a new file profile in order to add data locations.")
            no_file_profile.exec_()
            return

        # If bounding box area too small, warn user and return
        if self.template_display.image_area_too_small:
            no_file_profile = QtWidgets.QMessageBox()
            no_file_profile.setIcon(QtWidgets.QMessageBox.Information)
            no_file_profile.setWindowTitle("Area Too Small")
            no_file_profile.setText(
                "Data area too small. Please choose a larger area.")
            no_file_profile.exec_()
            return

        # Show user found text and let them choose a unique parameter name for the profile
        unique_profile_paramater = False
        while not unique_profile_paramater:
            self.apply_unique_profile_paramater_dialog = ApplyFoundData(self.template_display.true_coords(
            ), self.template_display.found_text, dialog_type="data_information")
            if self.apply_unique_profile_paramater_dialog.exec():
                print("success")
                # If clicked confirm, then add unique file identifier to database if not exists, if exists ask user to overwrite?
                unique_file_data_information = self.apply_unique_profile_paramater_dialog.text_input.text()
                description = self.apply_unique_profile_paramater_dialog.description.text().strip().replace(" ", "_")
                example_text = self.template_display.found_text.strip().replace(" ","-")
                print()
                regex = self.apply_unique_profile_paramater_dialog.regex.text()
                if not regex:
                    regex = None
                [x_1, x_2, y_1, y_2] = self.template_display.true_coords()
                connection, cursor = db_connect(db_file_path)

                # if the paramater name is not unique, warn user and let them try again (could do a textChanged.connect and check then, may be too slow)
                if cursor.execute("""SELECT * FROM profile_paramaters WHERE profile_id=? and description=?;""",(self.current_file_profile, description)).fetchone() is not None:
                    db_disconnect(connection, cursor)
                    unique_description_error = QtWidgets.QMessageBox()
                    unique_description_error.setIcon(
                        QtWidgets.QMessageBox.Critical)
                    unique_description_error.setWindowTitle(
                        "Description Error")
                    unique_description_error.setText(
                        f"Description ({description}) already used for this file profile. Please choose another description name.")
                    unique_description_error.exec_()
                # if paramater name is unique, insert into paramater table
                else:
                    unique_profile_paramater = True
                    add_data = """INSERT INTO profile_paramaters(profile_id, description, regex, x_1, x_2, y_1, y_2, example_text) VALUES(?,?,?,?,?,?,?,?)"""
                    data = (self.current_file_profile,
                            description, regex, x_1, x_2, y_1, y_2, scrub(example_text))
                    try:
                        cursor.execute(add_data, data)
                        connection.commit()
                    except Exception as e:
                        print(f"Error inserting data: {e}")
                        add_data_error = QtWidgets.QMessageBox()
                        add_data_error.setIcon(
                            QtWidgets.QMessageBox.Critical)
                        add_data_error.setWindowTitle(
                            "Add Data Error")
                        add_data_error.setText(
                            f"Error occured when adding data to database: {e}")
                        add_data_error.exec_()
                    finally:
                        db_disconnect(connection, cursor)
            else:
                print("cancelled")
                break
        # After clicking button, draw existing paramater bounding boxes on top of template file
        try:
            self.paint_existing_data_rects()
        except Exception as e:
            print(e)
            pass

    def paint_existing_data_rects(self):
        """Draws bounding boxes on top of loaded template file for user to see which data is already being analyzed for each profile"""                
        connection, cursor = db_connect(db_file_path)
        try:
            select_rects = """SELECT x_1, x_2, y_1, y_2, description FROM profile_paramaters WHERE profile_id=?;"""
            rects_data = cursor.execute(select_rects, (self.current_file_profile,)).fetchall()
            print(rects_data)
            if rects_data:
                try:
                    self.template_display.set_data_info(rects_data)
                    # TemplateWidget.coords = rects
                    print(
                        f"templatedisplay.coords = {self.template_display.data_info}")
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
        self.file_profile_path, _ = QtWidgets.QFileDialog.getOpenFileName()
        if self.file_profile_path:
            self.update_template_pixmap()

    def update_template_pixmap(self):
        """Displays PDF file to be used for updating/creating a file_profile"""        

        image_jpeg = []
        try:
            image_jpeg = convert_from_path(
                self.file_profile_path, fmt="jpeg", poppler_path=poppler_path, single_file=True)
            img_byte_arr = io.BytesIO()
            image_jpeg[0].save(img_byte_arr, format='jpeg')
            img_byte_arr = img_byte_arr.getvalue()

            self.template_display = TemplateWidget(img_byte_arr, image_jpeg[0])

            updated_width = self.template_display.scaled_width() + 25
            updated_height = self.template_display.scaled_height(
            ) + self.select_template_file.height() + self.file_template_tab_line_1.height() * 3 + 25

            self.resize(int(updated_width), int(updated_height))
            self.file_template_tab_layout.addWidget(self.template_display, 3, 0, 20, 10)
            self.update()

            self.profile_file_loaded = True
        except Exception as e:
            print(e)
            
    # TODO: Update this function
    def email_button_handler(self):
        signature_path = os.path.abspath(os.path.join(
            home_dir + r"\\Signature\\concrete.htm"))
        signature_path_28 = os.path.abspath(os.path.join(
            home_dir + r"\\Signature\\concrete28.htm"))
        if not self.analyzed and self.file_names:
            if os.path.isfile(signature_path):
                with open(signature_path, "r") as file:
                    body_text = file.read()
                with open(signature_path_28, "r") as file:
                    body_text_28 = file.read()

            else:
                # print("Signature File Not Found")
                body_text = ""
                pass
            msg = QtWidgets.QMessageBox()
            button_reply = msg.question(msg, "", "Do you want to create e-mails for non-analyzed files?",
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if button_reply == QtWidgets.QMessageBox.No:
                self.status_output_box.appendPlainText("E-Mails not generated\n")
            elif button_reply == QtWidgets.QMessageBox.Yes:
                for file in self.file_names:
                    description = file.split("_")
                    description = description[1]
                    project_number, _, _, _, _, email_recipient_to, email_recipient_cc, email_recipient_subject = project_info(
                        test=self.test, description=description)
                    title = file.split("/").pop()
                    attachment = file
                    try:
                        outlook = win32.Dispatch('outlook.application')
                        mail = outlook.CreateItem(0)
                        mail.To = email_recipient_to
                        mail.CC = email_recipient_cc
                        mail.Subject = email_recipient_subject
                        if "28d" in title:
                            mail.HtmlBody = body_text_28
                        else:
                            mail.HtmlBody = body_text
                        mail.Attachments.Add(attachment)
                        mail.Save()
                        e = "Drafted email for: {0}".format(title)
                        self.status_output_box.appendPlainText(e)
                    except Exception as e:
                        print(e)
                        self.status_output_box.appendPlainText(e)
                        pass
        if self.analyzed:
            if os.path.isfile(signature_path):
                with open(signature_path, "r") as file:
                    body_text = file.read()
                with open(signature_path_28, "r") as file:
                    body_text_28 = file.read()
            else:
                # print("Signature File Not Found")
                body_text = ""
                pass
            all_list_titles = []
            all_list_data = []
            for i in range(self.processed_files_list_widget.count()):
                all_list_data.append(self.processed_files_list_widget.item(
                    i).data(QtCore.Qt.UserRole).split("%%")[0])
                all_list_titles.append(self.processed_files_list_widget.item(i).text())
            for i, project_number in enumerate(self.project_numbers):
                if self.project_numbers_short[i][0] == "P":
                    self.project_numbers_short[i] = self.project_numbers_short[i].replace(
                        "P-", "P-00")
                project_number, _, _, _, _, email_recipient_to, email_recipient_cc, email_recipient_subject = project_info(project_number=project_number, project_number_short=self.project_numbers_short[i],
                                                                                                                           test=self.test)
                attachment = all_list_data[i]
                try:
                    outlook = win32.Dispatch('outlook.application')
                    mail = outlook.CreateItem(0)
                    mail.To = email_recipient_to
                    mail.CC = email_recipient_cc
                    mail.Subject = email_recipient_subject
                    if "28d" in attachment:
                        mail.HtmlBody = body_text_28
                    else:
                        mail.HtmlBody = body_text
                    mail.Attachments.Add(attachment)
                    mail.Save()
                    e = "Drafted email for: {0}".format(all_list_titles[i])
                    self.status_output_box.appendPlainText(e)
                except Exception as e:
                    print(e)
                    self.status_output_box.appendPlainText(str(e))
                    pass

    def test_check(self):
        """Checks for 'Test Mode'.\n
        Mainly used for testing file analysis without saving to server locations or e-mailing to clients.\n
        Files will be saved to original location instead and e-mails will be blank.  
        """        
        if "test" in self.test_box.currentText().lower():
            self.test = True
        else:
            self.test = False

    def open_file_dialog(self):
        """Opens a file dialog to select files for input"""        

        self.dialog = QtWidgets.QFileDialog(directory=str(
            os.path.abspath(os.path.join(os.getcwd(), "test_files"))))
        self.file_names, _ = QtWidgets.QFileDialog.getOpenFileNames()

        if len(self.file_names) == 1:
            file_names_string = "(" + str(len(self.file_names)) + \
                ")" + " file has been selected: \n"
        else:
            file_names_string = "(" + str(len(self.file_names)) + \
                ")" + " files have been selected: \n"

        for item in self.file_names:
            file_names_string = file_names_string + item + "\n"

        self.status_output_box.appendPlainText(file_names_string)

    def rename_file_handler(self):
        """Upon double clicking a list item, it can leave it open for some reason and not allow it to be clicked again, so close persistant editor upon double click.
        """        

        if self.processed_files_list_widget.isPersistentEditorOpen(self.processed_files_list_widget.currentItem()):
            self.processed_files_list_widget.closePersistentEditor(
                self.processed_files_list_widget.currentItem())
        self.processed_files_list_widget.editItem(self.processed_files_list_widget.currentItem())


    # TODO: Update this function
    def file_rename_button_handler(self):
        file_path = self.processed_files_list_widget.currentItem().data(QtCore.Qt.UserRole).split("%%")
        file_path_transit_src = file_path[0]
        # Project path may be changed if project number updated so declare up here
        file_path_project_src = file_path[1]

        # See if project number is the edited string. If it is and description is == "SomeProjectDescription"
        # Then the project was previously not detected properly so assume the project edit is correct and find
        # details in the database table.
        # Before renaming occurs Old data = entry in the listWidget
        #                        New data = entry in the text edit box
        description = "SomeProjectDescription"
        old_project_number = ""
        new_project_number = ""
        project_number = ""
        project_number_short = ""
        old_package = ""
        old_title = self.processed_files_list_widget.currentItem().text()
        project_details_changed = False
        new_title = self.file_rename_line_edit.text()
        if re.search(r"-([\dPBpb\.-]+)_", old_title, re.I) is not None:
            old_project_number = re.search(
                r"-([\dPBpb\.-]+)_", old_title, re.I).groups()
            old_project_number = old_project_number[-1]
        elif re.search(r"-(NA)_", old_title, re.I) is not None:
            old_project_number = "NA"
        if re.search(r"-([\dPBpb\.-]+)_", new_title, re.I) is not None:
            new_project_number = re.search(
                r"-([\dPBpb\.-]+)_", new_title, re.I).groups()
            new_project_number = new_project_number[-1]
        if old_project_number != new_project_number:
            project_number, project_number_short, _, _, file_path, _, _, _ = project_info(
                project_number=new_project_number, project_number_short=new_project_number, test=self.test)
            project_details_changed = True
        if re.search(r"(\d+)-[\dA-z]", old_title, re.I) is not None:
            old_package = re.search(r"(\d+)-[\dA-z]", old_title, re.I).groups()
            old_package = old_package[-1]

        if project_details_changed:
            updated_file_details = old_title.replace(
                "SomeProjectDescription", description)
            updated_package = detect_package_number(
                file_path_project_src)
            updated_file_details = updated_file_details.replace(
                old_package, updated_package)
            updated_file_details = updated_file_details.replace(
                old_project_number, project_number_short)
            rename_transit_len = 260 - len(
                str(file_path_transit_src.replace(file_path_transit_src.split("\\").pop(), "")))
            rename_project_length = 260 - len(str(file_path_project_src))
            if len(updated_file_details) > rename_transit_len or len(updated_file_details) > rename_project_length:
                updated_file_details = updated_file_details.replace(
                    "Concrete", "Conc")
            if len(updated_file_details) > rename_transit_len or len(updated_file_details) > rename_project_length:
                updated_file_details = updated_file_details.replace(
                    "-2022", "")
                updated_file_details = updated_file_details.replace(
                    "-2021", "")
            if len(updated_file_details) > rename_transit_len or len(updated_file_details) > rename_project_length:
                if rename_project_length > rename_transit_len:
                    cut = rename_project_length + 4
                else:
                    cut = rename_transit_len + 4
                updated_file_details = updated_file_details.replace(".pdf", "")
                updated_file_details = updated_file_details[:-cut] + "LONG.pdf"
            rename_path_transit = os.path.abspath(os.path.join(
                file_path_transit_src.replace(
                    file_path_transit_src.split("\\").pop(), ""),
                updated_file_details + ".pdf"))
            rename_path_project = os.path.abspath(os.path.join(
                file_path_project_src, updated_file_details + ".pdf"))
            os.rename(file_path_transit_src, rename_path_transit)
            if not os.path.isfile(file_path_project_src):
                file_path_project_src = rename_path_project
            if os.path.isfile(file_path_project_src):
                if file_path_project_src != file_path_transit_src:
                    os.rename(file_path_project_src, rename_path_project)
            else:
                shutil.copy(rename_path_transit, rename_path_project)
            self.processed_files_list_widget.currentItem().setText(updated_file_details)
            data = rename_path_transit + "%%" + rename_path_project
            self.processed_files_list_widget.currentItem().setData(QtCore.Qt.UserRole, data)
            self.file_rename_line_edit.setText(updated_file_details)
            self.project_numbers_short[self.processed_files_list_widget.currentRow(
            )] = project_number_short
            self.project_numbers[self.processed_files_list_widget.currentRow()] = project_number
        else:
            # 254 to accommodate the .pdf
            rename_transit_len = 254 - \
                len(file_path_transit_src.replace(
                    file_path_transit_src.split("\\").pop(), ""))
            rename_project_len = 254 - \
                len(file_path_project_src.replace(
                    file_path_project_src.split("\\").pop(), ""))
            if len(self.file_rename_line_edit.text()) > rename_transit_len or len(self.file_rename_line_edit.text()) > rename_project_len:
                # print("Filename too long")
                if rename_transit_len > rename_project_len:
                    msg_string = f"Filename too long. Reduce by {len(self.file_rename_line_edit.text()) - rename_transit_len}"
                else:
                    msg_string = f"Filename too long. Reduce by {len(self.file_rename_line_edit.text()) - rename_project_len}"
                ctypes.windll.user32.MessageBoxW(
                    0, msg_string, "Filename Too Long", 1)
            else:
                rename_path_transit = os.path.abspath(os.path.join(
                    file_path_transit_src.replace(
                        file_path_transit_src.split("\\").pop(), ""),
                    str(self.file_rename_line_edit.text()) + ".pdf"))
                rename_path_project = os.path.abspath(os.path.join(
                    file_path_project_src.replace(
                        file_path_project_src.split("\\").pop(), ""),
                    str(self.file_rename_line_edit.text()) + ".pdf"))
                try:
                    os.rename(file_path_transit_src, rename_path_transit)
                except Exception:
                    pass
                if file_path_project_src != file_path_transit_src:  # If project and transit aren't the same, rename
                    try:
                        os.rename(file_path_project_src, rename_path_project)
                    except Exception:
                        pass
                self.processed_files_list_widget.currentItem().setText(self.file_rename_line_edit.text())
                data = rename_path_transit + "%%" + rename_path_project
                self.processed_files_list_widget.currentItem().setData(QtCore.Qt.UserRole, data)

    def evt_analyze_complete(self, results):
        """Appends processed files list widget with new processed file data

        Args:
            results (list): processed file list in format [print_string, file_name, file_path]
        """        
        print_string = results[0]
        file_name = results[1]
        file_path = results[2]
        self.status_output_box.appendPlainText(print_string)
        self.processed_files_list_item = QtWidgets.QListWidgetItem(file_name)
        self.processed_files_list_item.setData(QtCore.Qt.UserRole, file_path)
        self.processed_files_list_widget.addItem(self.processed_files_list_item)

    def evt_analyze_progress(self, val):
        """Updates main progress bar based off of emitted progress values.

        Args:
            val (int): Current progress level of file being analyzed
        """        

        # Since val is progress of each individual file, need to ensure whole progress accounts for all files
        self.progress += val
        self.progress_bar.setValue(int(self.progress / len(self.file_names)))

    def analyze_button_handler(self):
        """Handles the initialization for processing selected files."""
               
        if self.file_names is not None:
            self.test_check()
            self.analyzed = False
            self.progress = 0
            self.progress_bar.setValue(0)
            self.status_output_box.appendPlainText("Analysis Started...\n")
            self.data_processing()
            self.analyzed = True
        else:
            self.status_output_box.appendPlainText(
                "Please select at least 1 file to analyze...\n")
        self.analyze_button.setEnabled(True)

    def list_widget_handler(self):
        """Displays the currently selected list widget item"""

        file_path = str(self.processed_files_list_widget.currentItem().data(
            QtCore.Qt.UserRole))
        self.file_preview.load(QtCore.QUrl(f"file:{file_path}"))
        self.file_preview.show()
        set_text = self.processed_files_list_widget.currentItem().text()
        self.file_rename_line_edit.setText(set_text)

    def data_processing(self):
        """Processes the selected files"""

        # For each file create a new thread to increase performance
        for file_name in self.file_names:
            self.analyze_worker = WorkerAnalyzeThread(
                file_name=file_name, test=self.test, analyzed=self.analyzed)
            self.analyze_worker.signals.progress.connect(
                self.evt_analyze_progress)
            self.analyze_worker.signals.result.connect(
                self.evt_analyze_complete)
            self.thread_pool.start(self.analyze_worker)


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    window = MainWindow()
    app.exec_()
