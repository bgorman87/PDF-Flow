from PySide6 import QtWidgets, QtCore
from view_models import settings_view_model
from widgets import utility_widgets, email_widget


class SettingsView(QtWidgets.QWidget):
    def __init__(self, view_model: settings_view_model.SettingsViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setObjectName("settings_stack_item")

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
            self.view_model.format_file_profile_dropdown()
        )
        self.settings_profile_templates_list_widget.itemClicked.connect(
            self.view_model.display_active_parameters
        )
        self.view_model.template_choice_update.connect(
            lambda: self.update_parameter_list(
                paramater_items=self.view_model.active_parameter_items,
                file_naming_scheme=self.view_model.active_file_naming_scheme,
            )
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
            lambda: self.view_model.add_active_param_line_edit(self.settings_profile_naming_scheme_line_edit, self.settings_profile_parameters_list_widget.currentItem().text())
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
            self.view_model.display_example_file_name
        )
        self.view_model.file_name_example_update.connect(lambda: self.update_file_name_example_line_edit(self.view_model.settings_profile_naming_scheme_example_text))
        self.settings_file_name_pattern_layout.addWidget(
            self.settings_profile_naming_scheme_line_edit
        )

        # Button to sanem file naming scheme to database
        self.settings_profile_naming_scheme_button = QtWidgets.QPushButton()
        self.settings_profile_naming_scheme_button.setObjectName(
            "settings_profile_naming_scheme_button"
        )
        self.settings_profile_naming_scheme_button.clicked.connect(
            lambda: self.view_model.check_profile_file_name_pattern(self.settings_profile_templates_list_widget.currentItem().text())
        )
        self.settings_file_name_pattern_layout.addWidget(
            self.settings_profile_naming_scheme_button
        )

        self.main_layout.addLayout(self.settings_file_name_pattern_layout)

        # Label for file rename example output
        self.settings_profile_naming_scheme_example_label = QtWidgets.QLabel()
        self.settings_profile_naming_scheme_example_label.setObjectName(
            "settings_profile_naming_scheme_example_label"
        )
        self.main_layout.addWidget(self.settings_profile_naming_scheme_example_label)

        # Line edit to display an example of data shown
        self.settings_profile_naming_scheme_example_line_edit = QtWidgets.QLineEdit()
        self.settings_profile_naming_scheme_example_line_edit.setEnabled(False)
        self.settings_profile_naming_scheme_example_line_edit.setObjectName(
            "settings_profile_naming_scheme_example_line_edit"
        )
        self.main_layout.addWidget(
            self.settings_profile_naming_scheme_example_line_edit
        )

        # signature text edit
        self.settings_email_text_edit = email_widget.EmailWidget()
        self.settings_email_text_edit.setObjectName("settings_email_text_edit")
        self.main_layout.addWidget(self.settings_email_text_edit)
        self.main_layout.setStretch(
            self.main_layout.indexOf(self.settings_email_text_edit), 1
        )
        self.setLayout(self.main_layout)
        self.translate_ui()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.settings_profile_naming_scheme_label.setText(
            _translate("SettingsView", "File Name Template:")
        )
        self.settings_profile_naming_scheme_example_label.setText(
            _translate("SettingsView", "File Name Preview:")
        )
        self.settings_profile_parameters_label.setText(
            _translate("SettingsView", "Available Profile Parameters:")
        )
        self.settings_profile_template_label.setText(
            _translate("SettingsView", "Choose Profile:")
        )
        self.settings_profile_naming_scheme_button.setText(
            _translate("SettingsView", "Save Filename Pattern")
        )

    def update_parameter_list(
        self, paramater_items: list[QtWidgets.QListWidgetItem], file_naming_scheme: str
    ) -> None:
        self.settings_profile_parameters_list_widget.clear()
        self.settings_profile_naming_scheme_line_edit.clear()

        self.settings_profile_naming_scheme_line_edit.setText(file_naming_scheme)
        for param_list_item in paramater_items:
            self.settings_profile_parameters_list_widget.addItem(param_list_item)

    def update_file_name_line_edit(self, new_text: str, cursor_position: int) -> None:
        self.settings_profile_naming_scheme_line_edit.setText(new_text)
        self.settings_profile_naming_scheme_line_edit.setFocus()
        self.settings_profile_naming_scheme_line_edit.setCursorPosition(cursor_position)

    def update_file_name_example_line_edit(self, new_example_text: str) -> None:
        self.settings_profile_naming_scheme_example_line_edit.setText(new_example_text)

