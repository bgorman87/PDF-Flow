from multiprocessing.reduction import duplicate
import os

from PySide6 import QtCore, QtGui, QtWidgets

from view_models import data_viewer_view_model
from widgets import email_list_widget, utility_widgets
from utils import path_utils, general_utils


class DataViewerView(QtWidgets.QWidget):
    def __init__(self, view_model: data_viewer_view_model.DataViewerViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self._project_data_loaded_data = None
        self._project_data_changed = False
        self._current_index = None
        self._adding_new_entry = False

        self.main_layout.setObjectName("main_layout")

        self.project_data_cta_layout = QtWidgets.QHBoxLayout()

        # Add new data button
        self.project_data_add_new_button = QtWidgets.QPushButton()
        self.project_data_add_new_button.clicked.connect(
            self.project_data_add_new)
        self.project_data_cta_layout.addWidget(self.project_data_add_new_button)

        # Import project data button
        self.import_project_data_button = QtWidgets.QPushButton()
        self.import_project_data_button.clicked.connect(
            self.view_model.get_project_data_import_file
        )
        self.project_data_cta_layout.addWidget(self.import_project_data_button)

        # Export project data button
        self.export_project_data_button = QtWidgets.QPushButton()
        self.export_project_data_button.clicked.connect(
            self.view_model.get_project_data_export_location
        )
        self.view_model.main_view_model.process_button_state_update.connect(
            lambda: self.export_project_data_button.setEnabled(
                self.view_model.main_view_model.process_button_state
            )
        )
        self.project_data_cta_layout.addWidget(self.export_project_data_button)

        # Delete all project data button
        self.delete_all_project_data_button = QtWidgets.QPushButton()
        self.delete_all_project_data_button.clicked.connect(
            self.view_model.delete_all_project_data_verification
        )
        self.delete_all_project_data_button.setProperty("class", "delete-button")
        self.project_data_cta_layout.addWidget(self.delete_all_project_data_button)

        self.main_layout.addLayout(self.project_data_cta_layout)

        # Line below action buttons
        self.project_data_line_below_cta_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_2 = utility_widgets.HorizontalLine()
        self.project_data_line_below_cta_layout.addWidget(self.database_tab_line_2)

        self.main_layout.addLayout(self.project_data_line_below_cta_layout)

        self.database_search_layout = QtWidgets.QHBoxLayout()
        
        self.duplicate_button = QtWidgets.QPushButton("Duplicate")
        self.duplicate_button.clicked.connect(self.duplicate_project_data)
        self.duplicate_button.setEnabled(False)
        self.database_search_layout.addWidget(self.duplicate_button)
        self.database_search_layout.setStretch(
            self.database_search_layout.indexOf(self.duplicate_button), 1
        )

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
        self.main_layout.addLayout(self.database_search_layout)

        # Table widget to display DB results
        self.database_viewer_table = QtWidgets.QTableWidget()
        self.view_model.data_table_index_update.connect(self.set_data_viewer_index)
        # model = QtCore.QSortFilterProxyModel()
        # self.database_viewer_table.setModel(model)
        self.database_viewer_table.currentItemChanged.connect(
            self.project_data_discard_check
        )
        # Enable sorting for table widget
        self.database_viewer_table.setSortingEnabled(True)
        self.database_viewer_table.setSelectionMode(
            QtWidgets.QTableWidget.SingleSelection
        )
        self.database_viewer_table.setEditTriggers(
            QtWidgets.QTableWidget.NoEditTriggers
        )
        self.view_model.data_table_update.connect(
            lambda: self.update_data_table(
                project_data=self.view_model.project_data,
                headers=self.view_model.project_data_headers,
            )
        )

        self.main_layout.addWidget(self.database_viewer_table)

        # Line below table
        self.project_data_line_below_table_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_3 = utility_widgets.HorizontalLine()
        self.project_data_line_below_table_layout.addWidget(self.database_tab_line_3)
        self.main_layout.addLayout(self.project_data_line_below_table_layout)

        # Line below table
        self.project_data_line_below_table_2_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_4 = utility_widgets.HorizontalLine()
        self.project_data_line_below_table_2_layout.addWidget(self.database_tab_line_4)
        self.main_layout.addLayout(self.project_data_line_below_table_2_layout)

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
        self.database_project_number_line_edit.setProperty("edited", False)
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

        self.main_layout.addLayout(self.project_data_project_number_line_layout)

        self.project_data_directory_layout = QtWidgets.QHBoxLayout()

        # Label for directory line edit
        self.database_directory_label = QtWidgets.QLabel()
        self.database_directory_label.setObjectName("database_directory_label")
        self.project_data_directory_layout.addWidget(self.database_directory_label)

        # Project directory line edit
        self.database_project_directory_line_edit = QtWidgets.QLineEdit()
        self.database_project_directory_line_edit.setProperty("edited", False)
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
        self.main_layout.addLayout(self.project_data_directory_layout)

        self.project_data_description_layout = QtWidgets.QHBoxLayout()
        self.project_data_description_label = QtWidgets.QLabel()
        self.project_data_description_label.setObjectName(
            "project_data_description_label"
        )
        self.project_data_description_layout.addWidget(
            self.project_data_description_label
        )
        self.project_data_description_line_edit = QtWidgets.QLineEdit()
        self.project_data_description_line_edit.setProperty("edited", False)
        self.project_data_description_line_edit.setObjectName(
            "project_data_description_line_edit"
        )
        self.project_data_description_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.project_data_description_line_edit, "description"
            )
        )
        self.project_data_description_layout.addWidget(
            self.project_data_description_line_edit
        )

        self.main_layout.addLayout(self.project_data_description_layout)

        self.project_data_email_subject_layout = QtWidgets.QHBoxLayout()

        # Label for email subject line edit
        self.database_email_subject_label = QtWidgets.QLabel()
        self.database_email_subject_label.setObjectName("database_email_subject_label")
        self.project_data_email_subject_layout.addWidget(
            self.database_email_subject_label
        )

        # Project email subject line edit
        self.database_project_email_subject_line_edit = QtWidgets.QLineEdit()
        self.database_project_email_subject_line_edit.setProperty("edited", False)
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
        self.main_layout.addLayout(self.project_data_email_subject_layout)

        self.profile_email_layout = QtWidgets.QHBoxLayout()
        # Label for dropdown menu
        self.profile_email_label = QtWidgets.QLabel()
        self.profile_email_label.setObjectName(
            "profile_email_label"
        )
        self.profile_email_layout.addWidget(self.profile_email_label)

        # Dropdown menu containing e-mail profiles
        self.profile_email_combo_box = QtWidgets.QComboBox()
        self.profile_email_combo_box.setProperty("edited", False)
        self.profile_email_combo_box.setObjectName(
            "profile_email_combo_box"
        )
    
        self.view_model.email_profile_list_update.connect(
            self.handle_email_profile_list_update
        )
        self.profile_email_combo_box.currentIndexChanged.connect(
            lambda: self.project_data_change_check(
                self.profile_email_combo_box, "email_profile_name"
            )
        )
        self.profile_email_layout.addWidget(self.profile_email_combo_box)

        self.profile_email_combo_box_helper = QtWidgets.QPushButton()
        self.profile_email_combo_box_helper.setMaximumSize(QtCore.QSize(28, 28))
        icon = QtGui.QIcon()
        icon.addFile(path_utils.resource_path(u"assets/icons/tooltip.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.profile_email_combo_box_helper.setIcon(icon)
        self.profile_email_combo_box_helper.setProperty("class", "invert-icon")
        self.profile_email_combo_box_helper.setIconSize(QtCore.QSize(12, 12))

        self.profile_email_combo_box_helper.setObjectName(
            "profile_email_combo_box_helper"
        )
        self.profile_email_combo_box_helper.setToolTip(
            "Tip: Project specific email template will take precedence over profile email template."
        )
        self.profile_email_combo_box_helper.clicked.connect(
            self.display_tooltip
        )
        self.profile_email_layout.addWidget(self.profile_email_combo_box_helper)

        self.profile_email_layout.setStretch(
            self.profile_email_layout.indexOf(self.profile_email_combo_box), 6
        )
        self.main_layout.addLayout(self.profile_email_layout)

        self.project_data_email_lists_layout = QtWidgets.QHBoxLayout()
        self.project_data_email_to_layout = QtWidgets.QVBoxLayout()

        # Label for email to list widget
        self.database_email_to_label = QtWidgets.QLabel()
        self.database_email_to_label.setObjectName("database_email_to_label")
        self.project_data_email_to_layout.addWidget(self.database_email_to_label)

        # Email to list widget
        self.database_email_to_list_widget = email_list_widget.EmailListWidget()
        self.database_email_to_list_widget.setProperty("edited", False)
        self.database_email_to_list_widget.setProperty("email_type", "email_to")
        # Enable dragging and dropping of items within the list widget
        self.database_email_to_list_widget.setDragDropMode(
            QtWidgets.QListWidget.InternalMove
        )
        # Enable editing of items by double-clicking on them
        self.database_email_to_list_widget.setEditTriggers(
            QtWidgets.QListWidget.DoubleClicked
        )
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

        # Add 2 buttons to add new item and edit bulk items
        self.database_email_to_list_button_layout = QtWidgets.QHBoxLayout()

        # Add new item button
        self.database_email_to_list_add_button = QtWidgets.QPushButton()
        self.database_email_to_list_add_button.clicked.connect(
            self.database_email_to_list_widget.add_new_email
        )
        self.database_email_to_list_add_button.setObjectName(
            "database_email_to_list_add_button"
        )
        self.database_email_to_list_button_layout.addWidget(
            self.database_email_to_list_add_button
        )

        # Edit bulk items button
        self.database_email_to_list_edit_button = QtWidgets.QPushButton()
        self.database_email_to_list_edit_button.clicked.connect(
            lambda: self.database_list_widget_edit_bulk(
                self.database_email_to_list_widget
            )
        )
        self.database_email_to_list_edit_button.setObjectName(
            "database_email_to_list_edit_button"
        )
        self.database_email_to_list_button_layout.addWidget(
            self.database_email_to_list_edit_button
        )

        self.project_data_email_to_layout.addLayout(
            self.database_email_to_list_button_layout
        )

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_to_layout
        )

        self.project_data_email_cc_layout = QtWidgets.QVBoxLayout()
        # Label for email cc list widget
        self.database_email_cc_label = QtWidgets.QLabel()
        self.database_email_cc_label.setObjectName("database_email_cc_label")
        self.project_data_email_cc_layout.addWidget(self.database_email_cc_label)

        # Email cc list widget
        self.database_email_cc_list_widget = email_list_widget.EmailListWidget()
        self.database_email_cc_list_widget.setProperty("edited", False)
        self.database_email_cc_list_widget.setProperty("email_type", "email_cc")
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

        # Add 2 buttons to add new item and edit bulk items
        self.database_email_cc_list_button_layout = QtWidgets.QHBoxLayout()

        # Add new item button
        self.database_email_cc_list_add_button = QtWidgets.QPushButton()
        self.database_email_cc_list_add_button.clicked.connect(
            self.database_email_cc_list_widget.add_new_email
        )
        self.database_email_cc_list_add_button.setObjectName(
            "database_email_cc_list_add_button"
        )
        self.database_email_cc_list_button_layout.addWidget(
            self.database_email_cc_list_add_button
        )

        # Edit bulk items button
        self.database_email_cc_list_edit_button = QtWidgets.QPushButton()
        self.database_email_cc_list_edit_button.clicked.connect(
            lambda: self.database_list_widget_edit_bulk(
                self.database_email_cc_list_widget
            )
        )
        self.database_email_cc_list_edit_button.setObjectName(
            "database_email_cc_list_edit_button"
        )
        self.database_email_cc_list_button_layout.addWidget(
            self.database_email_cc_list_edit_button
        )

        self.project_data_email_cc_layout.addLayout(
            self.database_email_cc_list_button_layout
        )

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
        self.database_email_bcc_list_widget.setProperty("edited", False)
        self.database_email_bcc_list_widget.setProperty("email_type", "email_bcc")
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

        # Add 2 buttons to add new item and edit bulk items
        self.database_email_bcc_list_button_layout = QtWidgets.QHBoxLayout()

        # Add new item button
        self.database_email_bcc_list_add_button = QtWidgets.QPushButton()
        self.database_email_bcc_list_add_button.clicked.connect(
            self.database_email_bcc_list_widget.add_new_email
        )
        self.database_email_bcc_list_add_button.setObjectName(
            "database_email_bcc_list_add_button"
        )
        self.database_email_bcc_list_button_layout.addWidget(
            self.database_email_bcc_list_add_button
        )

        # Edit bulk items button
        self.database_email_bcc_list_edit_button = QtWidgets.QPushButton()
        self.database_email_bcc_list_edit_button.clicked.connect(
            lambda: self.database_list_widget_edit_bulk(
                self.database_email_bcc_list_widget
            )
        )
        self.database_email_bcc_list_edit_button.setObjectName(
            "database_email_bcc_list_edit_button"
        )
        self.database_email_bcc_list_button_layout.addWidget(
            self.database_email_bcc_list_edit_button
        )

        self.project_data_email_bcc_layout.addLayout(
            self.database_email_bcc_list_button_layout
        )

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_bcc_layout
        )
        self.main_layout.addLayout(self.project_data_email_lists_layout)

        # Line above buttons
        self.cta_button_line_layout = QtWidgets.QHBoxLayout()
        self.cta_button_line = utility_widgets.HorizontalLine()
        self.cta_button_line_layout.addWidget(self.cta_button_line)
        self.main_layout.addLayout(self.cta_button_line_layout)

        self.project_data_bottom_cta_layout = QtWidgets.QHBoxLayout()

        # Action button to save manual changes
        self.database_save_edited_project_data_button = QtWidgets.QPushButton()
        self.database_save_edited_project_data_button.clicked.connect(
            self.save_project_data
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
            self.project_data_discard_check
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
        self.view_model.project_data_entry_deleted.connect(
            self.project_data_deleted_slot
        )

        self.view_model.all_project_data_deleted.connect(
            self.project_data_deleted_slot
        )

        self.main_layout.addLayout(self.project_data_bottom_cta_layout)

        self.view_model.main_view_model.fetch_all_project_data()

        self.setLayout(self.main_layout)

        self._project_data_editable_widgets_list = [
            self.database_project_number_line_edit,
            self.database_project_directory_line_edit,
            self.project_data_description_line_edit,
            self.database_project_email_subject_line_edit,
            self.profile_email_combo_box,
            self.database_email_to_list_widget,
            self.database_email_cc_list_widget,
            self.database_email_bcc_list_widget,
        ]

        self.translate_ui()
        self.view_model.update_data_table()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.database_email_to_label.setText(_translate("MainWindow", "Email TO List:"))
        self.database_email_cc_label.setText(_translate("MainWindow", "Email CC List:"))
        self.database_email_bcc_label.setText(
            _translate("MainWindow", "Email BCC List:")
        )
        self.database_project_number_label.setText(
            _translate("MainWindow", "Project Number:")
        )
        self.project_data_description_label.setText(
            _translate("MainWindow", "Project Description:")
        )
        self.database_directory_label.setText(_translate("MainWindow", "Directory:"))
        self.database_email_subject_label.setText(
            _translate("MainWindow", "Email Subject:")
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
        self.database_discard_edited_project_data_button.setText(
            _translate("MainWindow", "Discard Changes")
        )
        self.database_save_edited_project_data_button.setText(
            _translate("MainWindow", "Save")
        )
        self.database_delete_project_data_button.setText(
            _translate("MainWindow", "Delete Entry")
        )
        self.profile_email_label.setText(
            _translate("MainWindow", "Project Email Profile:")
        )
        self.database_email_to_list_add_button.setText(
            _translate("MainWindow", "Add New")
        )
        self.database_email_to_list_edit_button.setText(
            _translate("MainWindow", "Edit Bulk")
        )
        self.database_email_cc_list_add_button.setText(
            _translate("MainWindow", "Add New")
        )
        self.database_email_cc_list_edit_button.setText(
            _translate("MainWindow", "Edit Bulk")
        )
        self.database_email_bcc_list_add_button.setText(
            _translate("MainWindow", "Add New")
        )
        self.database_email_bcc_list_edit_button.setText(
            _translate("MainWindow", "Edit Bulk")
        )

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

    def update_data_table(self, project_data: list[str], headers: list[str]):
        if not project_data:
            self.database_viewer_table.clear()
            self.database_viewer_table.setRowCount(0)
            self.database_viewer_table.setColumnCount(0)
            self.export_project_data_button.setEnabled(False)
            self.delete_all_project_data_button.setEnabled(False)
            return
        
        self.export_project_data_button.setEnabled(True)
        self.delete_all_project_data_button.setEnabled(True)
        self.database_viewer_table.currentItemChanged.disconnect()
        self.database_viewer_table.clear()
        # self.clear_project_data_fields()
        # TODO: Set current table index to the one just saved
        self.display_data_as_table(project_data=project_data, headers=headers)
        self.database_viewer_table.sortItems(0, QtCore.Qt.AscendingOrder)
        self.update()
        self.database_viewer_table.currentItemChanged.connect(
            self.project_data_discard_check
        )

    def display_data_as_table(self, project_data: list[str], headers: list[str]):
        self.database_viewer_table.setSortingEnabled(False)
        self.database_viewer_table.setRowCount(0)
        table_widget_item = QtWidgets.QTableWidgetItem
        # try to assign data to variables

        self.database_viewer_table.setColumnCount(len(headers))
        self.database_viewer_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        # Add headers to table
        for col, header_text in enumerate(headers):
            self.database_viewer_table.setHorizontalHeaderItem(
                col, table_widget_item(header_text)
            )
        # Add data to table
        for row, row_data in enumerate(project_data):
            self.database_viewer_table.insertRow(row)
            for column, item in enumerate(row_data):
                self.database_viewer_table.setItem(
                    row, column, table_widget_item(str(item))
                )
        self.filter_table()
        self.database_viewer_table.setSortingEnabled(True)

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
                    if search_term.lower() in item_text.lower():
                        # If the search term is found, show the entire row and break out of the column loop
                        self.database_viewer_table.setRowHidden(row, False)
                        # Show all cells in the row
                        for column in range(self.database_viewer_table.columnCount()):
                            self.database_viewer_table.setColumnHidden(column, False)
                        row_count += 1
                        break
                except AttributeError:
                    pass

        # if theres data in filtered results, and a row is chosen, enable the delete button
        # if row_count > 0 and self._current_index is not None:
        #     self.database_delete_project_data_button.setEnabled(True)
        # else:
        #     self.database_delete_project_data_button.setEnabled(False)
    

    def set_data_viewer_index(self, index: int):
        self.database_viewer_table.setCurrentIndex(index)

    def clear_project_data_fields(self):
        self.disconnect_widget_signals()
        self.database_project_number_line_edit.setText("")
        self.database_project_directory_line_edit.setText("")
        self.project_data_description_line_edit.setText("")
        self.database_project_email_subject_line_edit.setText("")
        self.database_email_to_list_widget.clear()
        self.database_email_cc_list_widget.clear()
        self.database_email_bcc_list_widget.clear()
        self.profile_email_combo_box.setCurrentIndex(0)
        self.connect_widget_signals()

    def project_data_discard_check(self):
        # If user presses new entry, but then selects an existing entry, and the new entry fields are blank
        # then user is not adding a new entry, and just wants the selected entry to display
        if self._adding_new_entry:
            for widget in self._project_data_editable_widgets_list:
                if widget.property("edited"):
                    self._adding_new_entry = True
                    break
                else:
                    self._adding_new_entry = False

        if self._project_data_changed or self._adding_new_entry:
            # Create a popup asking if user wants to discard changes
            message_box = general_utils.MessageBox()
            message_box.title = "Discard Changes"
            message_box.icon = QtWidgets.QMessageBox.Warning
            message_box.text = f"Are you sure you want to discard changes?"
            message_box.buttons = ["Discard", "Cancel"]
            message_box.button_roles = [QtWidgets.QMessageBox.YesRole, QtWidgets.QMessageBox.NoRole]
            message_box.callback = [
                self.handle_project_data_update,
                self.reset_database_current_active_id,
            ]
            
            self.view_model.main_view_model.display_message_box(message_box=message_box)
        else:
            self.handle_project_data_update()

    def reset_database_current_active_id(self):
        if self._adding_new_entry:
            # No id to change to, keep current data and return
            return
        
        # If user discards and then presses cancel
        # Try to set the current index to the last selected index
        if self._current_index:
            self.database_viewer_table.currentItemChanged.disconnect()
            self.set_focus_select_and_highlight_cell(
                self._current_index.row(), self._current_index.column()
            )
            self.database_viewer_table.currentItemChanged.connect(
                self.project_data_discard_check
            )

    def set_focus_select_and_highlight_cell(self, row: int, column: int):
        # TODO: This doesn't work. Find a way to programmatically set the "selected" attribute for use in the QSS style file
        self.database_viewer_table.setFocus()
        self.database_viewer_table.clearSelection()
        try:
            found_items = self.database_viewer_table.findItems(
                self.database_viewer_table.item(row, column).text(), QtCore.Qt.MatchExactly
            )
            index = self.database_viewer_table.indexFromItem(found_items[0])
            self.database_viewer_table.setCurrentIndex(index)
            self.database_viewer_table.setCurrentItem(found_items[0])
            self.database_viewer_table.selectionModel().select(
                index, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Current
            )
            self.database_viewer_table.repaint()
            return
        except IndexError:
            pass

        index = self.database_viewer_table.model().index(row, column)
        self.database_viewer_table.setCurrentIndex(index)
        self.database_viewer_table.selectionModel().select(
                index, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Current
            )
        self.database_viewer_table.repaint()

        self._current_index = self.database_viewer_table.selectionModel().currentIndex()

        self.repaint()
        self.update()       


    def handle_project_data_update(self):

        # If adding a new entry, this function is only called from discarding changes dialog. So just clear fields and return
        self._adding_new_entry = False
        self._project_data_changed = False
        
        # Otherwise called when user clicks a new entry, or discards changes
        self.disable_buttons()
        self.clear_project_data_fields()

        # If user discards changes and theres no data in table
        # reconnect the signal and return
        if self.database_viewer_table.rowCount() == 0:
            self._project_data_loaded_data = None
            self.database_delete_project_data_button.setEnabled(False)
            return
        
        current_row = self.database_viewer_table.currentRow()
        if current_row:
            self._current_index = self.database_viewer_table.selectionModel().currentIndex()
        
        self.database_viewer_table.currentItemChanged.disconnect()
        if current_row == -1 and self._current_index:
            temp_row = self.view_model.get_next_visible_row_index(self._current_index.row(), self.database_viewer_table)
            if temp_row != -1:
                current_row = temp_row
                self.set_focus_select_and_highlight_cell(current_row, 1)

        # If there is no next visible data in table, return
        if current_row == -1:
            self._project_data_loaded_data = None
            self.database_delete_project_data_button.setEnabled(False)
            self.database_viewer_table.currentItemChanged.connect(
                self.project_data_discard_check
            )
            return None
        
        self._project_data_loaded_data = self.project_data_from_row(current_row)
        self.duplicate_button.setEnabled(True)
        self.update_list_widget_edited_properties(False)
        self.database_populate_project_edit_fields()
        
        self.database_viewer_table.currentItemChanged.connect(
            self.project_data_discard_check
        )
        # After populating fields, enable the delete entry button
        self.database_delete_project_data_button.setEnabled(True)

    def database_populate_project_edit_fields(self):

        self.disconnect_widget_signals()
        
        self._project_data_changed = False
        self.database_project_number_line_edit.setText(
            self._project_data_loaded_data["project_number"]
        )
        self.database_project_directory_line_edit.setText(
            self._project_data_loaded_data["directory"]
        )
        self.project_data_description_line_edit.setText(
            self._project_data_loaded_data["description"]
        )
        self.database_project_email_subject_line_edit.setText(
            self._project_data_loaded_data["email_subject"]
        )

        for widget in [self.database_email_to_list_widget, self.database_email_cc_list_widget, self.database_email_bcc_list_widget]:
            index = widget.property("email_type")
            email_addresses = self._project_data_loaded_data[index].split(";")
            email_addresses = [address.strip() for address in email_addresses]
            for email_address in email_addresses:
                # Dont add blank emails to list (sometimes users add rogue ; to email list)
                if email_address is None or email_address == "":
                    continue
                email_address_item = QtWidgets.QListWidgetItem(email_address)
                email_address_item.setFlags(
                    email_address_item.flags() | QtCore.Qt.ItemIsEditable
                )
                widget.addItem(email_address_item)
        
        # Set the email profile combo box to the correct profile
        email_profile_name = self._project_data_loaded_data["email_profile_name"]
        index = self.profile_email_combo_box.findText(email_profile_name)
        if index != -1:
            self.profile_email_combo_box.setCurrentIndex(index)
        else:
            self.profile_email_combo_box.setCurrentIndex(0)

        self.connect_widget_signals()

    def project_data_change_check(self, widget: QtWidgets.QWidget, project_data_type: str):
        new_text = None

        if isinstance(widget, QtWidgets.QLineEdit):
            new_text = widget.text()
        elif isinstance(widget, QtWidgets.QListWidget):
            item_texts = [widget.item(i).text() for i in range(widget.count()) if widget.item(i).text()]
            new_text = "; ".join(item_texts)
        elif isinstance(widget, QtWidgets.QComboBox):
            new_text = widget.currentText()

        if self._project_data_loaded_data is None:
            if new_text:
                self._adding_new_entry = True
                widget.setProperty("edited", True)
            else:
                widget.setProperty("edited", False)
            
        if self._project_data_loaded_data is not None:
            if new_text != self._project_data_loaded_data[project_data_type]:
                self._project_data_changed = True
                widget.setProperty("edited", True)
            else:
                widget.setProperty("edited", False)

        self.project_data_save_button_check()


    def project_data_save_button_check(self):

        # Check if any widget has their "edited" property set to True
        for widget in self._project_data_editable_widgets_list:
            if widget.property("edited"):
                self.enable_buttons()
                return None
        
        self._project_data_changed = False
        self.disable_buttons()

    def disconnect_widget_signals(self):
        for widget in self._project_data_editable_widgets_list:
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.editingFinished.disconnect()
            elif isinstance(widget, QtWidgets.QListWidget):
                widget.itemChanged.disconnect()
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.disconnect()

    def connect_widget_signals(self):
        self.database_project_number_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.database_project_number_line_edit, "project_number"
            )
        )
        self.database_project_directory_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.database_project_directory_line_edit, "directory"
            )
        )
        self.project_data_description_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.project_data_description_line_edit, "description"
            )
        )
        self.database_project_email_subject_line_edit.editingFinished.connect(
            lambda: self.project_data_change_check(
                self.database_project_email_subject_line_edit, "email_subject"
            )
        )
        self.profile_email_combo_box.currentIndexChanged.connect(
            lambda: self.project_data_change_check(
                self.profile_email_combo_box, "email_profile_name"
            )
        )
        self.database_email_to_list_widget.itemChanged.connect(
            lambda: self.project_data_change_check(
                self.database_email_to_list_widget, "email_to"
            )
        )
        self.database_email_cc_list_widget.itemChanged.connect(
            lambda: self.project_data_change_check(
                self.database_email_cc_list_widget, "email_cc"
            )
        )
        self.database_email_bcc_list_widget.itemChanged.connect(
            lambda: self.project_data_change_check(
                self.database_email_bcc_list_widget, "email_bcc"
            )
        )

    def update_list_widget_edited_properties(self, edited: bool):
        for widget in self._project_data_editable_widgets_list:
            widget.setProperty("edited", edited)

    def enable_buttons(self):
        self.database_discard_edited_project_data_button.setEnabled(True)
        self.database_save_edited_project_data_button.setEnabled(True)

    def disable_buttons(self):
        self.database_discard_edited_project_data_button.setEnabled(False)
        self.database_save_edited_project_data_button.setEnabled(False)

    def discard_project_data_changes(self):
        self.disable_buttons()
        self.clear_project_data_fields()
        self.handle_project_data_update()

    def database_delete_project_data(self):
        if self._current_index is None or not self._project_data_loaded_data:
            return None
        self.view_model.delete_project_data_entry_verification(self._project_data_loaded_data)

    def project_data_deleted_slot(self):
        self._project_data_changed = False
        self.clear_project_data_fields()
        self.disable_buttons()
        self._project_data_loaded_data = None
        self.database_delete_project_data_button.setEnabled(False)

    def get_new_project_data(self):
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
        ] = self.database_project_directory_line_edit.text()
        new_project_data[
            "description"
        ] = self.project_data_description_line_edit.text()
        new_project_data[
            "email_subject"
        ] = self.database_project_email_subject_line_edit.text()
        new_project_data[
            "email_profile_name"
        ] = self.profile_email_combo_box.currentText()
        
        return new_project_data

    def save_project_data(self):
        
        new_project_data = self.get_new_project_data()
        if not new_project_data["project_number"]:
            self.view_model.display_warning_message(message="Project Number cannot be blank")
            return None
        
        self.disable_buttons()

        if self._adding_new_entry:
            self.view_model.database_save_new_project_data(new_project_data)
            self._project_data_loaded_data = self.project_data_from_dict(new_project_data)
        elif self._project_data_changed:
            self.view_model.database_save_edited_project_data(self._project_data_loaded_data, new_project_data)
            self._project_data_loaded_data = self.project_data_from_dict(new_project_data)

        self._project_data_changed = False
        self._adding_new_entry = False

        self.update_list_widget_edited_properties(False)

    def project_data_from_row(self, row: int) -> dict:

        return {
            "project_number": self.database_viewer_table.item(row, 0).text(),
            "directory": self.database_viewer_table.item(row, 1).text(),
            "description": self.database_viewer_table.item(row, 2).text(),
            "email_to": self.database_viewer_table.item(row, 3).text(),
            "email_cc": self.database_viewer_table.item(row, 4).text(),
            "email_bcc": self.database_viewer_table.item(row, 5).text(),
            "email_subject": self.database_viewer_table.item(row, 6).text(),
            "email_profile_name": self.database_viewer_table.item(row, 7).text(),
        }

    def project_data_from_dict(self, project_data: dict) -> dict:

        return {
            "project_number": project_data["project_number"],
            "directory": project_data["directory"],
            "description": project_data["description"],
            "email_to": project_data["email_to"],
            "email_cc": project_data["email_cc"],
            "email_bcc": project_data["email_bcc"],
            "email_subject": project_data["email_subject"],
            "email_profile_name": project_data["email_profile_name"],
        }
    
    def duplicate_project_data(self):
        if self._current_index is None or not self._project_data_loaded_data:
            return None

        new_project_data = self._project_data_loaded_data.copy()

        self.project_data_add_new()

        new_project_data["project_number"] = ""
        self._project_data_loaded_data = new_project_data
        self.database_populate_project_edit_fields()
        self._project_data_changed = True
        self.enable_buttons()
        self.database_delete_project_data_button.setEnabled(False)
        self.duplicate_button.setEnabled(False)
        self.database_project_number_line_edit.setFocus()

    def project_data_add_new(self) -> None:

        self._project_data_loaded_data = None

        self._adding_new_entry = True
        self._project_data_changed = False
        self.clear_project_data_fields()
        self.database_delete_project_data_button.setEnabled(False)
        self.disable_buttons()
        
        return None

    def handle_email_profile_list_update(self):
        email_list = self.view_model.email_profile_list
        current_email_name = self.profile_email_combo_box.currentText()
        self.profile_email_combo_box.clear()
        self.profile_email_combo_box.addItems(email_list)
        self.profile_email_combo_box.setCurrentIndex(
            self.profile_email_combo_box.findText(current_email_name)
        )

    def display_tooltip(self):
        text = "If an email template is chosen for a project, it will take precedence over the specific file type email template defined in the 'File Name' tab.\n"\
        "\nLeave this blank to use the specific file type email template."

        self.view_model.display_tooltip(text=text)

    def database_list_widget_edit_bulk(self, email_widget: email_list_widget.EmailListWidget):
        """Opens a dialog to edit all items in a list widget at once."""
        
        emails = []
        for i in range(email_widget.count()):
            emails.append(email_widget.item(i).text())

        title = "Bulk Edit Email Addresses"
        email_type = str(email_widget.property("email_type")).replace('email_','').upper()
        label = "Email Addresses (separate with ';')"
        default_text = "; ".join(emails)

        line_edit_text = utility_widgets.LineEditDialog(self, title=title, label=label, prefix=email_type, default_text=default_text)
        if line_edit_text is not None and line_edit_text != default_text:
            new_emails = line_edit_text.split(";")
            new_emails = [email.strip() for email in new_emails]
            email_widget.set_items(new_emails)

        self.project_data_change_check(email_widget, email_widget.property("email_type"))

