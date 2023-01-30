from PySide6 import QtCore, QtWidgets
from view_models import main_view_model

class SettingsViewModel(QtCore.QObject):
    template_choice_update = QtCore.Signal()
    file_name_update = QtCore.Signal()
    file_name_example_update = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._active_parameter_data = None
        self._active_parameter_list_items = None
        self._active_paramaters_examples = None
        self._active_file_naming_scheme = ""
        self._process_profile_file_name = ""
        self._process_profile_file_name_cursor_position = 0
        self._settings_profile_naming_scheme_example_text = ""
        self._profile_id = None

    def format_file_profile_dropdown(self) -> list[str]:
        """Transforms profiles into a list with profile name and identifier text. profiles list comes from fetch_file_profiles from data_handler.

        Returns:
            list: Items to display in profiles dropdown
        """
        dropdown_items = []
        results = self.main_view_model.fetch_file_profiles()
        if results:
            dropdown_items = ["".join([s[0], " - ", s[1]])
                            for s in results]
        return dropdown_items
    
    def display_active_parameters(self, file_profile_item) -> None:
        """Fills in active parameters list based off the currently chosen file_profile dropdown item.

        Args:
            file_profile_text (str): file_profile text as format "file_profile - example text"
        """
        file_profile_text = file_profile_item.text()
        if not file_profile_text.split(" - ")[-1]:
            return
        self._profile_id = self.main_view_model.fetch_profile_id(file_profile_text.split(" - ")[0])
        self._active_parameters = self.main_view_model.fetch_active_parameters(self._profile_id)
        self._active_paramaters_examples = []
        self._active_parameter_list_items = []
        for parameter in self._active_parameters:
            self._active_paramaters_examples.append(self.main_view_model.fetch_parameter_example_text(parameter=parameter))
            active_param_list_item = QtWidgets.QListWidgetItem(parameter)
            self._active_parameter_list_items.append(active_param_list_item)
        self._active_file_naming_scheme = self.main_view_model.fetch_profile_file_name_pattern(self._profile_id)
        self.template_choice_update.emit()

    @property
    def active_parameter_items(self):
        return self._active_parameter_list_items
    
    @property
    def active_file_naming_scheme(self):
        return self._active_file_naming_scheme
    
    def add_active_param_line_edit(self, line_edit: QtWidgets.QLineEdit, parameter_name: str):
        """Upon clicking a parameter in the parameter list, {parameter}' gets inserted to the line edit"""
        current_cursor_position = line_edit.cursorPosition()

        parameter = "{" + parameter_name + "}"
        chars = list(line_edit.text())
        chars.insert(current_cursor_position, parameter)
        self._process_profile_file_name = "".join(chars)
        self._process_profile_file_name_cursor_position = current_cursor_position + len(parameter)
        self.file_name_update.emit()

    @property
    def process_profile_file_name(self):
        return self._process_profile_file_name
    
    @property
    def process_profile_file_name_cursor_position(self):
        return self._process_profile_file_name_cursor_position
    
    def display_example_file_name(self, line_edit_text: str) -> None:
        """When file name line edit is changed, replace any instance of '{parameter}' with an example string from that parameter and replace the example line edit with that text."""
        replace_result = line_edit_text
        if r"{doc_num}" in replace_result[len(r"{doc_num}") :]:
            replace_result = replace_result.replace(r"{doc_num}", "")
            replace_result = r"{doc_num}" + replace_result
            self._process_profile_file_name = replace_result
            self._process_profile_file_name_cursor_position = 0
            self.file_name_update.emit()
        for param_name, example in zip(self._active_parameter_items, self._active_paramaters_examples):
            replace_result = replace_result.replace(
                "".join(["{", param_name, "}"]), example
            )
        self._settings_profile_naming_scheme_example_text = replace_result
        self.file_name_example_update.emit()

    @property
    def settings_profile_naming_scheme_example_text(self):
        return self._settings_profile_naming_scheme_example_text
    
    def check_profile_file_name_pattern(self, list_widget_text:str) -> None:
        profile_name = list_widget_text.split(" - ")[0]
        current_profile_file_name = self.main_view_model.fetch_profile_file_name_pattern(profile_name)

        # Check current profile file nameing scheme to see if one exists
        # Ask user if they want to overwrite if so then call update function
        if current_profile_file_name is not None:
            message_box_window_title = "Filename Pattern Already Found"
            severity_icon = QtWidgets.QMessageBox.Warning
            text_body = f"Unique identifier already in database \
                    \n \
                    \n{current_profile_file_name} \
                    \n "
            buttons = [QtWidgets.QPushButton("Overwrite"), QtWidgets.QPushButton("Cancel")]
            button_roles = [QtWidgets.QMessageBox.YesRole, QtWidgets.QMessageBox.RejectRole]
            callback = lambda: self.apply_file_name_pattern(profile_name)
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }
            
            self.main_view_model.message_box_alert.emit(message_box_dict)
        else:
            self.apply_file_name_pattern(profile_name)

    def apply_file_name_pattern(self, profile_name: str) -> None:
        """Handles the saving of a file profile's file naming pattern to the database"""

        self.main_view_model.update_profile_file_name_pattern(profile_name, self._process_profile_file_name)