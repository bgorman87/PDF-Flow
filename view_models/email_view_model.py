from PySide6 import QtCore, QtWidgets
import os

from view_models import main_view_model


class EmailViewModel(QtCore.QObject):
    email_profiles_updated = QtCore.Signal(list)
    email_text_update = QtCore.Signal()
    clear_email_text = QtCore.Signal()
    email_list_update = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._text_changed = False
        self._email_profile_names = []
        self.email_raw_html = ""
        self._loaded_email_index = 0

    def set_current_index(self, index: int):
        self._loaded_email_index = index

    def get_current_index(self):
        return self._loaded_email_index
    
    def get_current_profile_name(self):
        return self._email_profile_names[self._loaded_email_index]
        
    def save_email(self):
        # If theres a loaded index, then save changes to that profile
        if self._loaded_email_index != 0:
            print("save changes")
            pass
        else:
            # If there is no loaded index, then prompt user to save new profile
            self.save_button_dialog()

    def save_button_dialog(self):
        # Display a dialog box so the user can enter a name for the new profile
        # If the user clicks ok, then save the new profile
        # If the user clicks cancel, then do nothing
        while True:
            dialog = QtWidgets.QInputDialog()
            dialog.setLabelText("Enter a name for the new profile")
            dialog.setOkButtonText("Save")
            dialog.setCancelButtonText("Cancel")

            if dialog.exec():
                new_profile_name = dialog.textValue()
                # Only save if name exists
                if new_profile_name not in self._email_profile_names:
                    self.save_new_profile(new_profile_name)
                    break
                else:
                    message_box_window_title = "Email Profile Name Already Exists"
                    severity_icon = QtWidgets.QMessageBox.Information
                    text_body = f"Please choose a different name for the new profile.\n\nIf you would like to edit the existing profile '{new_profile_name}', please select it from the dropdown menu to make your changes."
                    buttons = [QtWidgets.QPushButton("Close")]
                    button_roles = [QtWidgets.QMessageBox.RejectRole]
                    callback = [None,]
                    message_box_dict = {
                        "title": message_box_window_title,
                        "icon": severity_icon,
                        "text": text_body,
                        "buttons": buttons,
                        "button_roles": button_roles,
                        "callback": callback
                    }

                    self.main_view_model.display_message_box(message_box_dict)
            else:
                break

    def save_new_profile(self, profile_name: str):
        # Create a new directory in the signatures folder
        # Save the html data to the new directory
        # Update the email profile names
        # Update the email profile combo box
        
        # Create the new directory
        directory = self.main_view_model.get_email_directory()
        new_directory = os.path.join(directory, profile_name)
        os.mkdir(new_directory)

        # Save the html data to the new directory
        html_file = os.path.join(new_directory, "email.html")
        with open(html_file, "w") as f:
            f.write(self.email_raw_html)
        
        # Update the email profile names
        self._email_profile_names.append(profile_name)
        self._loaded_email_index = len(self._email_profile_names) - 1
        self.email_profiles_updated.emit(self._email_profile_names)
        self.email_list_update.emit()


    def email_text_changed(self, text: str):
        self._text_changed = bool(text)
        self.email_raw_html = text
        print("text changed")

    def get_email_profiles(self):
        # Email data i.e. signatures are stored in individual subdirectories of the signatures directory
        # The name of the subdirectory is the name of the email profile
        # The signatures folder is to be created when the user first runs the program
        directory = self.main_view_model.get_email_directory()
        emails = [dir for dir in os.listdir(directory) if os.path.isdir(os.path.join(directory, dir))]
        
        if not emails:
            emails = [""]
        else:
            emails = [""] + emails

        self._email_profile_names = emails
        self.email_profiles_updated.emit(emails)
        return emails
    
    def email_profile_changed(self, index: int):
        # If user selects current profile, do nothing
        if index == self._loaded_email_index:
            return
        
        # If user selects an existing profile, and text has been changed 
        # from a current profile, prompt user to save changes
        if self._text_changed and index != 0:
            print("save changes?")
            return

        # If user selects an existing profile, and text has been changed, but there is no current profile
        # prompt user to save new profile, then load new profile
        if self._text_changed and self._loaded_email_index == 0:
            message_box_window_title = "Save Changes"
            severity_icon = QtWidgets.QMessageBox.Information
            text_body = f"Save new email before proceeding?"
            buttons = [QtWidgets.QPushButton(
                "Save New"), QtWidgets.QPushButton("Cancel")]
            button_roles = [QtWidgets.QMessageBox.YesRole,
                            QtWidgets.QMessageBox.RejectRole]
            callback = [self.save_button_dialog, None]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }

            self.main_view_model.display_message_box(message_box_dict)

        # If text has not been changed, and user selects index 0, empty the email box
        if not self._text_changed and index == 0:
            self.clear_email_text.emit()
            return

        # If text has not been changed, load whatever profile the user selects
        self.load_email_profile(self._email_profile_names[index])

    def load_email_profile(self, profile_name: str) :
        email_folder = os.path.join(self.main_view_model.get_email_directory(), profile_name)
        if not os.path.exists(email_folder):
            self.main_view_model.add_console_text(f"Email folder {email_folder} does not exist")
            self.main_view_model.add_console_alerts(1)
            return 
        
        email_html_file = os.path.join(email_folder, "email.html")
        if not os.path.exists(email_html_file):
            self.main_view_model.add_console_text(f"Email file not found for {email_folder}")
            self.main_view_model.add_console_alerts(1)
            return
        
        with open(email_html_file, "r") as f:
            self.email_raw_html = f.read()

        self.email_text_update.emit()

        return
