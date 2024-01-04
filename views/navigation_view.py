from PySide6 import QtCore, QtGui, QtWidgets

from view_models import main_view_model, navigation_view_model


class NavigationView(QtWidgets.QVBoxLayout):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self.view_model = navigation_view_model.NavigationViewModel(
            self.main_view_model
        )

        self.company_logo = QtWidgets.QLabel()
        self.company_logo.setProperty("class", "company-logo")
        self.company_logo.setPixmap(
            QtGui.QPixmap("assets/icons/englobe_logo.png").scaledToWidth(75)
        )
        self.company_logo.setAlignment(QtCore.Qt.AlignCenter)

        self.navigation_title = QtWidgets.QLabel()
        self.navigation_title.setText("Navigation")

        self.process_nav_button = QtWidgets.QPushButton()
        self.process_nav_button.setText("Process")
        self.view_model.currently_active_button = self.process_nav_button

        self.console_nav_button = QtWidgets.QPushButton()
        self.console_nav_button.setText("Console (0)")

        self.data_viewer_nav_button = QtWidgets.QPushButton()
        self.data_viewer_nav_button.setText("Project Data")

        self.template_nav_button = QtWidgets.QPushButton()
        self.template_nav_button.setText("Template")

        self.file_name_nav_button = QtWidgets.QPushButton()
        self.file_name_nav_button.setText("File Name")

        self.email_nav_button = QtWidgets.QPushButton()
        self.email_nav_button.setText("E-Mail")

        self.stats_title = QtWidgets.QLabel()
        self.stats_title.setText("Stats")

        self.loaded_files_button = QtWidgets.QPushButton()
        self.loaded_files_button.setText("Loaded Files: 0")

        self.processed_files_button = QtWidgets.QPushButton()
        self.processed_files_button.setText("Processed Files: 0")

        self.emailed_files_button = QtWidgets.QPushButton()
        self.emailed_files_button.setText("Emailed Files: 0")

        self.program_info_title = QtWidgets.QLabel()
        self.program_info_title.setText("Program Info")

        self.version_button = QtWidgets.QPushButton()
        self.version_button.setText(f"Version {self.main_view_model.version}")
        self.version_button.clicked.connect(self.open_documentation_link)

        self.feedback_button = QtWidgets.QPushButton()
        self.feedback_button.setText("Feedback")
        # Add a click event to open a mailto link to send feedback
        self.feedback_button.clicked.connect(
            lambda: self.view_model.open_feedback_link()
        )

        self.setSpacing(5)
        self.setContentsMargins(0, 0, 0, 0)

        self.addSpacing(25)
        self.addWidget(self.company_logo)
        self.addSpacing(25)

        self.layout_index_count = self.count()

        # self.addWidget(self.navigation_title)
        self.addWidget(self.process_nav_button)
        self.addWidget(self.console_nav_button)
        self.addWidget(self.data_viewer_nav_button)
        self.addWidget(self.template_nav_button)
        self.addWidget(self.file_name_nav_button)
        self.addWidget(self.email_nav_button)

        self.addStretch()

        # self.addWidget(self.stats_title)
        self.addWidget(self.loaded_files_button)
        self.addWidget(self.processed_files_button)
        self.addWidget(self.emailed_files_button)

        self.addSpacing(50)

        # self.addWidget(self.program_info_title)
        self.addWidget(self.version_button)
        self.addWidget(self.feedback_button)

        self.process_nav_button.setProperty(
            "id", self.indexOf(self.process_nav_button) - self.layout_index_count
        )
        self.console_nav_button.setProperty(
            "id", self.indexOf(self.console_nav_button) - self.layout_index_count
        )
        self.data_viewer_nav_button.setProperty(
            "id", self.indexOf(self.data_viewer_nav_button) - self.layout_index_count
        )
        self.template_nav_button.setProperty(
            "id", self.indexOf(self.template_nav_button) - self.layout_index_count
        )
        self.file_name_nav_button.setProperty(
            "id", self.indexOf(self.file_name_nav_button) - self.layout_index_count
        )
        self.email_nav_button.setProperty(
            "id", self.indexOf(self.email_nav_button) - self.layout_index_count
        )

        self.process_nav_button.setProperty("class", "nav-button-active")
        self.console_nav_button.setProperty("class", "nav-button")
        self.data_viewer_nav_button.setProperty("class", "nav-button")
        self.file_name_nav_button.setProperty("class", "nav-button")
        self.template_nav_button.setProperty("class", "nav-button")
        self.email_nav_button.setProperty("class", "nav-button")

        self.processed_files_button.setProperty("class", "stats-button")
        self.loaded_files_button.setProperty("class", "stats-button")
        self.emailed_files_button.setProperty("class", "stats-button")

        self.version_button.setProperty("class", "program-info-button")
        self.feedback_button.setProperty("class", "program-info-button")

        self.process_nav_button.clicked.connect(
            lambda: self.handle_nav_change(self.process_nav_button)
        )
        self.console_nav_button.clicked.connect(
            lambda: self.handle_nav_change(self.console_nav_button)
        )
        self.data_viewer_nav_button.clicked.connect(
            lambda: self.handle_nav_change(self.data_viewer_nav_button)
        )
        self.template_nav_button.clicked.connect(
            lambda: self.handle_nav_change(self.template_nav_button)
        )
        self.file_name_nav_button.clicked.connect(
            lambda: self.handle_nav_change(self.file_name_nav_button)
        )
        self.email_nav_button.clicked.connect(
            lambda: self.handle_nav_change(self.email_nav_button)
        )

        self.main_view_model.console_alerts_update.connect(
            lambda: self.console_nav_button.setText(
                f"Console ({self.main_view_model.console_alerts})"
            )
        )
        self.main_view_model.loaded_files_count_update.connect(
            lambda: self.loaded_files_button.setText(
                f"Loaded Files: {self.main_view_model.loaded_files_count}"
            )
        )
        self.main_view_model.processed_files_update.connect(
            lambda: self.processed_files_button.setText(
                f"Processed Files: {self.main_view_model.processed_files}"
            )
        )
        self.main_view_model.emailed_files_count_update.connect(
            lambda: self.emailed_files_button.setText(
                f"Emailed Files: {self.main_view_model.emailed_files_count}"
            )
        )

    def handle_nav_change(self, button: QtWidgets.QPushButton):
        """Handles the logic of switching current stack index"""

        self.view_model.currently_active_button.setProperty("class", "nav-button")
        self.view_model.currently_active_button.style().polish(
            self.view_model.currently_active_button
        )

        button.setProperty("class", "nav-button-active")
        button.style().polish(button)

        self.view_model.stacked_item_change(button)

    def open_documentation_link(self):
        """Opens the documentation link in the default browser."""

        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl("https://pdfflow.godevservices.com/")
        )
