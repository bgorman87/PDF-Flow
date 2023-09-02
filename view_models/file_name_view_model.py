from PySide6 import QtCore, QtWidgets

from view_models import main_view_model


class FileNameViewModel(QtCore.QObject):
    file_name_update = QtCore.Signal()
    file_name_example_update = QtCore.Signal()
    parameter_update_list = QtCore.Signal()

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
        self._active_parameters = None

    def format_file_profile_list(self) -> list[str]:
        """Transforms profiles into a list with profile name and identifier text. profiles list comes from fetch_file_profiles from data_handler.

        Returns:
            list: Items to display in profiles dropdown
        """
        dropdown_items = []
        results = self.main_view_model.fetch_file_profiles_for_settings()
        if results:
            dropdown_items = ["".join([result[0], " - ", result[1]])
                              for result in results]
        return dropdown_items

    def display_active_parameters_from_item(self, file_profile_item) -> None:
        """Fills in active parameters list based off the currently chosen file_profile dropdown item.

        Args:
            file_profile_text (str): file_profile text as format "file_profile - example text"
        """
        file_profile_text = file_profile_item.text()
        if not file_profile_text.split(" - ")[-1]:
            return
        self._profile_id = self.main_view_model.fetch_profile_id_by_profile_name(
            file_profile_text.split(" - ")[0])
        self._active_parameters = self.main_view_model.fetch_active_parameters_by_profile_id(
            self._profile_id)
        self._active_paramaters_examples = ["01"]
        self._active_parameter_list_items = []
        active_param_list_item = QtWidgets.QListWidgetItem("doc_num")
        self._active_parameter_list_items.append(active_param_list_item)
        for parameter in self._active_parameters[1:]:
            self._active_paramaters_examples.append(
                self.main_view_model.fetch_parameter_example_text_by_name_and_profile_id(profile_id=self._profile_id, parameter=parameter))
            active_param_list_item = QtWidgets.QListWidgetItem(parameter)
            self._active_parameter_list_items.append(active_param_list_item)
        self._active_file_naming_scheme = self.main_view_model.fetch_profile_file_name_pattern_by_profile_id(
            self._profile_id)
        self.main_view_model.parameter_update_list.emit()

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
        self._process_profile_file_name_cursor_position = current_cursor_position + \
            len(parameter)
        self.file_name_update.emit()

    @property
    def process_profile_file_name(self):
        return self._process_profile_file_name

    @property
    def process_profile_file_name_cursor_position(self):
        return self._process_profile_file_name_cursor_position

    def display_file_name(self, line_edit_text: str) -> None:
        """When file name line edit is changed, replace any instance of '{parameter}' with an example string from that parameter and replace the example line edit with that text."""
        replace_result = line_edit_text
        self._process_profile_file_name = replace_result
        if r"{doc_num}" in replace_result[len(r"{doc_num}"):]:
            replace_result = replace_result.replace(r"{doc_num}", "")
            replace_result = r"{doc_num}" + replace_result
            self._process_profile_file_name = replace_result
            self._process_profile_file_name_cursor_position = 0
            self.file_name_update.emit()
        else:
            self.display_example_file_name(line_edit_text=line_edit_text)

    def display_example_file_name(self, line_edit_text: str) -> None:
        replace_result = line_edit_text
        for param_name, example in zip(self._active_parameters, self._active_paramaters_examples):
            replace_result = replace_result.replace(
                "".join(["{", param_name, "}"]), example
            )
        self._settings_profile_naming_scheme_example_text = replace_result
        self.file_name_example_update.emit()

    @property
    def settings_profile_naming_scheme_example_text(self):
        return self._settings_profile_naming_scheme_example_text

    def check_profile_file_name_pattern(self, list_widget_text: str) -> None:
        profile_name = list_widget_text.split(" - ")[0]
        profile_id = self.main_view_model.fetch_profile_id_by_profile_name(profile_name=profile_name)
        current_profile_file_name = self.main_view_model.fetch_profile_file_name_pattern_by_profile_id(
            profile_id=profile_id)

        # Check current profile file nameing scheme to see if one exists
        # Ask user if they want to overwrite if so then call update function
        if current_profile_file_name:
            message_box_window_title = "File Name Pattern Already Found"
            severity_icon = QtWidgets.QMessageBox.Warning
            text_body = f"Overwrite current pattern?\
                    \n \
                    \n{current_profile_file_name} \
                    \n "
            buttons = [
                "Overwrite", "Cancel"]
            button_roles = [QtWidgets.QMessageBox.YesRole,
                            QtWidgets.QMessageBox.RejectRole,]
            callback = [lambda: self.apply_file_name_pattern(
                profile_name=profile_name), None]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }

            self.main_view_model.display_message_box(message_box_dict=message_box_dict)
        else:
            self.apply_file_name_pattern(profile_name=profile_name)

    def apply_file_name_pattern(self, profile_name: str) -> None:
        """Handles the saving of a file profile's file naming pattern to the database"""

        self.main_view_model.update_template_profile_file_name_pattern(
            profile_name=profile_name, profile_file_name_pattern=self._process_profile_file_name)
        self.main_view_model.add_console_text(new_text=f"Updated file name pattern for profile '{profile_name}' to: {self._process_profile_file_name}")
        self.main_view_model.add_console_alerts(alerts=1)