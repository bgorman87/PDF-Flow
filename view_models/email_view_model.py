import base64
import os
import shutil
import uuid
from bs4 import BeautifulSoup
from lxml import html
from PySide6 import QtCore, QtWidgets

from utils import general_utils
from view_models import main_view_model


class EmailViewModel(QtCore.QObject):
    email_profiles_updated = QtCore.Signal(list)
    email_text_update = QtCore.Signal()
    clear_email_text = QtCore.Signal()
    email_list_update = QtCore.Signal()
    set_current_index_signal = QtCore.Signal(int)

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._text_changed = False
        self._email_profile_names = []
        self.email_raw_html = ""
        self._loaded_email_index = 0
        self._loaded_raw_html = ""

    def set_current_index(self, index: int):
        self._loaded_email_index = index

    def get_current_index(self):
        return self._loaded_email_index

    def get_current_profile_name(self):
        return self._email_profile_names[self._loaded_email_index]

    def get_text_changed(self):
        return self._text_changed

    def set_loaded_raw_html(self, raw_html: str):
        self._loaded_raw_html = raw_html

    @property
    def formatted_html(self):
        return self._loaded_raw_html

    def save_email(self):
        # If theres a loaded index, then save changes to that profile
        if self._loaded_email_index != 0:
            self.save_changes_button_dialog(self._loaded_email_index)
        else:
            # If there is no loaded index, then prompt user to save new profile
            self.save_new_button_dialog()

        return

    def save_new_button_dialog(self):
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
                    message_box = general_utils.MessageBox()
                    message_box.title = "Email Profile Name Already Exists"
                    message_box.icon = QtWidgets.QMessageBox.Information
                    message_box.text = f"Please choose a different name for the new profile.\n\nIf you would like to edit the existing profile '{new_profile_name}', please select it from the dropdown menu to make your changes."
                    message_box.buttons = [QtWidgets.QPushButton("Close")]
                    message_box.button_roles = [QtWidgets.QMessageBox.RejectRole]
                    message_box.callback = [
                        None,
                    ]

                    self.main_view_model.display_message_box(message_box=message_box)
            else:
                break

    def save_changes_button_dialog(self, index: int):
        # Display a dialog box so asking the user if they want to save changes
        # If the user clicks yes, then save the changes by overwriting the existing profile
        # If the user clicks no, then do nothing
        message_box = general_utils.MessageBox()
        message_box.title = "Save Changes"
        message_box.icon = QtWidgets.QMessageBox.Information
        message_box.text = (
            f"Save changes to '{self._email_profile_names[self._loaded_email_index]}'?"
        )
        message_box.buttons = [
            QtWidgets.QPushButton("Save Changes"),
            QtWidgets.QPushButton("Discard Changes"),
            QtWidgets.QPushButton("Cancel"),
        ]
        message_box.button_roles = [
            QtWidgets.QMessageBox.YesRole,
            QtWidgets.QMessageBox.NoRole,
            QtWidgets.QMessageBox.RejectRole,
        ]
        message_box.callback = [
            lambda: self.save_changes(index),
            lambda: self.discard_changes(index),
            lambda: self.set_current_index_signal.emit(self._loaded_email_index),
        ]

        self.main_view_model.display_message_box(message_box=message_box)
        return

    def save_changes(self, index: int):
        # Overwrite the existing profile with the new changes
        # Update the email profile names
        # Update the email profile combo box
        directory = self.main_view_model.get_local_email_directory()
        email_folder = os.path.join(
            directory, self._email_profile_names[self._loaded_email_index]
        )
        self.save_email_signature(email_folder)

        self._text_changed = False
        self._loaded_raw_html = self.email_raw_html
        self._loaded_email_index = index
        self.load_email_profile(self._email_profile_names[index])

        return

    def discard_changes(self, index: int):
        self.set_current_index(index)
        self.load_email_profile(self._email_profile_names[index])
        self.set_current_index_signal.emit(index)

    def save_new_profile(self, profile_name: str):
        # Create a new directory in the signatures folder
        # Save the html data to the new directory
        # Update the email profile names
        # Update the email profile combo box

        # Create the new directory
        directory = self.main_view_model.get_local_email_directory()
        new_directory = os.path.join(directory, profile_name)
        try:
            os.mkdir(new_directory)
        except OSError as e:
            message_box = general_utils.MessageBox()
            message_box.title = "Email Creation Error"
            message_box.icon = QtWidgets.QMessageBox.Information
            message_box.text = f"Email creation error. Most likely invalid folder/file name: {profile_name}"
            message_box.buttons = [QtWidgets.QPushButton("Close")]
            message_box.button_roles = [QtWidgets.QMessageBox.RejectRole]
            message_box.callback = [
                None,
            ]

            self.main_view_model.display_message_box(message_box)

            return

        # Save the html data to the new directory
        self.save_email_signature(new_directory)
        # html_file = os.path.join(new_directory, "email.html")
        # with open(html_file, "w") as f:
        #     f.write(self.email_raw_html)

        # Update the email profile names
        self._text_changed = False
        self._email_profile_names.append(profile_name)
        self.main_view_model.update_email_profile_names(self._email_profile_names)
        self.set_current_index(self._email_profile_names.index(profile_name))
        self.email_list_update.emit()

    def save_email_signature(self, new_directory: str):
        """Parses the email html and saves all images to the new directory and updates the src attribute to point to the new image location.

        Args:
            new_directory (str): Path to the signature directory
        """

        root = html.fromstring(self.email_raw_html)

        for img_tag in root.xpath("//img"):
            src = img_tag.get("src")

            # Check if the image is base64 encoded
            if src.startswith("data:image/"):
                # Extracting the file type and base64 data
                file_type = src.split(";")[0].split("/")[-1]
                base64_data = src.split(",")[1]

                # Decoding the base64 data to get the image
                image_data = base64.b64decode(base64_data)

                # Generating a random filename with the identified file type
                random_filename = f"{uuid.uuid4()}.{file_type}"
                new_img_path = os.path.join(new_directory, random_filename)

                # Saving the image to the new directory
                with open(new_img_path, "wb") as f:
                    f.write(image_data)

                # Update the src attribute to point to the new image location
                img_tag.set("src", new_img_path)

            # If the image is not base64 encoded
            elif (
                not "://" in src
            ):  # This ensures it's a local path and not an external URL
                # Generate a random filename while preserving the image's extension
                extension = os.path.splitext(src)[1]
                random_filename = f"{uuid.uuid4()}{extension}"
                new_img_path = os.path.join(new_directory, random_filename)

                # Copy the image to the new directory
                shutil.copy2(src, new_img_path)

                # Update the src attribute to point to the new image location
                img_tag.set("src", new_img_path)

        self.email_raw_html = html.tostring(root, encoding="unicode")

        html_file = os.path.join(new_directory, "email.html")
        with open(html_file, "w") as f:
            f.write(self.email_raw_html)

    def email_text_changed(self, raw_html: str, plain_text: str):
        self.email_raw_html = raw_html
        if self._loaded_email_index == 0 or self._loaded_email_index == -1:
            self._text_changed = self._loaded_raw_html != plain_text
        else:
            self._text_changed = self._loaded_raw_html != self.email_raw_html
        print(f"text changed {self._text_changed}")

    def get_email_profiles(self):
        current_name = ""
        if len(self._email_profile_names) > 0 and self._loaded_email_index != 0:
            current_name = self._email_profile_names[self._loaded_email_index]

        # Email data i.e. signatures are stored in individual subdirectories of the signatures directory
        # The name of the subdirectory is the name of the email profile
        # The signatures folder is to be created when the user first runs the program
        directory = self.main_view_model.get_local_email_directory()
        emails = [
            dir
            for dir in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, dir))
        ]

        if not emails:
            emails = [""]
        else:
            emails = [""] + emails

        # After getting local email signatures, try to add in Outlook signatures
        for filename in os.listdir(self.main_view_model.get_outlook_email_directory()):
            if filename.endswith(".htm") or filename.endswith(
                ".html"
            ):  # For HTML signatures
                signature_name = filename.split(".")[0]
                emails.append(signature_name + " - Outlook")
        # New entries can be added here as program runs, so indexing can become off
        # If the current name is in the updated list, then set the loaded index to that index
        if current_name:
            try:
                self._loaded_email_index = emails.index(current_name)
            except ValueError:
                self._loaded_email_index = 0

        self._email_profile_names = emails
        self.main_view_model.update_email_profile_names(emails)
        return emails

    def email_profile_changed(self, index: int):
        # If user selects current profile, do nothing
        if index == self._loaded_email_index:
            return

        # If there is a loaded profile, and text has been changed, prompt user to save changes
        if self._text_changed and self._loaded_email_index != 0:
            self.save_changes_button_dialog(index)
            return

        # If user selects an existing profile, and text has been changed, but there is no current profile
        # prompt user to save new profile, then load new profile
        if self._text_changed and self._loaded_email_index == 0:
            message_box = general_utils.MessageBox()
            message_box.title = "Save Changes"
            message_box.icon = QtWidgets.QMessageBox.Information
            message_box.text = f"Save new email before proceeding?"
            message_box.buttons = [
                QtWidgets.QPushButton("Save New"),
                QtWidgets.QPushButton("Cancel"),
            ]
            message_box.button_roles = [
                QtWidgets.QMessageBox.YesRole,
                QtWidgets.QMessageBox.RejectRole,
            ]
            message_box.callback = [self.save_new_button_dialog, None]

            self.main_view_model.display_message_box(message_box=message_box)

        # If text has not been changed, and user selects index 0, empty the email box
        if not self._text_changed and index == 0:
            self.set_current_index(index)
            self._loaded_raw_html = ""
            self.clear_email_text.emit()
            return

        # If text has not been changed, load whatever profile the user selects
        self.set_current_index(index)
        self.load_email_profile(self._email_profile_names[index])

    def format_external_html(self, signature_name: str, html: str) -> str:
        soup = BeautifulSoup(html, 'lxml')
        
        def update_path(tag, attribute):
            if tag.has_attr(attribute):
                rel_path = tag[attribute]
                # Check if the path is relative and not an external link
                if rel_path and not rel_path.startswith(('http:', 'https:', 'mailto:', '#')):
                    abs_path = os.path.join(self.main_view_model.get_outlook_email_directory(), *rel_path.split("/"))
                    tag[attribute] = abs_path

        # Update src and href attributes
                    
        def custom_selector(tag):
            # Return tags with either a 'src' or 'href' attribute
            return (tag.name is not None) and (tag.has_attr('src') or tag.has_attr('href'))

        for tag in soup.find_all(custom_selector):
            update_path(tag, 'src')
            update_path(tag, 'href')

        return(str(soup))

    def load_email_profile(self, profile_name: str):
        # For now, check if name has ' - Outlook' to determine if email is from outlook
        # TODO In future, update database to also store the location of the email Signature
        if " - Outlook" not in profile_name:

            local_email_folder = os.path.join(
                self.main_view_model.get_local_email_directory(), profile_name
            )

            if not os.path.exists(local_email_folder):
                self.main_view_model.add_console_text(
                    f"Email folder {local_email_folder} does not exist"
                )
                self.main_view_model.add_console_alerts(1)
                return

            email_html_file = os.path.join(local_email_folder, "email.html")

            if not os.path.exists(email_html_file):
                self.main_view_model.add_console_text(
                    f"Email file not found for {local_email_folder}"
                )
                self.main_view_model.add_console_alerts(1)
                return
            
            with open(email_html_file, "r") as f:
                self.email_raw_html = f.read()

            self._loaded_raw_html = self.email_raw_html

        else:
            profile_base_name = profile_name.replace(" - Outlook", "")
            outlook_directory = self.main_view_model.get_outlook_email_directory()
            
            signature_name = ""
            for filename in os.listdir(outlook_directory):
                if (filename.endswith(".htm") or filename.endswith(".html")) and (profile_base_name in filename):
                    signature_name = filename
                    break
            
            if not os.path.exists(outlook_directory):
                self.main_view_model.add_console_text(
                    f"Email folder {local_email_folder} does not exist"
                )
                self.main_view_model.add_console_alerts(1)
                return

            email_html_file = os.path.join(outlook_directory, signature_name)

            if not os.path.exists(email_html_file):
                self.main_view_model.add_console_text(
                    f"Email file not found for {local_email_folder}"
                )
                self.main_view_model.add_console_alerts(1)
                return

            with open(email_html_file, "r") as f:
                self.email_raw_html = f.read()

            self._loaded_raw_html = self.format_external_html(profile_base_name, self.email_raw_html)

        self.email_text_update.emit()

        return

    def delete_email_profile_dialog(self):
        # Display a dialog box so asking the user if they want to delete the profile
        # If the user clicks yes, then delete the profile
        # If the user clicks no, then do nothing
        message_box = general_utils.MessageBox()
        message_box.title = "Delete Email Profile"
        message_box.icon = QtWidgets.QMessageBox.Information
        message_box.text = f"Delete email template '{self._email_profile_names[self._loaded_email_index]}'?"
        message_box.buttons = [
            QtWidgets.QPushButton("Delete"),
            QtWidgets.QPushButton("Cancel"),
        ]
        message_box.button_roles = [
            QtWidgets.QMessageBox.YesRole,
            QtWidgets.QMessageBox.RejectRole,
        ]
        message_box.callback = [self.delete_email_profile, None]

        self.main_view_model.display_message_box(message_box=message_box)
        return

    def delete_email_profile(self):
        profile_name = self._email_profile_names[self._loaded_email_index]
        email_folder = os.path.join(
            self.main_view_model.get_local_email_directory(), profile_name
        )
        if not os.path.exists(email_folder):
            self.main_view_model.add_console_text(
                f"Email deletion error: Email folder {email_folder} does not exist"
            )
            self.main_view_model.add_console_alerts(1)
            return

        try:
            shutil.rmtree(email_folder)
        except OSError as e:
            self.main_view_model.add_console_text(f"Email deletion error: {e}")
            self.main_view_model.add_console_alerts(1)
            return

        self._email_profile_names.pop(self._loaded_email_index)
        self._text_changed = False
        self._loaded_raw_html = ""
        self.set_current_index(0)

        self.set_current_index_signal.emit(0)
        self.main_view_model.update_email_profile_names(self._email_profile_names)
        self.email_list_update.emit()
        self.clear_email_text.emit()

        return
