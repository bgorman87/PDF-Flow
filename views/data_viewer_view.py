from PySide6 import QtCore, QtGui, QtWidgets

from view_models import data_viewer_view_model
from widgets import email_list_widget, utility_widgets


class DataViewerView(QtWidgets.QWidget):
    def __init__(self, view_model: data_viewer_view_model.DataViewerViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()

        self.main_layout.setObjectName(
            "main_layout")

        self.project_data_cta_layout = QtWidgets.QHBoxLayout()

        # Add new data button
        self.project_data_add_new_button = QtWidgets.QPushButton()
        # self.project_data_add_new_button.clicked.connect(
        #     self.project_data_add_new)
        self.project_data_cta_layout.addWidget(
            self.project_data_add_new_button)

        # Import project data button
        self.import_project_data_button = QtWidgets.QPushButton()
        self.import_project_data_button.clicked.connect(
            self.view_model.get_project_data_import_file)
        self.project_data_cta_layout.addWidget(self.import_project_data_button)

        # Export project data button
        self.export_project_data_button = QtWidgets.QPushButton()
        self.export_project_data_button.clicked.connect(
            self.view_model.get_project_data_export_location)
        self.project_data_cta_layout.addWidget(self.export_project_data_button)

        # Delete all project data button
        self.delete_all_project_data_button = QtWidgets.QPushButton()
        # self.delete_all_project_data_button.clicked.connect(
        #     self.delete_all_project_data
        # )
        self.delete_all_project_data_button.setProperty(
            "class", "delete-button")
        self.project_data_cta_layout.addWidget(
            self.delete_all_project_data_button)

        self.main_layout.addLayout(self.project_data_cta_layout)

        # Line below action buttons
        self.project_data_line_below_cta_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_2 = utility_widgets.HorizontalLine()
        self.project_data_line_below_cta_layout.addWidget(
            self.database_tab_line_2)

        self.main_layout.addLayout(
            self.project_data_line_below_cta_layout
        )

        self.database_search_layout = QtWidgets.QHBoxLayout()
        self.database_search_layout.addStretch(2)

        self.database_search_icon = QtWidgets.QLabel()
        self.database_search_icon.setPixmap(
            QtGui.QPixmap("assets/icons/search.svg"))
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
        # Enable sorting for table widget
        # self.database_viewer_table.setSortingEnabled(True)
        self.database_viewer_table.setSelectionMode(
            QtWidgets.QTableWidget.SingleSelection
        )
        self.database_viewer_table.setEditTriggers(
            QtWidgets.QTableWidget.NoEditTriggers
        )
        self.view_model.data_table_update.connect(lambda: self.update_data_table(
            project_data=self.view_model.project_data, headers=self.view_model.project_data_headers))
        # self.database_viewer_table.setModel(QtCore.QSortFilterProxyModel())
        # self.database_viewer_table.currentItemChanged.connect(
        #     self.database_populate_project_edit_fields
        # )

        self.main_layout.addWidget(self.database_viewer_table)

        # Line below table
        self.project_data_line_below_table_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_3 = utility_widgets.HorizontalLine()
        self.project_data_line_below_table_layout.addWidget(
            self.database_tab_line_3)
        self.main_layout.addLayout(
            self.project_data_line_below_table_layout
        )

        # Line below table
        self.project_data_line_below_table_2_layout = QtWidgets.QHBoxLayout()
        self.database_tab_line_4 = utility_widgets.HorizontalLine()
        self.project_data_line_below_table_2_layout.addWidget(
            self.database_tab_line_4)
        self.main_layout.addLayout(
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
        # self.database_project_number_line_edit.editingFinished.connect(
        #     lambda: self.project_data_change_check(
        #         self.database_project_number_line_edit, "project_number"
        #     )
        # )
        self.project_data_project_number_line_layout.addWidget(
            self.database_project_number_line_edit
        )

        self.main_layout.addLayout(
            self.project_data_project_number_line_layout
        )

        self.project_data_directory_layout = QtWidgets.QHBoxLayout()

        # Label for directory line edit
        self.database_directory_label = QtWidgets.QLabel()
        self.database_directory_label.setObjectName("database_directory_label")
        self.project_data_directory_layout.addWidget(
            self.database_directory_label)

        # Project directory line edit
        self.database_project_directory_line_edit = QtWidgets.QLineEdit()
        self.database_project_directory_line_edit.setObjectName(
            "database_project_directory_line_edit"
        )
        # self.database_project_directory_line_edit.editingFinished.connect(
        #     lambda: self.project_data_change_check(
        #         self.database_project_directory_line_edit, "directory"
        #     )
        # )
        self.project_data_directory_layout.addWidget(
            self.database_project_directory_line_edit
        )

        # Action button to call rename function
        self.database_project_directory_button = QtWidgets.QPushButton()
        # self.database_project_directory_button.clicked.connect(
        #     self.database_project_directory
        # )
        self.database_project_directory_button.setObjectName(
            "database_project_directory_button"
        )
        self.project_data_directory_layout.addWidget(
            self.database_project_directory_button
        )

        self.project_data_directory_layout.setStretch(0, 1)
        self.project_data_directory_layout.setStretch(1, 10)
        self.project_data_directory_layout.setStretch(2, 2)
        self.main_layout.addLayout(
            self.project_data_directory_layout)

        self.project_data_email_subject_layout = QtWidgets.QHBoxLayout()

        # Label for email subject line edit
        self.database_email_subject_label = QtWidgets.QLabel()
        self.database_email_subject_label.setObjectName(
            "database_email_subject_label")
        self.project_data_email_subject_layout.addWidget(
            self.database_email_subject_label
        )

        # Project email subject line edit
        self.database_project_email_subject_line_edit = QtWidgets.QLineEdit()
        self.database_project_email_subject_line_edit.setObjectName(
            "database_project_email_subject_line_edit"
        )
        # self.database_project_email_subject_line_edit.editingFinished.connect(
        #     lambda: self.project_data_change_check(
        #         self.database_project_email_subject_line_edit, "email_subject"
        #     )
        # )
        self.project_data_email_subject_layout.addWidget(
            self.database_project_email_subject_line_edit
        )
        self.main_layout.addLayout(
            self.project_data_email_subject_layout
        )

        self.project_data_email_lists_layout = QtWidgets.QHBoxLayout()
        self.project_data_email_to_layout = QtWidgets.QVBoxLayout()

        # Label for email to list widget
        self.database_email_to_label = QtWidgets.QLabel()
        self.database_email_to_label.setObjectName("database_email_to_label")
        self.project_data_email_to_layout.addWidget(
            self.database_email_to_label)

        # Email to list widget
        self.database_email_to_list_widget = email_list_widget.EmailListWidget()
        # Enable dragging and dropping of items within the list widget
        # self.database_email_to_list_widget.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        # Enable editing of items by double-clicking on them
        # self.database_email_to_list_widget.setEditTriggers(QtWidgets.QListWidget.DoubleClicked)
        # self.database_email_to_list_widget.itemClicked.connect(
        #     lambda: self.database_list_widget_add_blank(
        #         self.database_email_to_list_widget
        #     )
        # )
        # self.database_email_to_list_widget.itemChanged.connect(
        #     lambda: self.project_data_change_check(
        #         self.database_email_to_list_widget, "email_to"
        #     )
        # )
        self.project_data_email_to_layout.addWidget(
            self.database_email_to_list_widget)

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_to_layout
        )

        self.project_data_email_cc_layout = QtWidgets.QVBoxLayout()
        # Label for email cc list widget
        self.database_email_cc_label = QtWidgets.QLabel()
        self.database_email_cc_label.setObjectName("database_email_tcc_label")
        self.project_data_email_cc_layout.addWidget(
            self.database_email_cc_label)

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
        # self.database_email_cc_list_widget.itemChanged.connect(
        #     lambda: self.project_data_change_check(
        #         self.database_email_cc_list_widget, "email_cc"
        #     )
        # )
        self.project_data_email_cc_layout.addWidget(
            self.database_email_cc_list_widget)

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_cc_layout
        )

        self.project_data_email_bcc_layout = QtWidgets.QVBoxLayout()
        # Label for email bcc list widget
        self.database_email_bcc_label = QtWidgets.QLabel()
        self.database_email_bcc_label.setObjectName("database_email_bcc_label")
        self.project_data_email_bcc_layout.addWidget(
            self.database_email_bcc_label)

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
        # self.database_email_bcc_list_widget.itemChanged.connect(
        #     lambda: self.project_data_change_check(
        #         self.database_email_bcc_list_widget, "email_bcc"
        #     )
        # )
        self.project_data_email_bcc_layout.addWidget(
            self.database_email_bcc_list_widget
        )

        self.project_data_email_lists_layout.addLayout(
            self.project_data_email_bcc_layout
        )
        self.main_layout.addLayout(
            self.project_data_email_lists_layout)

        self.project_data_bottom_cta_layout = QtWidgets.QHBoxLayout()

        # Action button to save manual changes
        self.database_save_edited_project_data_button = QtWidgets.QPushButton()
        # self.database_save_edited_project_data_button.clicked.connect(
        #     self.project_data_save_new
        # )
        self.database_save_edited_project_data_button.setObjectName(
            "database_save_edited_project_data_button"
        )
        self.database_save_edited_project_data_button.setEnabled(False)
        self.project_data_bottom_cta_layout.addWidget(
            self.database_save_edited_project_data_button
        )

        # Action button to discard manual changes
        self.database_discard_edited_project_data_button = QtWidgets.QPushButton()
        # self.database_discard_edited_project_data_button.clicked.connect(
        #     self.database_populate_project_edit_fields
        # )
        self.database_discard_edited_project_data_button.setObjectName(
            "database_discard_edited_project_data_button"
        )
        self.database_discard_edited_project_data_button.setEnabled(False)
        self.project_data_bottom_cta_layout.addWidget(
            self.database_discard_edited_project_data_button
        )

        # Action button to delete database entry
        self.database_delete_project_data_button = QtWidgets.QPushButton()
        # self.database_delete_project_data_button.clicked.connect(
        #     self.database_delete_project_data
        # )
        self.database_delete_project_data_button.setObjectName(
            "database_delete_project_data_button"
        )
        self.database_delete_project_data_button.setProperty(
            "class", "delete-button")
        self.database_delete_project_data_button.setEnabled(False)
        self.project_data_bottom_cta_layout.addWidget(
            self.database_delete_project_data_button
        )

        self.main_layout.addLayout(
            self.project_data_bottom_cta_layout)

        self.view_model.main_view_model.fetch_all_project_data()

        self.setLayout(self.main_layout)

        self.translate_ui()
        self.view_model.update_data_table()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.database_email_to_label.setText(
            _translate("MainWindow", "Email TO List:"))
        self.database_email_cc_label.setText(
            _translate("MainWindow", "Email CC List:"))
        self.database_email_bcc_label.setText(
            _translate("MainWindow", "Email BCC List:")
        )
        self.database_project_number_label.setText(
            _translate("MainWindow", "Project Number:")
        )
        self.database_directory_label.setText(
            _translate("MainWindow", "Directory:"))
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
        self.project_data_add_new_button.setText(
            _translate("MainWindow", "New Entry"))
        self.delete_all_project_data_button.setText(
            _translate("MainWindow", "Delete ALL Project Data")
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

    def update_data_table(self, project_data: list[str], headers: list[str]):

        if not project_data:
            return

        # self.database_viewer_table.currentItemChanged.disconnect()
        self.database_viewer_table.clear()
        self.display_data_as_table(project_data=project_data, headers=headers)
        # self.database_viewer_table.currentItemChanged.connect(
        #     self.database_populate_project_edit_fields
        # )
        self.database_viewer_table.sortItems(0, QtCore.Qt.AscendingOrder)
        self.update()

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
                    item_text = self.database_viewer_table.item(
                        row, column).text()
                    if search_term.lower() in item_text.lower():
                        # If the search term is found, show the entire row and break out of the column loop
                        self.database_viewer_table.setRowHidden(row, False)
                        # Show all cells in the row
                        for column in range(self.database_viewer_table.columnCount()):
                            self.database_viewer_table.setColumnHidden(
                                column, False)
                        row_count += 1
                        break
                except AttributeError:
                    pass

        # if theres data in filtered results, and a row is chosen, enable the delete button
        # if row_count > 0 and self.project_data_loaded_id is not None:
        #     self.database_delete_project_data_button.setEnabled(True)
