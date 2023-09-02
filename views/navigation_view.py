from PySide6 import QtWidgets

from view_models import main_view_model, navigation_view_model


class NavigationView(QtWidgets.QVBoxLayout):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self.view_model = navigation_view_model.NavigationViewModel(
            self.main_view_model)

        self.process_nav_button = QtWidgets.QPushButton()
        self.process_nav_button.setText("Process")

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

        self.loaded_files_button = QtWidgets.QPushButton()
        self.loaded_files_button.setText("Loaded Files: 0")

        self.processed_files_button = QtWidgets.QPushButton()
        self.processed_files_button.setText("Processed Files: 0")

        self.emailed_files_button = QtWidgets.QPushButton()
        self.emailed_files_button.setText("Emailed Files: 0")

        self.setSpacing(5)
        self.setContentsMargins(0, 100, 0, 0)

        self.addWidget(self.process_nav_button)
        self.addWidget(self.console_nav_button)
        self.addWidget(self.data_viewer_nav_button)
        self.addWidget(self.template_nav_button)
        self.addWidget(self.file_name_nav_button)
        self.addWidget(self.email_nav_button)

        self.addStretch()

        self.addWidget(self.loaded_files_button)
        self.addWidget(self.processed_files_button)
        self.addWidget(self.emailed_files_button)

        self.addSpacing(50)

        self.process_nav_button.setProperty(
            "id", self.indexOf(self.process_nav_button))
        self.console_nav_button.setProperty(
            "id", self.indexOf(self.console_nav_button))
        self.data_viewer_nav_button.setProperty(
            "id", self.indexOf(self.data_viewer_nav_button))
        self.template_nav_button.setProperty(
            "id", self.indexOf(self.template_nav_button))
        self.file_name_nav_button.setProperty(
            "id", self.indexOf(self.file_name_nav_button))
        self.email_nav_button.setProperty(
            "id", self.indexOf(self.email_nav_button))
        

        self.process_nav_button.setProperty("class", "nav-button")
        self.console_nav_button.setProperty("class", "nav-button")
        self.data_viewer_nav_button.setProperty("class", "nav-button")
        self.file_name_nav_button.setProperty("class", "nav-button")
        self.template_nav_button.setProperty("class", "nav-button")
        self.email_nav_button.setProperty("class", "nav-button")

        self.process_nav_button.clicked.connect(
            lambda: self.view_model.stacked_item_change(self.process_nav_button.property("id")))
        self.console_nav_button.clicked.connect(
            lambda: self.view_model.stacked_item_change(self.console_nav_button.property("id")))
        self.data_viewer_nav_button.clicked.connect(
            lambda: self.view_model.stacked_item_change(self.data_viewer_nav_button.property("id")))
        self.template_nav_button.clicked.connect(
            lambda: self.view_model.stacked_item_change(self.template_nav_button.property("id")))
        self.file_name_nav_button.clicked.connect(
            lambda: self.view_model.stacked_item_change(self.file_name_nav_button.property("id")))
        self.email_nav_button.clicked.connect(
            lambda: self.view_model.stacked_item_change(self.email_nav_button.property("id")))

        self.main_view_model.console_alerts_update.connect(
            lambda: self.console_nav_button.setText(f"Console ({self.main_view_model.console_alerts})"))
        self.main_view_model.loaded_files_count_update.connect(lambda: self.loaded_files_button.setText(
            f"Loaded Files: {self.main_view_model.loaded_files_count}"))
        self.main_view_model.processed_files_update.connect(lambda: self.processed_files_button.setText(
            f"Processed Files: {self.main_view_model.processed_files}"))
        self.main_view_model.emailed_files_count_update.connect(lambda: self.emailed_files_button.setText(
            f"Emailed Files: {self.main_view_model.emailed_files_count}"))
