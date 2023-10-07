from PySide6 import QtCore, QtGui, QtWidgets

from datetime import date

from models import main_model
from view_models import main_view_model, message_box_view_model
from views import message_box_view, navigation_view, stacked_view

from utils import path_utils, general_utils


class MainView(QtWidgets.QMainWindow):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()

        self.central_widget = QtWidgets.QWidget()

        self.main_view_model = main_view_model
        self.main_view_model.message_box_alert.connect(self.show_message_alert)

        self.stacked_view = stacked_view.StackedWidget(self.main_view_model)
        self.navigation_view = QtWidgets.QWidget()
        self.navigation_view.setLayout(
            navigation_view.NavigationView(self.main_view_model)
        )
        self.navigation_view.setProperty("class", "nav-widget")

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.navigation_view)
        self.main_layout.addWidget(self.stacked_view)
        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 1)

        self.copyright_label = QtWidgets.QLabel(
            f"© {date.today().year} Brandon Gorman. All rights reserved."
        )
        self.copyright_label.setProperty("class", "copyright-label")
        self.copyright_layout = QtWidgets.QHBoxLayout()
        self.copyright_layout.setContentsMargins(0, 0, 0, 0)
        self.copyright_layout.addWidget(self.copyright_label)
        self.copyright_layout.setAlignment(QtCore.Qt.AlignHCenter) # type: ignore
        self.copyright_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum # type: ignore
         )

        self.copyright_widget = QtWidgets.QWidget()
        self.copyright_widget.setLayout(self.copyright_layout)
        self.copyright_widget.setProperty("class", "copyright-label")

        self.central_layout = QtWidgets.QVBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.addLayout(self.main_layout)
        self.central_layout.setStretch(self.central_layout.indexOf(self.main_layout), 1)
        self.central_layout.addWidget(self.copyright_widget)

        self.central_widget.setLayout(self.central_layout)

        self.setCentralWidget(self.central_widget)
        self.navigation_view.setProperty("class", "nav-widget")
        screen = QtGui.QGuiApplication.primaryScreen().size()
        self.resize(screen.width() // 2, screen.height())
        self.main_view_model.window_size_update.connect(self.resize)

    def show_message_alert(self, message_box: general_utils.MessageBox):
        """Shows a message box alert to the user from given message box dict.

        Args:
            message_box (MessageBox): An object that encapsulates attributes and configurations for displaying a message box to the user.
        """
        self.message_box = message_box_view.MessageBoxView(
            message_box_view_model.MessageBoxViewModel(self.main_view_model, message_box)
        )
        result_index = self.message_box.exec_()
        # result = message_box_dict.get("button_roles")[result_index]
        self.main_view_model.message_box_handler(message_box.callback[result_index])


def main():
    app = QtWidgets.QApplication([])
    
    # Open the qss styles file and read in the css-alike styling code
    style_file_path = path_utils.resource_path("style/styles.qss")
    with open(style_file_path, "r") as f:
        style = f.read()

    # Set the stylesheet of the application
    app.setStyleSheet(style)
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(QtCore.Qt.gray))
    app.setPalette(palette)
    QtGui.QFontDatabase.addApplicationFont(path_utils.resource_path("assests/Roboto-Regular.ttf"))
    window = MainView(main_view_model.MainViewModel(main_model.MainModel()))
    window.setWindowTitle("PDF Flow")
    window.navigation_view.setProperty("class", "nav-widget")
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
