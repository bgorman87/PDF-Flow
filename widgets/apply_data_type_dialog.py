from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QLineEdit

class ApplyFoundData(QDialog):
    """Dialog box class used to displays information for creating new profiles and appliyng paramaters"""    

    def __init__(self, coords, found_text, dialog_type="file_profile", parent=None):
        super(ApplyFoundData, self).__init__(parent)
        self.coords = coords
        self.found_text = found_text          

        self.button_box = QDialogButtonBox()
        self.button_box.addButton("Confirm", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Cancel", QDialogButtonBox.RejectRole)
        if dialog_type !="file_profile":
            title = "Date Information Entry"
        else:
            title = "File Profile Entry"
        self.button_box.setWindowTitle(title)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # TODO: Look into adjusting layout to look better
        self.layout = QVBoxLayout()
        
        self.description = QLineEdit()
        if dialog_type != "file_profile":
            message = QLabel("Data Description: (Any spaces will be replaced with underscores '_' upon submission)")
            self.description.setPlaceholderText("project_number, date, client_id ...etc")
        else:
            message = QLabel("Unique Profile Name: (Any spaces will be replaced with underscores '_' upon submission)")
            self.description.setPlaceholderText("formal_report, invoice, client_report_2, ...etc")
        self.layout.addWidget(message)
        self.layout.addWidget(self.description)
        message1 = QLabel("Scanned Text Result.")
        if dialog_type != "file_profile":
            message2 = QLabel("If scanned text produced acceptable results leave as is.")
        else:
            message2 = QLabel(f"If you are aware of the possible consequences, you can manually input text if scanned result is not as desired.")
        self.text_input = QLineEdit()
        self.text_input.setText(self.found_text)

        self.layout.addWidget(message1)
        self.layout.addWidget(message2)
        self.layout.addWidget(self.text_input)
        
        if dialog_type != "file_profile":
            message3 = QLabel("If scanned result not exactly as desired, regex string can be enetered.\nRegex search will occur on file scan if not left blank.")
            self.layout.addWidget(message3)

            self.regex = QLineEdit()
            self.regex.setPlaceholderText("Regex...")
            self.layout.addWidget(self.regex)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)