from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from widgets import email_widget
from view_models import email_view_model


class EmailView(QWidget):
    def __init__(self, view_model: email_view_model.EmailViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QVBoxLayout()
        self.setObjectName("email_stack_item")

        self.email_profile_layout = QHBoxLayout()
        # Label for dropdown menu
        self.email_profile_label = QLabel()
        self.email_profile_label.setObjectName(
            "email_profile_label"
        )
        self.email_profile_layout.addWidget(self.email_profile_label)

        # Dropdown menu containing e-mail profiles
        self.email_profile_combo_box = QComboBox()
        self.email_profile_combo_box.setObjectName(
            "email_profile_combo_box"
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
            self.email_profile_layout.indexOf(self.email_profile_combo_box), 6
        )

        self.email_profile_delete_button = QPushButton()
        self.email_profile_delete_button.setObjectName(
            "email_profile_delete_button"
        )
        self.email_profile_layout.addWidget(
            self.email_profile_delete_button
        )
        self.email_profile_layout.setStretch(
            self.email_profile_layout.indexOf(self.email_profile_delete_button), 1
        )
        self.email_profile_delete_button.setProperty("class", "delete-button")
        self.email_profile_delete_button.clicked.connect(
            self.view_model.delete_email_profile_dialog
        )
        self.email_profile_delete_button.setEnabled(False)
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
        self.save_button = QPushButton()
        self.save_button.setObjectName("save_button")
        self.save_button.clicked.connect(self.save_email)
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

        self.view_model.email_list_update.connect(
            self.load_email_options
        )

        self.view_model.set_current_index_signal.connect(
            self.email_profile_combo_box.setCurrentIndex
        )

        self.setLayout(self.main_layout)
        self.translate_ui()
        self.load_email_options()

    def translate_ui(self):
        _translate = QCoreApplication.translate
        self.email_profile_label.setText(
            _translate("EmailView", "Loaded Email:")
        )
        self.save_button.setText(_translate("EmailView", "Save"))
        self.email_profile_delete_button.setText(
            _translate("EmailView", "Delete")
        )

    def load_email_options(self):
        self.email_profile_combo_box.currentIndexChanged.disconnect()
        self.email_profile_combo_box.clear()
        
        items = self.view_model.get_email_profiles()
        self.email_profile_combo_box.addItems(
            items
        )
        self.email_profile_combo_box.currentIndexChanged.connect(
            self.email_profile_changed
        )

        self.email_profile_combo_box.setCurrentIndex(
            self.view_model.get_current_index()
        )
        # self.email_profile_combo_box.setCurrentText(
        #     self.view_model.get_current_profile_name()
        # )

    def save_email(self):
        self.view_model.save_email()
        
    def email_profile_changed(self, index: int):
        self.view_model.email_profile_changed(index)
        if " - Outlook" in self.view_model._email_profile_names[index]:
            self.save_button.setEnabled(False)
            self.email_profile_delete_button.setEnabled(False)
            self.email_text_edit.setEnabled(False)
        else:
            self.save_button.setEnabled(self.view_model.get_text_changed())
            self.email_profile_delete_button.setEnabled(self.view_model.get_current_index() != 0)
            self.email_text_edit.setEnabled(True)
    
    def email_text_changed(self):
        raw_html = self.email_text_edit.get_html()
        plain_text = self.email_text_edit.get_plain_text()
        self.view_model.email_text_changed(raw_html, plain_text)
        if " - Outlook" in self.view_model._email_profile_names[self.view_model._loaded_email_index]:
            self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(self.view_model.get_text_changed())

    def update_email_text(self):
        self.email_text_edit.set_html(self.view_model.formatted_html)
        self.view_model.set_loaded_raw_html(self.email_text_edit.get_html())
        self.save_button.setEnabled(False)