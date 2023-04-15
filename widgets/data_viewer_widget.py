from PySide6 import QtWidgets, QtGui, QtCore
from widgets import email_list_widget, utility_widgets
from utils import utils

class DataViewerTableWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
    
        # Layout for data viewer table and related buttons
        self.data_viewer_layout = QtWidgets.QVBoxLayout()
        self.data_viewer_layout.setObjectName("data_viewer_layout")

        self.data_viewer_layout.addWidget(utility_widgets.HorizontalLine())

        # Layout for row of buttons (new/import/export/delete all)
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

        self.data_viewer_layout.addLayout(self.project_data_cta_layout)

        # Line below action buttons
        self.project_data_line_below_cta_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_2 = QtWidgets.QFrame(self.database_viewer_tab)
        self.database_tab_line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.database_tab_line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.database_tab_line_2.setObjectName("database_tab_line_2")
        self.project_data_line_below_cta_layout.addWidget(self.database_tab_line_2)

        self.data_viewer_layout.addWidget(utility_widgets.HorizontalLine())

        self.database_search_layout = QtWidgets.QHBoxLayout()
        self.database_search_layout.addStretch(2)

        self.database_search_icon = QtWidgets.QLabel()
        self.database_search_icon.setPixmap(QtGui.QPixmap(utils.resource_path("assets/icons/search.svg")))
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
        self.data_viewer_layout.addLayout(self.database_search_layout)

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

        self.data_viewer_layout.addWidget(self.database_viewer_table)

        # Line below table
        self.data_viewer_layout.addWidget(utility_widgets.HorizontalLine)

        self.translate_ui()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate

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

    def database_discard_edited_project_data(self) -> None:
        self.project_data_changed = False
        self.database_discard_edited_project_data_button.setEnabled(False)
        self.database_save_edited_project_data_button.setEnabled(False)
        if not self.adding_new:
            self.database_viewer_table.setCurrentIndex(self.project_data_loaded_id)
        return None

    def clear_project_data_entry_fields(self) -> None:
        self.database_email_to_list_widget.clear()
        self.database_email_cc_list_widget.clear()
        self.database_email_bcc_list_widget.clear()
        self.database_project_number_line_edit.clear()
        self.database_project_directory_line_edit.clear()
        self.database_project_email_subject_line_edit.clear()
        return None



class DataViewerEditWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
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
        self.database_email_to_list_widget = email_list_widget.EmailListWidget()
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
        self.database_email_cc_list_widget = email_list_widget.EmailListWidget()
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
        self.database_email_bcc_list_widget = email_list_widget.EmailListWidget()
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

        self.translate_ui()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        
        self.database_discard_edited_project_data_button.setText(
            _translate("MainWindow", "Discard Changes")
        )
        self.database_save_edited_project_data_button.setText(
            _translate("MainWindow", "Save New")
        )
        self.database_delete_project_data_button.setText(
            _translate("MainWindow", "Delete Entry")
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
        self.database_project_directory_button.setText(
            _translate("MainWindow", "Select Folder")
        )
