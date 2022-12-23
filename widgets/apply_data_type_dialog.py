from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QLineEdit

class ApplyFoundData(QDialog):
    """Dialog box class used to displays information for creating new profiles and appliyng parameters"""    

    def __init__(self, coords, found_text, dialog_type={"parameter": False, "file_profile": False, "project_number": False}, parent=None):
        super(ApplyFoundData, self).__init__(parent)

        self.coords = coords
        self.found_text = found_text          

        # TODO: Look into adjusting layout to look better
        self.layout = QVBoxLayout()
        
        self.description = QLineEdit()

        if dialog_type.get("parameter") is not None:
            message = QLabel("Data Description: (Any spaces will be replaced with underscores '_' upon submission)")
            self.description.setPlaceholderText("date, client_id, project_tag ...etc")
            self.layout.addWidget(message)
            self.layout.addWidget(self.description)
        elif dialog_type.get("file_profile") is not None:
            message = QLabel("Unique Profile Name: (Any spaces will be replaced with underscores '_' upon submission)")
            self.description.setPlaceholderText("formal_report, invoice, client_report_2, ...etc")
            self.layout.addWidget(message)
            self.layout.addWidget(self.description)

        title = "Scanned Text Result."
        self.setWindowTitle(title)

        if dialog_type.get("parameter") is not None:
            message2 = QLabel("If scanned text produced acceptable results leave as is.")
            self.layout.addWidget(message2)
        elif dialog_type.get("file_profile") is not None:
            message2 = QLabel(f"If you are aware of the possible consequences, you can manually input text if scanned result is not as desired.")
            self.layout.addWidget(message2)
        elif dialog_type.get("project_number") is not None:
            message2 = QLabel(f"If project number produced acceptable results Continue on.\nOtherwise Cancel and try again by adjusting the selection area.")
            self.layout.addWidget(message2)

        self.text_input = QLineEdit()
        self.text_input.setText(self.found_text)
        self.layout.addWidget(self.text_input)
        
        if dialog_type.get("parameter") is not None:
            message3 = QLabel("If desired, enter a regex string here to perform a regex search on the found text.\nOtherwise ensure this line is left blank.")
            self.layout.addWidget(message3)

            self.regex = QLineEdit()
            self.regex.setPlaceholderText("Regex...")
            self.layout.addWidget(self.regex)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Confirm", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Cancel", QDialogButtonBox.RejectRole)
        if dialog_type.get("parameter") is not None:
            title = "Parameter Entry"
        elif dialog_type.get("file_profile") is not None:
            title = "File Profile Entry"
        elif dialog_type.get("project_number") is not None:
            title = "Project Number Entry"

        self.button_box.setWindowTitle(title)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)