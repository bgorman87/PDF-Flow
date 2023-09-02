from PySide6 import QtWidgets, QtCore
from widgets import email_widget
from view_models import email_view_model

class EmailView(QtWidgets.QWidget):
    def __init__(self, view_model: email_view_model.EmailViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setObjectName("email_stack_item")
        self.loaded_email_index = 0

        self.email_profile_layout = QtWidgets.QHBoxLayout()
        # Label for dropdown menu
        self.email_profile_label = QtWidgets.QLabel()
        self.email_profile_label.setObjectName(
            "settings_email_profile_label"
        )
        self.email_profile_layout.addWidget(self.email_profile_label)

        # Dropdown menu containing e-mail profiles
        self.email_profile_combo_box = QtWidgets.QComboBox()
        self.email_profile_combo_box.setObjectName(
            "settings_email_profile_combo_box"
        )
        self.email_profile_combo_box.currentIndexChanged.connect(
            self.email_profile_changed
        )

        self.email_profile_layout.addWidget(self.email_profile_combo_box)
        # Make combo box directly next to label and stretch to fill
        # self.database_search_layout.setStretch(
        #     self.database_search_layout.indexOf(self.database_search_bar), 1
        # )
        self.email_profile_layout.setStretch(
            self.email_profile_layout.indexOf(self.email_profile_combo_box), 1
        )
        self.main_layout.addLayout(self.email_profile_layout)

        self.email_text_edit = email_widget.EmailWidget()
        self.email_text_edit.setObjectName("email_text_edit")
        self.main_layout.addWidget(self.email_text_edit)
        self.main_layout.setStretch(
            self.main_layout.indexOf(self.email_text_edit), 1
        )
        self.email_text_edit.text_changed.connect(
            self.email_text_changed
        )

        # Add a save button positioned to the right, below the email text edit
        self.save_button = QtWidgets.QPushButton()
        self.save_button.setObjectName("save_button")
        self.save_button.clicked.connect(self.view_model.save_email)
        self.main_layout.addWidget(self.save_button)
        self.main_layout.setStretch(
            self.main_layout.indexOf(self.save_button), 0
        )
        self.save_button.setEnabled(False)
        
        self.view_model.email_text_update.connect(
            self.update_email_text
        )

        self.view_model.clear_email_text.connect(
            self.email_text_edit.clear
        )

        self.setLayout(self.main_layout)
        self.translate_ui()
        self.load_email_options()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.email_profile_label.setText(
            _translate("EmailView", "Loaded Email:")
        )
        self.save_button.setText(_translate("EmailView", "Save"))

    def load_email_options(self):
        items = self.view_model.get_email_profiles()
        self.email_profile_combo_box.addItems(
            items
        )
    
    def email_profile_changed(self, index: int):
        self.email_text_edit.text_changed.disconnect()
        self.view_model.email_profile_changed(index, self.loaded_email_index)
        self.email_text_edit.text_changed.connect(
            self.email_text_changed
        )
        self.update_loaded_email_index(index)
    
    def email_text_changed(self):
        text = self.email_text_edit.get_html()
        # If no loaded profile, then send True to indicate that text has changed
        # or False to indicate text is empty
        if self.loaded_email_index == 0:
            self.view_model.email_text_changed(bool(text))
            self.save_button.setEnabled(bool(text))
        else:
        # If loaded profile, then send True to indicate that text has changed
        # this also accounts for if a user completely empties the text box
            self.view_model.email_text_changed(True)
            self.save_button.setEnabled(True)


    def update_loaded_email_index(self, index: int):
        self.loaded_email_index = index
        self.save_button.setEnabled(False)

    def update_email_text(self):
        self.email_text_edit.set_html(self.view_model.email_raw_html)
        self.save_button.setEnabled(False)