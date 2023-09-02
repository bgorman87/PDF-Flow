from PySide6 import QtCore, QtWidgets
import os

from view_models import main_view_model


class EmailViewModel(QtCore.QObject):
    email_profiles_updated = QtCore.Signal(list)
    email_text_update = QtCore.Signal()
    clear_email_text = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._text_changed = False
        self._email_profile_names = []
        self.email_raw_html = ""
        

    def save_email(self):
        self._text_changed = False
        print("Email saved")

    def email_text_changed(self, text_changed: bool):
        self._text_changed = text_changed
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
    
    def email_profile_changed(self, index: int, loaded_index: int):
        # If user selects current profile, do nothing
        if index == loaded_index:
            return
        
        # If user selects an existing profile, and text has been changed 
        # from a current profile, prompt user to save changes
        if self._text_changed and loaded_index != 0:
            pass

        # If user selects an existing profile, and text has been changed, but there is no current profile
        # prompt user to save new profile, then load new profile
        if self._text_changed and loaded_index == 0:
            pass

        # If text has not been changed, and user selects index 0, empty the email box
        if not self._text_changed and index == 0:
            self.clear_email_text.emit()
            return

        # If text has not been changed, load whatever profile the user selects
        self.load_email_profile(self._email_profile_names[index-1])

    def load_email_profile(self, profile_name: str) :
        email_folder = os.path.join(self.main_view_model.get_email_directory(), profile_name)
        if not os.path.exists(email_folder):
            self.main_view_model.add_console_text(f"Email folder {email_folder} does not exist")
            self.main_view_model.add_console_alerts(1)
            return 
        
        # Create hardcoded html data for now
        self.email_raw_html = "<p>Test</p>"
        self.email_text_update.emit()

        return

    

