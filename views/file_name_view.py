from PySide6 import QtWidgets, QtCore, QtGui
from view_models import file_name_view_model
from widgets import utility_widgets
from utils import general_utils, path_utils


class FileNameView(QtWidgets.QWidget):
    def __init__(self, view_model: file_name_view_model.FileNameViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setObjectName("file_name_stack_item")

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

        self.main_layout.addLayout(self.settings_profile_choices_label_layout)

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
            self.view_model.format_file_profile_list()
        )
        self.settings_profile_templates_list_widget.itemClicked.connect(
            self.profile_clicked
        )
        self.view_model.profile_list_update.connect(
            self.update_profile_list
        )
        self.settings_profile_choices_layout.addWidget(
            self.settings_profile_templates_list_widget
        )

        # List widget to display active parameters
        self.settings_profile_parameters_list_widget = QtWidgets.QListWidget()
        self.settings_profile_parameters_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )

        self.view_model.main_view_model.parameter_update_list.connect(
            lambda: self.update_parameter_list(
                parameter_items=self.view_model.active_parameter_items,
                file_naming_scheme=self.view_model.active_file_naming_scheme,
            )
        )
        self.settings_profile_parameters_list_widget.setObjectName(
            "settings_profile_parameters_list_widget"
        )
        self.settings_profile_parameters_list_widget.itemClicked.connect(
            lambda: self.view_model.add_active_param_line_edit(
                self.settings_profile_naming_scheme_line_edit, self.settings_profile_parameters_list_widget.currentItem().text())
        )
        self.view_model.file_name_update.connect(
            lambda: self.update_file_name_line_edit(
                new_text=self.view_model.process_profile_file_name,
                cursor_position=self.view_model.process_profile_file_name_cursor_position,
            )
        )
        self.settings_profile_choices_layout.addWidget(
            self.settings_profile_parameters_list_widget
        )

        self.main_layout.addLayout(self.settings_profile_choices_layout)

        # Label for file rename parameter input
        self.settings_profile_naming_scheme_label = QtWidgets.QLabel()
        self.settings_profile_naming_scheme_label.setObjectName(
            "settings_profile_naming_scheme_label"
        )
        self.main_layout.addWidget(self.settings_profile_naming_scheme_label)

        self.settings_file_name_pattern_layout = QtWidgets.QHBoxLayout()
        # Line edit for user to type in format with parameters
        self.settings_profile_naming_scheme_line_edit = QtWidgets.QLineEdit()
        self.settings_profile_naming_scheme_line_edit.setObjectName(
            "settings_profile_naming_scheme_line_edit"
        )
        self.settings_profile_naming_scheme_line_edit.textChanged.connect(
            self.view_model.display_file_name
        )
        self.view_model.file_name_example_update.connect(lambda: self.update_file_name_example_line_edit(
            self.view_model.settings_profile_naming_scheme_example_text))
        self.settings_file_name_pattern_layout.addWidget(
            self.settings_profile_naming_scheme_line_edit
        )

        self.main_layout.addLayout(self.settings_file_name_pattern_layout)
        self.file_name_preview_layout = QtWidgets.QHBoxLayout()
        # # Label for file rename example output
        # self.settings_profile_naming_scheme_example_label = QtWidgets.QLabel()
        # self.settings_profile_naming_scheme_example_label.setObjectName(
        #     "settings_profile_naming_scheme_example_label"
        # )
        # self.file_name_preview_layout.addWidget(
        #     self.settings_profile_naming_scheme_example_label)

        # Line edit to display an example of data shown

        self.settings_profile_naming_scheme_example_helper = QtWidgets.QPushButton()
        self.settings_profile_naming_scheme_example_helper.setMaximumSize(QtCore.QSize(22, 22))
        icon = QtGui.QIcon()
        icon.addFile(path_utils.resource_path(u"assets/icons/tooltip.svg"), QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.settings_profile_naming_scheme_example_helper.setIcon(icon)
        self.settings_profile_naming_scheme_example_helper.setProperty("class", "invert-icon")
        self.settings_profile_naming_scheme_example_helper.setIconSize(QtCore.QSize(12, 12))

        self.settings_profile_naming_scheme_example_helper.setObjectName(
            "settings_profile_naming_scheme_example_helper"
        )
        self.settings_profile_naming_scheme_example_helper.setToolTip(
            "Tip: Project specific email template will take precedence over profile email template."
        )
        self.settings_profile_naming_scheme_example_helper.clicked.connect(
            self.display_tooltip
        )
        self.file_name_preview_layout.addWidget(self.settings_profile_naming_scheme_example_helper)

        self.settings_profile_naming_scheme_example_line_edit = QtWidgets.QLineEdit()
        self.settings_profile_naming_scheme_example_line_edit.setReadOnly(True)
        self.settings_profile_naming_scheme_example_line_edit.setEnabled(False)

        self.settings_profile_naming_scheme_example_line_edit.setObjectName(
            "settings_profile_naming_scheme_example_line_edit"
        )
        self.settings_profile_naming_scheme_example_line_edit.setProperty(
            "class", "line-edit-disabled small"
        )
        self.file_name_preview_layout.addWidget(
            self.settings_profile_naming_scheme_example_line_edit
        )
        
        self.main_layout.addLayout(
            self.file_name_preview_layout
        )

        self.profile_email_layout = QtWidgets.QHBoxLayout()
        # Label for dropdown menu
        self.profile_email_label = QtWidgets.QLabel()
        self.profile_email_label.setObjectName(
            "profile_email_label"
        )
        self.main_layout.addWidget(self.profile_email_label)

        # Dropdown menu containing e-mail profiles
        self.profile_email_combo_box = QtWidgets.QComboBox()
        self.profile_email_combo_box.setObjectName(
            "profile_email_combo_box"
        )
        self.profile_email_combo_box.currentIndexChanged.connect(
            self.update_email_combo_box_state
        )
        self.profile_email_combo_box.setEnabled(False)
        self.profile_email_layout.addWidget(self.profile_email_combo_box)

        self.profile_email_layout.setStretch(
            self.profile_email_layout.indexOf(self.profile_email_combo_box), 6
        )
        self.main_layout.addLayout(self.profile_email_layout)

        self.line = utility_widgets.HorizontalLine()
        self.main_layout.addWidget(self.line)

        # Button to save profile file/email data to database
        self.settings_profile_naming_scheme_button = QtWidgets.QPushButton()
        self.settings_profile_naming_scheme_button.setObjectName(
            "settings_profile_naming_scheme_button"
        )
        self.settings_profile_naming_scheme_button.clicked.connect(
            self.save_profile_data
        )
        self.main_layout.addWidget(
            self.settings_profile_naming_scheme_button
        )

        self.view_model.email_profile_name_update.connect(
            self.set_current_email_index_from_name
        )
        self.view_model.email_profile_list_update.connect(
            self.handle_email_profile_list_update
        )
        
        self.setLayout(self.main_layout)
        self.translate_ui()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.settings_profile_naming_scheme_label.setText(
            _translate("FileNameView", "File Name Template:")
        )
        # self.settings_profile_naming_scheme_example_label.setText(
        #     _translate("FileNameView", "Example:")
        # )
        self.settings_profile_parameters_label.setText(
            _translate("FileNameView", "Available Profile Parameters:")
        )
        self.settings_profile_template_label.setText(
            _translate("FileNameView", "Choose Profile:")
        )
        self.settings_profile_naming_scheme_button.setText(
            _translate("FileNameView", "Save Profile File Name and Email")
        )
        self.profile_email_label.setText(
            _translate("FileNameView", "File Email Profile:")
        )

    def save_profile_data(self):
        self.view_model.check_profile_file_name_pattern(
            self.settings_profile_templates_list_widget.currentItem().text(),
            self.profile_email_combo_box.currentText()
        )

    def profile_clicked(self, item: QtWidgets.QListWidgetItem):
        self.view_model.display_active_parameters_from_item(item)
        self.update_email_combo_box_state()

    def update_profile_list(self):
        self.settings_profile_templates_list_widget.clear()
        self.settings_profile_templates_list_widget.addItems(
            self.view_model.format_file_profile_list()
        )

    def update_parameter_list(
        self, parameter_items: list[QtWidgets.QListWidgetItem], file_naming_scheme: str
    ) -> None:
        self.settings_profile_parameters_list_widget.clear()
        self.settings_profile_naming_scheme_line_edit.clear()

        self.settings_profile_naming_scheme_line_edit.setText(
            file_naming_scheme)
        for param_list_item in parameter_items:
            self.settings_profile_parameters_list_widget.addItem(
                param_list_item)

    def update_file_name_line_edit(self, new_text: str, cursor_position: int) -> None:
        self.settings_profile_naming_scheme_line_edit.setText(new_text)
        self.settings_profile_naming_scheme_line_edit.setFocus()
        self.settings_profile_naming_scheme_line_edit.setCursorPosition(
            cursor_position)

    def update_file_name_example_line_edit(self, new_example_text: str) -> None:
        self.settings_profile_naming_scheme_example_line_edit.setText(
            new_example_text)

        
    def save_email(self):
        self.view_model.set_email_profile(
            self.profile_email_combo_box.currentText()
        )

    def display_tooltip(self):
        text = ("This example line provides a general preview of how the file name will appear for a specific template after processing, and does not reflect the data of any currently loaded file. "
        "Specific parameters like {date} or {project_description} will be replaced with actual data during file processing.")

        self.view_model.display_tooltip(text=text)

    def set_current_email_index_from_name(self, email_profile_name: str) -> None:
        index = self.profile_email_combo_box.findText(email_profile_name)
        if index > 0:
            self.profile_email_combo_box.setCurrentIndex(index)
        else:
            self.profile_email_combo_box.setCurrentIndex(0)

    def update_email_combo_box_state(self) -> None:
        if self.view_model.profile_id and self.profile_email_combo_box.count() > 1:
            self.profile_email_combo_box.setEnabled(True)
        else:
            self.profile_email_combo_box.setEnabled(False)

    def handle_email_profile_list_update(self):
        email_list = self.view_model.email_profile_list
        current_email_name = self.profile_email_combo_box.currentText()
        self.profile_email_combo_box.currentIndexChanged.disconnect()
        self.profile_email_combo_box.clear()
        self.profile_email_combo_box.addItems(email_list)
        self.profile_email_combo_box.setCurrentIndex(
            self.profile_email_combo_box.findText(current_email_name)
        )
        self.profile_email_combo_box.currentIndexChanged.connect(
            self.update_email_combo_box_state
        )
