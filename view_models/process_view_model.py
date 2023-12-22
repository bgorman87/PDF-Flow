import base64
import mimetypes
import os
import subprocess
import uuid
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import msal
import requests
from google.auth.exceptions import GoogleAuthError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from lxml import html
from PySide6 import QtCore, QtWidgets

from utils import general_utils, image_utils, text_utils
from utils.enums import EmailProvider
from view_models import main_view_model


class ProcessViewModel(QtCore.QObject):
    processed_files_list_widget_update = QtCore.Signal(QtWidgets.QListWidgetItem)
    display_pdf_preview = QtCore.Signal()
    display_file_name = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel, Dispatch):
        super().__init__()
        self.main_view_model = main_view_model
        self._file_names = None
        self._selected_file_dir = None
        self._selected_file_name = None
        self._progress = 0
        self._thread_pool = QtCore.QThreadPool()
        self._token = ""
        self.Dispatch = Dispatch

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
        # Threads come with a cost though so we don't want to create too many
        # 50% of the total seems to be a good balance
        # Processing data comparison (Avg of 5 runs)
        # 100% Threads - 18 Files: 132s
        # 80% Threads - 18 Files: 9.6s
        # 70% Threads - 18 Files: 4.6s
        # 60% Threads - 18 Files: 3.0s
        # 50% Threads - 18 Files: 2.8s
        # 25% Threads - 18 Files: 4.9s
        max_threads = int(os.cpu_count() * 0.5)
        self._thread_pool.setMaxThreadCount(max_threads)

        for file_name in self._file_names:
            self.analyze_worker = image_utils.WorkerAnalyzeThread(
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
        # TODO: If doesn't exist remove from list widget and add
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
        if int(self._progress / len(self._file_names)) >= 100:
            self.main_view_model.set_process_progress_bar_text("Processing Complete.")

    def evt_analyze_complete(self, results: List[str]):
        """Appends processed files list widget with new processed file data

        Args:
            results (List[str]): processed file list
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

    def get_outlook_token(self) -> bool:
        """Gets Outlook token for use in API calls

        Returns:
            bool: True if token is successfully retrieved, False otherwise
        """

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
            message_box = general_utils.MessageBox()
            message_box.title = "Email Authentication Error"
            message_box.icon = QtWidgets.QMessageBox.Critical
            message_box.text = f"Authentication Error: {result['error']}\nDescription: {result['error_description']}"
            message_box.buttons = [QtWidgets.QPushButton("Close")]
            message_box.button_roles = [QtWidgets.QMessageBox.RejectRole]
            message_box.callback = [
                None,
            ]

            self.main_view_model.display_message_box(message_box=message_box)
            return False
        else:
            self._token = result["access_token"]
            return True

    def get_gmail_token(self) -> bool:
        """Gets GMail token for use in API calls

        Returns:
            bool: True if token is successfully retrieved, False otherwise
        """

        SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                "assets/credentials.json", SCOPES
            )
            credentials = flow.run_local_server(port=0)
        except (GoogleAuthError, FileNotFoundError) as e:
            self.main_view_model.add_console_text(f"Email Authentication Error: {e}")
            self.main_view_model.add_console_alerts(1)
            message_box = general_utils.MessageBox()
            message_box.title = "Email Authentication Error"
            message_box.icon = QtWidgets.QMessageBox.Critical
            message_box.text = f"Authentication Error: {e}"
            message_box.buttons = [QtWidgets.QPushButton("Close")]
            message_box.button_roles = [QtWidgets.QMessageBox.RejectRole]
            message_box.callback = [
                None,
            ]

            self.main_view_model.display_message_box(message_box)
            return False

        if credentials:
            self._token = credentials.token
            return True
        else:
            self.main_view_model.add_console_text(
                f"Email Authentication Error: Unexpected error occurred while confirming gmail credentials."
            )
            self.main_view_model.add_console_alerts(1)
            message_box = general_utils.MessageBox()
            message_box.title = "Email Authentication Error"
            message_box.icon = QtWidgets.QMessageBox.Critical
            message_box.text = f"Authentication Error: Unexpected error occurred while confirming gmail credentials."
            message_box.buttons = [QtWidgets.QPushButton("Close")]
            message_box.button_roles = [QtWidgets.QMessageBox.RejectRole]
            message_box.callback = [
                None,
            ]

            self.main_view_model.display_message_box(message_box)
            return False

    def email_files(
        self,
        email_items: List[QtWidgets.QListWidgetItem],
        email_provider: EmailProvider,
    ):
        """Emails the selected files

        Args:
            email_items (List[QtWidgets.QListWidgetItem]): List of Email items from processed files list widget
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
                if " - Outlook" in email_template:
                    profile_base_name = email_template.replace(" - Outlook", "")
                    outlook_directory = (
                        self.main_view_model.get_outlook_email_directory()
                    )

                    signature_name = ""
                    for filename in os.listdir(outlook_directory):
                        if (
                            filename.endswith(".htm") or filename.endswith(".html")
                        ) and (profile_base_name in filename):
                            signature_name = filename
                            break

                    email_template_path = os.path.join(
                        outlook_directory, signature_name
                    )

                else:
                    email_template_path = os.path.join(
                        self.main_view_model.get_local_email_directory(),
                        email_template,
                        "email.html",
                    )

                with open(email_template_path) as email_file:
                    body_content = email_file.read()

            subject = ""
            recipients = []
            cc_recipients = []
            bcc_recipients = []
            if file_data["project_number"] is not None:
                project_number = file_data["project_number"]
                email_template_info = (
                    self.main_view_model.fetch_project_data_by_project_number(
                        project_number
                    )
                )
                if email_template_info:
                    subject = email_template_info[6]
                    recipients += email_template_info[3].split(";")
                    cc_recipients += email_template_info[4].split(";")
                    bcc_recipients += email_template_info[5].split(";")

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
                    email_template,
                )
            elif email_provider == EmailProvider.GMAIL:
                email_info = self.create_gmail_draft_email(
                    subject,
                    body_content,
                    recipients,
                    cc_recipients,
                    bcc_recipients,
                    attachments,
                    email_template,
                )
            elif email_provider == EmailProvider.LOCAL:
                email_info = self.create_local_draft_email(
                    subject,
                    body_content,
                    recipients,
                    cc_recipients,
                    bcc_recipients,
                    attachments,
                    email_template,
                )
            if email_info.status_code == 201:
                self.main_view_model.add_console_text(
                    f"Draft email created for: {os.path.basename(source_path)}"
                )
                self.main_view_model.add_console_alerts(1)
            else:
                self.main_view_model.add_console_text(
                    f"Error creating draft email for: {os.path.basename(source_path)}"
                )
                self.main_view_model.add_console_text(
                    f"{email_info.status_code} - {email_info.text}"
                )
                self.main_view_model.add_console_alerts(1)

    def embed_images_as_base64(self, html_content: str) -> str:
        """Embeds images in html as base64

        Args:
            html_content (str): Body content for an HTML email

        Returns:
            str: html with images embedded as base64
        """
        root = html.fromstring(html_content)

        for img_tag in root.xpath("//img"):
            src = img_tag.get("src")
            if not src.startswith("data:image/"):
                # Read the image and encode it in base64
                with open(src, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

                # Get the image's format from its extension (e.g., .jpg -> jpeg)
                image_format = (
                    os.path.splitext(src)[1].replace(".", "").replace("jpg", "jpeg")
                )

                # Replace the src with the base64 encoded version
                img_tag.set("src", f"data:image/{image_format};base64,{encoded_string}")

        return html.tostring(root, encoding="unicode")

    def create_outlook_draft_email(
        self,
        subject: str,
        body_content: str,
        recipients: List[str],
        cc_recipients: List[str] = None,
        bcc_recipients: List[str] = None,
        attachments: List[str] = None,
        email_template: str = None,
    ) -> requests.Response:
        """Creates a draft email in Outlook

        Args:
            subject (str): Email subject
            body_content (str): Email body content
            recipients (List[str]): List of email recipients
            cc_recipients (List[str], optional): List of carbon copied recipients. Defaults to None.
            bcc_recipients (List[str], optional): List of blind carbon copied recipients. Defaults to None.
            attachments (List[str], optional): List of attachment file paths. Defaults to None.
            email_template (str, optional): Name of email template used. Defaults to None.

        Returns:
            requests.Response: Response from Outlook API
        """

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
        email["body"] = {
            "contentType": "HTML",
            "content": self.embed_images_as_base64(body_content),
        }
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

    def create_local_draft_email(
        self,
        subject: str,
        body_content: str,
        recipients: List[str],
        cc_recipients: List[str] = None,
        bcc_recipients: List[str] = None,
        attachments: List[str] = None,
        email_template: str = None,
    ) -> general_utils.FauxResponse:
        """Creates a draft email in local mail client

        Args:
            subject (str): Email subject
            body_content (str): Email body content
            recipients (List[str]): List of email recipients
            cc_recipients (List[str], optional): List of carbon copied recipients. Defaults to None.
            bcc_recipients (List[str], optional): List of blind carbon copied recipients. Defaults to None.
            attachments (List[str], optional): List of attachment file paths. Defaults to None.
            email_template (str, optional): Name of email template used. Defaults to None.

        Returns:
            general_utils.FauxResponse: Fake response mimicking requests.Response
        """

        if self.main_view_model.os == "win32":
            # Create draft using local outlook
            try:
                outlook = self.Dispatch("outlook.application")
                mail = outlook.CreateItem(0)
                mail.To = "; ".join(recipients) if recipients else ""
                mail.CC = "; ".join(cc_recipients) if cc_recipients else ""
                mail.BCC = "; ".join(bcc_recipients) if bcc_recipients else ""
                mail.Subject = subject
                mail.HtmlBody = body_content
                for attachment in attachments:
                    mail.Attachments.Add(attachment)
                mail.Save()

                return general_utils.FauxResponse(201, "success")
            except Exception as e:
                return general_utils.FauxResponse(500, e)
        elif self.main_view_model.os == "linux":
            cmd = ["which", "thunderbird"]
            try:
                # Check if thunderbird is installed
                subprocess.run(cmd)
            except Exception:
                return general_utils.FauxResponse(
                    500,
                    "Thunderbird installation not found. Please install Thunderbird to use this feature on this platform. Please notify the developer if you would like to see support for additional mail clients on this platform.",
                )
            compose_str = f"to='{','.join(recipients)}',subject='{subject}'"
            # compose_str += f",message='{body_content}'"
            if cc_recipients:
                compose_str += f",cc='{','.join(cc_recipients)}'"
            if bcc_recipients:
                compose_str += f",bcc='{','.join(bcc_recipients)}'"
            # if attachments:
            # compose_str += f",attachment='{','.join(attachments)}'"

            cmd = ["thunderbird", "-compose", compose_str]
            subprocess.run(cmd)
            return general_utils.FauxResponse(201, "success")
        else:
            return general_utils.FauxResponse(
                500,
                "Local email not supported on this platform. Supported platforms are Windows and Linux. Please notify the developer if you would like to see support for this platform.",
            )

    def create_gmail_draft_email(
        self,
        subject: str,
        body_content: str,
        recipients: List[str],
        cc_recipients: List[str] = None,
        bcc_recipients: List[str] = None,
        attachments: List[str] = None,
        email_template: str = None,
    ) -> general_utils.FauxResponse:
        """Creates a draft email in Gmail

        Args:
            subject (str): Email subject
            body_content (str): Email body content
            recipients (List[str]): List of email recipients
            cc_recipients (List[str], optional): List of carbon copied recipients. Defaults to None.
            bcc_recipients (List[str], optional): List of blind carbon copied recipients. Defaults to None.
            attachments (List[str], optional): List of attachment file paths. Defaults to None.
            email_template (str, optional): Name of email template used. Defaults to None.

        Returns:
            general_utils.FauxResponse: Fake response mimicking requests.Response
        """

        # Create the Gmail API client
        credentials = Credentials(token=self._token)
        service = build("gmail", "v1", credentials=credentials)

        # Construct the email headers
        email_to = ", ".join(recipients)
        email_cc = ", ".join(cc_recipients) if cc_recipients else None
        email_bcc = ", ".join(bcc_recipients) if bcc_recipients else None

        msg = MIMEMultipart(_subtype="related")  # Use 'related' for CID referencing
        msg["to"] = email_to
        msg["subject"] = subject
        if email_cc:
            msg["cc"] = email_cc
        if email_bcc:
            msg["bcc"] = email_bcc

        image_attachments = []
        root = html.fromstring(body_content)
        for img_tag in root.xpath("//img"):
            src = img_tag.get("src")
            if src.startswith("data:image/"):
                # Extracting the file type and base64 data
                file_type = src.split(";")[0].split("/")[-1]
                base64_data = src.split(",")[1]

                # Decoding the base64 data to get the image
                image_data = base64.b64decode(base64_data)

                # Generating a random filename with the identified file type
                random_filename = f"{uuid.uuid4()}.{file_type}"
                new_img_path = os.path.join(
                    self.main_view_model.get_local_email_directory(),
                    email_template,
                    random_filename,
                )

                # Saving the image to the new directory
                with open(new_img_path, "wb") as f:
                    f.write(image_data)

                cid = os.path.basename(new_img_path)
                img_tag.set("src", f"cid:{cid}")
                # Attach the extracted image with CID
                with open(new_img_path, "rb") as file:
                    image_data = file.read()
                image_mime_type, _ = mimetypes.guess_type(new_img_path)
                main_type, sub_type = image_mime_type.split("/")
                image = MIMEImage(image_data, sub_type, name=cid)
                image.add_header("Content-ID", f"<{cid}>")
                image.add_header("Content-Disposition", "inline", filename=cid)
                image_attachments.append(image)
            else:
                # For non-base64 images, just attach and set CID
                cid = os.path.basename(src)
                img_tag.set("src", f"cid:{cid}")

                with open(src, "rb") as file:
                    image_data = file.read()
                image_mime_type, _ = mimetypes.guess_type(src)
                main_type, sub_type = image_mime_type.split("/")
                image = MIMEImage(image_data, sub_type, name=cid)
                image.add_header("Content-ID", f"<{cid}>")
                image.add_header("Content-Disposition", "inline", filename=cid)
                image_attachments.append(image)

        for img_tag in root.xpath("//img"):
            src = img_tag.get("src")
            print(src)

        # Convert the modified HTML back to string and attach
        body_content = html.tostring(root, method="html", encoding="unicode")
        msg.attach(MIMEText(body_content, _subtype="html"))

        for image in image_attachments:
            msg.attach(image)

        # Attach other files if any
        for attachment_path in attachments or []:
            with open(attachment_path, "rb") as file:
                attachment_data = file.read()
            mime_type, _ = mimetypes.guess_type(attachment_path)
            main_type, sub_type = mime_type.split("/")
            attachment = MIMEImage(attachment_data, sub_type)
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(attachment_path),
            )
            msg.attach(attachment)

        raw_email = base64.b64encode(msg.as_bytes()).decode("utf-8")

        # Create draft using the Gmail API
        try:
            draft_body = {"message": {"raw": raw_email}}
            service.users().drafts().create(userId="me", body=draft_body).execute()

            return general_utils.FauxResponse(201, "success")
        except Exception as e:
            return general_utils.FauxResponse(500, e)

    def get_local_email_icon_path(self) -> str:
        """Gets the path to the local email icon depending on the detected OS

        Returns:
            str: Path to the local email icon
        """
        if self.main_view_model.os == "win32":
            return "assets/icons/outlook-local.png"
        else:
            return "assets/icons/thunderbird-local.png"
