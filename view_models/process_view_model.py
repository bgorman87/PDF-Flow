import os
import base64
import requests
import msal
import mimetypes

from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

from PySide6 import QtCore, QtWidgets

from functions import analysis
from view_models import main_view_model
from utils.enums import EmailProvider
from utils.utils import FauxResponse


class ProcessViewModel(QtCore.QObject):
    processed_files_list_widget_update = QtCore.Signal(QtWidgets.QListWidgetItem)
    display_pdf_preview = QtCore.Signal()
    display_file_name = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._file_names = None
        self._selected_file_dir = None
        self._selected_file_name = None
        self._progress = 0
        self._thread_pool = QtCore.QThreadPool()
        self._token = ""

    def get_files(self):
        """Opens a file dialog to select files for input"""
        # When clicking Select Files, clear any previously selected files, and reset the file status box
        self._file_names = None
        self.main_view_model.set_loaded_files_count(0)

        self._file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            caption="Select Files to Process", filter="PDF (*.pdf)"
        )

        self.main_view_model.set_process_progress_bar_value(0)
        if not self._file_names:
            self.main_view_model.set_process_button_state(False)
            self.main_view_model.set_process_progress_bar_text(
                "Select Files to Begin..."
            )
            return

        self.main_view_model.set_process_progress_bar_text(
            "Press 'Process' Button to Start Processing Files..."
        )

        number_files = len(self._file_names)

        file_names_string = f"New Selection of ({number_files}) file"
        if number_files == 0:
            file_names_string += ":"
        else:
            file_names_string += "s:"

        for item in self._file_names:
            file_names_string += f"\n{item}"

        self.main_view_model.set_process_button_count(
            f"Process ({len(self._file_names)} Selected)"
        )

        # Signals for this are defined in main_view_model because nav needs the info as well
        self.main_view_model.add_console_text(file_names_string)
        self.main_view_model.add_console_alerts(number_files)
        self.main_view_model.set_loaded_files_count(number_files)
        self.main_view_model.set_process_button_state(True)
        self.main_view_model.set_process_button_count(number_files)

    # For each file in self._file_names create a thread to process
    def process_files(self):
        """Processes the selected files"""
        self.main_view_model.set_process_progress_bar_text("Processing... %p%")
        # For each file create a new thread to increase performance
        for file_name in self._file_names:
            self.analyze_worker = analysis.WorkerAnalyzeThread(
                file_name=file_name, main_view_model=self.main_view_model
            )
            self.analyze_worker.signals.analysis_progress.connect(
                self.evt_analyze_progress
            )
            self.analyze_worker.signals.analysis_result.connect(
                self.evt_analyze_complete
            )
            self._thread_pool.start(self.analyze_worker)
            self.evt_analyze_progress(10)
        self.main_view_model.set_process_button_count(0)

    def list_widget_handler(self, list_widget_item: QtWidgets.QListWidgetItem):
        """Displays the currently selected list widget item"""

        file_dirs = list_widget_item.data(QtCore.Qt.UserRole)
        source_dir = file_dirs["source"].replace("\\", "/")
        # TODO: If doesnt exist remove from list widget and add
        # notice to the console
        # if not os.path.exists(source_dir):
        # self.processed_files_list_widget.takeItem(
        #     self.processed_files_list_widget.currentRow()
        # )
        # self.processed_files_list_widget.setCurrentRow(0)
        # set_text = self.processed_files_list_widget.currentItem().text()
        # self.file_rename_line_edit.setText(set_text)
        # return
        self._selected_file_dir = source_dir
        self.display_pdf_preview.emit()

        self._selected_file_name = list_widget_item.text()
        self.display_file_name.emit()

    @property
    def selected_file_dir(self) -> str:
        return self._selected_file_dir

    @property
    def selected_file_name(self) -> str:
        return self._selected_file_name

    def evt_analyze_progress(self, val: int):
        """Updates main progress bar based off of emitted progress values.

        Args:
            val (int): Current progress level of file being analyzed
        """

        # Since val is progress of each individual file, need to ensure whole progress accounts for all files
        self._progress += val
        self.main_view_model.set_process_progress_bar_value(
            int(self._progress / len(self._file_names))
        )
        if self._progress >= 100:
            self.main_view_model.set_process_progress_bar_text("Processing Complete.")

    def evt_analyze_complete(self, results: list[str]):
        """Appends processed files list widget with new processed file data

        Args:
            results (list): processed file list
        """
        print_string = results[0]
        file_name = results[1]
        file_path = results[2]
        project_data_dir = results[3]
        project_number = results[4]
        profile_id = results[5]

        file_data = {
            "source": file_path,
            "project_data": project_data_dir,
            "project_number": project_number,
            "profile_id": profile_id,
        }
        self.main_view_model.add_console_text(print_string)
        processed_files_list_item = QtWidgets.QListWidgetItem(file_name)
        processed_files_list_item.setData(QtCore.Qt.UserRole, file_data)
        self.processed_files_list_widget_update.emit(processed_files_list_item)
        self.main_view_model.update_processed_files_count(1)
        self.main_view_model.set_process_button_state(False)
        self.main_view_model.set_process_button_count(0)

    def rename_file(self, source_path: str, renamed_source_path: str):
        """Renames a file

        Args:
            source_path (str): Current file name
            renamed_source_path (str): New file name
        """
        try:
            os.rename(source_path, renamed_source_path)
            return True
        except OSError as e:
            self.main_view_model.add_console_text(
                f"Error renaming file - Please check if new directory exists:\nSource: {source_path}\nNew: {renamed_source_path}"
            )
            self.main_view_model.add_console_alerts(1)
            return False
        
    def get_outlook_token(self):
        authority = "https://login.microsoftonline.com/common"
        client_id = "c7cba64c-6df8-4e34-a136-f5a0a01428e7"

        app = msal.PublicClientApplication(client_id, authority=authority)
        result = None
        scope = ["User.Read", "Mail.ReadWrite"]  # Adjust scopes as needed.

        # Look for an existing token in the cache
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scope, account=accounts[0])

        # If no token exists in the cache or it's expired, get a new one using interactive flow
        if not result:
            result = app.acquire_token_interactive(scope)

        if "error" in result:
            self.main_view_model.add_console_text(
                f"Email Authentication Error: {result['error']}"
            )
            self.main_view_model.add_console_alerts(1)
            message_box_window_title = "Email Authentication Error"
            severity_icon = QtWidgets.QMessageBox.Critical
            text_body = f"Authentication Error: {result['error']}\nDescription: {result['error_description']}"
            buttons = [QtWidgets.QPushButton("Close")]
            button_roles = [QtWidgets.QMessageBox.RejectRole]
            callback = [
                None,
            ]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback,
            }

            self.main_view_model.display_message_box(message_box_dict)
            return False
        else:
            self._token = result["access_token"]
            return True

    def get_gmail_token(self):
        SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                    'assets/credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        except (GoogleAuthError, FileNotFoundError) as e:
            self.main_view_model.add_console_text(
                f"Email Authentication Error: {e}"
            )
            self.main_view_model.add_console_alerts(1)
            message_box_window_title = "Email Authentication Error"
            severity_icon = QtWidgets.QMessageBox.Critical
            text_body = f"Authentication Error: {e}"
            buttons = [QtWidgets.QPushButton("Close")]
            button_roles = [QtWidgets.QMessageBox.RejectRole]
            callback = [
                None,
            ]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback,
            }

            self.main_view_model.display_message_box(message_box_dict)
            return False
                
        if credentials:
            self._token = credentials.token
            return True
        else:
            self.main_view_model.add_console_text(
                f"Email Authentication Error: Unexpected error occurred while confirming gmail credentials."
            )
            self.main_view_model.add_console_alerts(1)
            message_box_window_title = "Email Authentication Error"
            severity_icon = QtWidgets.QMessageBox.Critical
            text_body = f"Authentication Error: Unexpected error occurred while confirming gmail credentials."
            buttons = [QtWidgets.QPushButton("Close")]
            button_roles = [QtWidgets.QMessageBox.RejectRole]
            callback = [
                None,
            ]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback,
            }

            self.main_view_model.display_message_box(message_box_dict)
            return False

    def email_files(self, email_items: [QtWidgets.QListWidgetItem], email_provider: EmailProvider):
        """Emails the selected files

        Args:
            email_items ([QtWidgets.QListWidgetItem]): List of Email items from processed files list widget
        """

        for email_item in email_items:
            file_data = email_item.data(QtCore.Qt.UserRole)
            source_path = file_data["source"]

            # Project specific email templates override report specific email templates
            email_template = (
                self.main_view_model.fetch_email_profile_name_by_project_number(
                    file_data["project_number"]
                )
            )
            
            if not email_template:
                email_template = (
                    self.main_view_model.fetch_email_profile_name_by_profile_id(
                        file_data["profile_id"]
                    )
                )
            print("Template: ", email_template)
            self.main_view_model.update_emailed_files_update_count(1)
            body_content = ""
            if email_template:
                email_template_path = os.path.join(
                    self.main_view_model.get_email_directory(), email_template, "email.html"
                )

                with open(email_template_path) as email_file:
                    body_content = email_file.read()
            subject = ""
            recipients = []
            cc_recipients = []
            bcc_recipients = []
            if file_data["project_number"] is not None:
                project_number = file_data["project_number"]
                email_template_info = self.main_view_model.fetch_project_data_by_project_number(
                    project_number
                )
                if email_template_info:
                    subject = email_template_info[5]
                    recipients += email_template_info[2].split(";")
                    cc_recipients += email_template_info[3].split(";")
                    bcc_recipients += email_template_info[4].split(";")
                
            attachments = [
                source_path,
            ]
            if email_provider == EmailProvider.OUTLOOK:
                email_info = self.create_outlook_draft_email(
                    subject,
                    body_content,
                    recipients,
                    cc_recipients,
                    bcc_recipients,
                    attachments,
                )
            elif email_provider == EmailProvider.GMAIL:
                email_info = self.create_gmail_draft_email(
                    subject,
                    body_content,
                    recipients,
                    cc_recipients,
                    bcc_recipients,
                    attachments,
                )
            if email_info.status_code == 201:
                self.main_view_model.add_console_text(f"Draft email created for: {os.path.basename(source_path)}")
                self.main_view_model.add_console_alerts(1)
            else:
                self.main_view_model.add_console_text(f"Error creating draft email for: {os.path.basename(source_path)}")
                self.main_view_model.add_console_text(f"{email_info.status_code} - {email_info.text()}")
                self.main_view_model.add_console_alerts(1)

    def create_outlook_draft_email(
        self,
        subject,
        body_content,
        recipients,
        cc_recipients=None,
        bcc_recipients=None,
        attachments: list = None,
    ):
        # Endpoint for creating draft messages
        url = "https://graph.microsoft.com/v1.0/me/messages"
        base64_attachments = []
        if attachments:
            # Take each file path and convert the actual file to base64
            for attachment in attachments:
                with open(attachment, "rb") as attachment_file:
                    base64_attachments.append(
                        {
                            "name": os.path.basename(attachment),
                            "data": base64.b64encode(attachment_file.read()).decode(
                                "utf-8"
                            ),
                        }
                    )

        # Define the draft email's details
        email = {}
        email["isDraft"] = True
        email["subject"] = subject
        email["body"] = {"contentType": "HTML", "content": body_content}
        if recipients:
            email["toRecipients"] = [
                {"emailAddress": {"address": recipient}} for recipient in recipients
            ]
        if cc_recipients:
            email["ccRecipients"] = [
                {"emailAddress": {"address": recipient}} for recipient in cc_recipients
            ]
        if bcc_recipients:
            email["bccRecipients"] = [
                {"emailAddress": {"address": recipient}} for recipient in bcc_recipients
            ]
        if base64_attachments:
            email["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": base64_attachment["name"],
                    "contentBytes": base64_attachment["data"],
                }
                for base64_attachment in base64_attachments
            ]

        headers = {
            "Authorization": "Bearer {}".format(self._token),
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=email)

        return response
    
    def create_gmail_draft_email(
        self,
        subject,
        body_content,
        recipients,
        cc_recipients=None,
        bcc_recipients=None,
        attachments: list = None,
    ):
        # Create the Gmail API client
        credentials = Credentials(token=self._token)
        service = build('gmail', 'v1', credentials=credentials)

        # Construct the email headers
        email_to = ', '.join(recipients)
        email_cc = ', '.join(cc_recipients) if cc_recipients else None
        email_bcc = ', '.join(bcc_recipients) if bcc_recipients else None

        # Create the email body as MIMEText
        msg = EmailMessage()
        msg['to'] = email_to
        if email_cc:
            msg['cc'] = email_cc
        if email_bcc:
            msg['bcc'] = email_bcc
        msg['subject'] = subject
        msg.add_alternative(body_content, subtype='html')

        # Attach files if any
        for attachment_path in attachments:
            type_subtype, _ = mimetypes.guess_type(attachment_path)
            maintype, subtype = type_subtype.split('/')
            with open(attachment_path, 'rb') as file:
                attachment_data = file.read()
            msg.add_attachment(attachment_data, maintype, subtype, filename=os.path.basename(attachment_path))

        # Convert email to raw and then to base64
        raw_email = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

        # Create draft using the Gmail API
        try:
            draft_body = {
                'message': {
                    'raw': raw_email
                }
            }
            service.users().drafts().create(userId='me', body=draft_body).execute()

            return FauxResponse(201, "success")
        except Exception as e:
            return FauxResponse(500, e)

    def build_file_part(self, file):
        """Creates a MIME part for a file.

        Args:
        file: The path to the file to be attached.

        Returns:
        A MIME part that can be attached to a message.
        """
        content_type, encoding = mimetypes.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            with open(file, 'rb'):
                msg = MIMEText('r', _subtype=sub_type)
        elif main_type == 'image':
            with open(file, 'rb'):
                msg = MIMEImage('r', _subtype=sub_type)
        elif main_type == 'audio':
            with open(file, 'rb'):
                msg = MIMEAudio('r', _subtype=sub_type)
        else:
            with open(file, 'rb'):
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(file.read())
        filename = os.path.basename(file)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        return msg
