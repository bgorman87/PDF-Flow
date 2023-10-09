from PySide6 import QtCore, QtWidgets

from view_models import template_view_model
from widgets import file_template_creation, utility_widgets


class TemplateView(QtWidgets.QWidget):
    def __init__(self, view_model: template_view_model.TemplateViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()

        self.file_template_tab_cta_button_layout = QtWidgets.QHBoxLayout()

        # Button to load template file
        self.select_template_file = QtWidgets.QPushButton()
        self.select_template_file.setObjectName("select_template_file")
        self.select_template_file.clicked.connect(
            self.view_model.file_profile_template_dialog)
        self.select_template_file_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(
            self.select_template_file)

        

        # Button to apply selection as co-ords for unique file identifier
        self.apply_unique_file_identifier_button = QtWidgets.QPushButton()
        self.apply_unique_file_identifier_button.setObjectName(
            "apply_unique_file_identifier_button"
        )
        self.apply_unique_file_identifier_button.clicked.connect(
            lambda: self.view_model.apply_template_property(
                property_type="profile", template_display=self.template_display)
        )
        self.apply_unique_file_identifier_button.setEnabled(False)
        self.view_model.unique_file_identifier_button_status.connect(
            lambda: self.apply_unique_file_identifier_button.setEnabled(self.view_model.unique_file_id_button_enabled))
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
            lambda: self.view_model.apply_template_property(
                property_type="project_number", template_display=self.template_display)
        )
        self.apply_unique_profile_project_number_button.setEnabled(False)
        self.view_model.project_number_status_update.connect(
            lambda: self.apply_unique_profile_project_number_button.setEnabled(self.view_model.project_button_enabled))
        self.apply_unique_profile_project_number_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(
            self.apply_unique_profile_project_number_button
        )

        # Button to apply selection as coords for unique data information
        self.apply_unique_profile_parameter_button = QtWidgets.QPushButton()
        self.apply_unique_profile_parameter_button.setObjectName(
            "apply_unique_profile_parameter_button"
        )
        self.apply_unique_profile_parameter_button.clicked.connect(
            lambda: self.view_model.apply_template_property(
                property_type="parameter", template_display=self.template_display)
        )
        self.apply_unique_profile_parameter_button.setEnabled(False)
        self.view_model.unique_parameter_status_update.connect(
            lambda: self.apply_unique_profile_parameter_button.setEnabled(self.view_model.parameter_button_enabled))
        self.apply_unique_profile_parameter_dialog = QtWidgets.QFileDialog()
        self.file_template_tab_cta_button_layout.addWidget(
            self.apply_unique_profile_parameter_button
        )

        self.main_layout.addLayout(
            self.file_template_tab_cta_button_layout
        )

        # Line below action buttons
        self.file_template_tab_line_below_cta_layout = utility_widgets.HorizontalLine()

        self.main_layout.addWidget(
            self.file_template_tab_line_below_cta_layout
        )

        self.loaded_template_name_layout = QtWidgets.QHBoxLayout()
        # Label for profile name
        self.file_template_profile_name_label = QtWidgets.QLabel()
        self.loaded_template_name_layout.addWidget(
            self.file_template_profile_name_label
        )
        self.file_template_profile_name_input = QtWidgets.QLabel()
        self.view_model.loaded_profile_label_update.connect(self.new_loaded_profile)
        self.file_template_profile_name_input.setEnabled(False)

        self.loaded_template_name_layout.addWidget(
            self.file_template_profile_name_input
        )
        self.loaded_template_name_layout.setStretch(
            self.loaded_template_name_layout.indexOf(self.file_template_profile_name_input), 4
        )

        self.file_template_profile_name_rename_button = QtWidgets.QPushButton()
        self.file_template_profile_name_rename_button.clicked.connect(
            self.view_model.handle_template_profile_rename)
        self.file_template_profile_name_rename_button.setEnabled(False)
        self.loaded_template_name_layout.addWidget(
            self.file_template_profile_name_rename_button
        )
        self.loaded_template_name_layout.setStretch(
            self.loaded_template_name_layout.indexOf(self.file_template_profile_name_rename_button), 1
        )
        self.file_template_delete_profile_button = QtWidgets.QPushButton()
        self.file_template_delete_profile_button.clicked.connect(
            self.view_model.handle_template_profile_deletion
        )
        self.file_template_delete_profile_button.setProperty("class", "delete-button")
        self.file_template_delete_profile_button.setEnabled(False)
        self.loaded_template_name_layout.addWidget(
            self.file_template_delete_profile_button
        )
        self.loaded_template_name_layout.setStretch(
            self.loaded_template_name_layout.indexOf(self.file_template_delete_profile_button), 1
        )
        self.main_layout.addLayout(
            self.loaded_template_name_layout
        )

        # Line below action buttons
        self.file_template_tab_line_below_profile_name_layout = utility_widgets.HorizontalLine()

        self.main_layout.addWidget(
            self.file_template_tab_line_below_profile_name_layout
        )


        # Custom template display widget
        self.template_display = file_template_creation.TemplateWidget()
        self.main_layout.addWidget(self.template_display)
        self.view_model.template_pixmap_update.connect(lambda: self.update_template_pixmap(
            img_byte_arr=self.view_model.img_byte_array,
            image=self.view_model.pil_image
        ))
        self.view_model.rects_found.connect(lambda: self.paint_existing_data_rects(
            parameter_rects=self.view_model.parameter_rects,
            profile_rect=self.view_model.profile_rect
        ))
        self.setLayout(self.main_layout)

        self.translate_ui()

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.select_template_file.setText(
            _translate("TemplateView", "Open Template File"))
        self.apply_unique_file_identifier_button.setText(_translate(
            "TemplateView", "Set Unique Profile Identifier"))
        self.apply_unique_profile_project_number_button.setText(
            _translate("TemplateView", "Set Project Number"))
        self.apply_unique_profile_parameter_button.setText(
            _translate("TemplateView", "Add Data Parameter"))
        self.file_template_profile_name_label.setText(
            _translate("TemplateView", "Loaded Template:"))
        self.file_template_profile_name_rename_button.setText(
            _translate("TemplateView", "Rename"))
        self.file_template_delete_profile_button.setText(
            _translate("TemplateView", "Delete"))

    def update_template_pixmap(self, img_byte_arr, image):
        self.template_display.deleteLater()
        self.template_display = file_template_creation.TemplateWidget(
            img_byte_arr, image)
        self.main_layout.addWidget(self.template_display)
        self.template_display.style().polish(self.template_display)

    def paint_existing_data_rects(self, parameter_rects: list[str], profile_rect: list[str]):
        self.template_display.set_data_info(parameter_rects, profile_rect)
        self.template_display.style().polish(self.template_display)

    def new_loaded_profile(self) -> None:
        """Updates the loaded profile name in the view, and sets enabled state of rename/delete buttons accordingly."""

        self.file_template_profile_name_input.setText(self.view_model.loaded_profile_label_text)

        if self.view_model.loaded_profile_label_text == "": 
            self.file_template_delete_profile_button.setEnabled(False)
            self.file_template_profile_name_rename_button.setEnabled(False)
            return
        
        self.file_template_delete_profile_button.setEnabled(True)
        self.file_template_profile_name_rename_button.setEnabled(True)
        return