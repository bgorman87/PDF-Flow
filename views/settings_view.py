from PySide6 import QtWidgets, QtCore
from view_models import settings_view_model
from widgets.utility_widgets import HorizontalLine
from functools import partial


class SettingsView(QtWidgets.QWidget):
    def __init__(self, view_model: settings_view_model.SettingsViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setObjectName("settings_stack_item")

        self.template_title = QtWidgets.QLabel()
        self.template_title.setText("Templates")

        self.main_layout.addWidget(self.template_title)

        # create a vertical list where each item has a check box and a label
        self.template_list = QtWidgets.QVBoxLayout()
        self.template_list.setContentsMargins(5, 5, 5, 5)
        self.template_list.setSpacing(5)
        self.template_list.setAlignment(QtCore.Qt.AlignTop)
        self.template_list.setObjectName("template_list")
        
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_widget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.populate_template_profile_list()
        self.scroll_widget.setLayout(self.template_list)
        

        # Set background color using QSs
        self.scroll_widget.setProperty("class", "template-list")
        # Create the QScrollArea and add the widget to it
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the QScrollArea to your main layout
        self.main_layout.addWidget(self.scroll_area)

        self.delete_button_layout = QtWidgets.QHBoxLayout()
        self.delete_template_button = QtWidgets.QPushButton()
        self.delete_template_button.setText("Delete Template")
        self.delete_template_button.setProperty("class", "delete-button")
        self.delete_template_button.setEnabled(False)
        self.delete_template_button.clicked.connect(self.view_model.delete_selected_templates_handler)
        self.delete_button_layout.addWidget(self.delete_template_button)
        self.delete_button_layout.addStretch(1)

        self.main_layout.addLayout(self.delete_button_layout)

        self.main_layout.addSpacing(100)
        self.main_layout.addWidget(HorizontalLine())
        self.main_layout.addWidget(HorizontalLine())
        self.main_layout.addSpacing(10)

        self.config_title = QtWidgets.QLabel()
        self.config_title.setText("Configuration Options")
        self.main_layout.addWidget(self.config_title)

        # Create a vertical list for "anonymous", "test", and "unique id" options
        # anonymous and test are check boxes, while unique id is a text box with a "set" button
        self.config_list = QtWidgets.QVBoxLayout()
        self.config_list.setContentsMargins(5, 5, 5, 5)
        self.config_list.setSpacing(0)
        self.config_list.setAlignment(QtCore.Qt.AlignTop)
        self.config_list.setObjectName("config_list")

        batch_email_layout = QtWidgets.QHBoxLayout()
        self.batch_email_label = QtWidgets.QLabel("Enable batch email: ")
        self.batch_email_label.setContentsMargins(0, 5, 20, 5)
        self.batch_email_checkbox = QtWidgets.QCheckBox()
        self.batch_email_checkbox.setToolTip("Enables batch email functionality.")
        self.batch_email_checkbox.setChecked(self.view_model.get_batch_email_state())
        self.batch_email_checkbox.clicked.connect(self.view_model.toggle_batch_email)
        batch_email_layout.addWidget(self.batch_email_label)
        batch_email_layout.addWidget(self.batch_email_checkbox)

        batch_email_layout.addStretch(1)
        self.config_list.addLayout(batch_email_layout)

        anonymous_layout = QtWidgets.QHBoxLayout()
        self.anonymous_label = QtWidgets.QLabel("Enable anonymous usage statistics:")
        self.anonymous_label.setContentsMargins(0, 5, 20, 5)
        self.anonymous_checkbox = QtWidgets.QCheckBox()
        self.anonymous_checkbox.setToolTip("Removes unique identifier from usage statistics if enabled.")
        self.anonymous_checkbox.setChecked(self.view_model.get_anonymous_state())
        self.anonymous_checkbox.clicked.connect(self.view_model.toggle_anonymous_usage)
        anonymous_layout.addWidget(self.anonymous_label)
        anonymous_layout.addWidget(self.anonymous_checkbox)

        anonymous_layout.addStretch(1)
        self.config_list.addLayout(anonymous_layout)        

        unique_id_layout = QtWidgets.QHBoxLayout()
        unique_id_layout.setContentsMargins(0, 5, 5, 0)
        unique_id_layout.setSpacing(0)
        unique_id_layout.setAlignment(QtCore.Qt.AlignLeft)
        unique_id_layout.setObjectName("unique_id_layout")

        unique_id_label = QtWidgets.QLabel()
        unique_id_label.setText("Unique ID:")
        unique_id_label.setContentsMargins(0, 0, 5, 0)
        unique_id_layout.addWidget(unique_id_label)
        
        self.unique_id_textbox = QtWidgets.QLineEdit()
        self.unique_id_textbox.setText(self.view_model.get_unique_id())
        self.unique_id_textbox.setReadOnly(True)
        unique_id_layout.addWidget(self.unique_id_textbox)
        self.config_list.addLayout(unique_id_layout)
        

        anonymous_clarification_label = QtWidgets.QLabel()
        anonymous_clarification_label.setText("Note: A unique identifier is generated for each user and is used to track usage statistics. This identifier does not contain any personal information.")
        anonymous_clarification_label.setWordWrap(True)
        anonymous_clarification_label.setContentsMargins(0, 2, 5, 0)
        anonymous_clarification_label.setProperty("class", "anonymous-clarification-label")
        self.config_list.addWidget(anonymous_clarification_label)
        self.main_layout.addLayout(self.config_list)

        self.main_layout.addStretch(2)
        
        self.setLayout(self.main_layout)

        self.view_model.anonymous_usage_update.connect(self.update_anonymous_config_options)
        self.view_model.selected_templates_update.connect(self.update_template_deletion_button)
        self.view_model.profile_list_update.connect(
            self.update_profile_list
        )
        self.view_model.batch_email_update.connect(
            self.update_batch_email
        )


    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        
        self.settings_profile_template_label.setText(
            _translate("FileNameView", "Choose Profile:")
        )

    def update_batch_email(self):
        self.batch_email_checkbox.setChecked(self.view_model.get_batch_email_state())

    def update_anonymous_config_options(self, anonymous: bool):
        if anonymous:
            self.unique_id_textbox.setText("")
        else:
            self.unique_id_textbox.setText(self.view_model.get_unique_id())

    def update_template_deletion_button(self, quantity: int):
        
        if quantity == 0:
            self.delete_template_button.setEnabled(False)
            self.delete_template_button.setText("Delete Template")
        else:
            self.delete_template_button.setEnabled(True)
            if quantity == 1:
                button_string = f"Delete (1) Template"
            else:
                button_string = f"Delete ({quantity}) Templates"

            self.delete_template_button.setText(button_string)

    def update_profile_list(self):
        # Clear the list
        for i in reversed(range(self.template_list.count())): 
            self.template_list.itemAt(i).widget().setParent(None)

        self.populate_template_profile_list()

    def populate_template_profile_list(self):
        # Add the new list
        for profile in self.view_model.format_file_profile_list():
            template_checkbox = QtWidgets.QCheckBox()
            template_checkbox.setText(profile)
            template_checkbox.setChecked(False)
            callback = partial(self.view_model.template_item_clicked, checkbox=template_checkbox, profile_line=profile)
            template_checkbox.clicked.connect(callback)
            template_checkbox.setProperty("class", "template-checkbox")
            self.template_list.addWidget(template_checkbox)

        self.template_list.update()
