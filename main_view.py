from PySide6 import QtCore, QtGui, QtWidgets

from models import main_model
from view_models import main_view_model, message_box_view_model
from views import message_box_view, navigation_view, stacked_view


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
            "© 2023 Brandon Gorman. All rights reserved."
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
        self.center_application(screen)

    def show_message_alert(self, message_box_dict: dict):
        self.message_box = message_box_view.MessageBoxView(
            message_box_view_model.MessageBoxViewModel(self.main_view_model, message_box_dict)
        )
        result_index = self.message_box.exec_()
        # result = message_box_dict.get("button_roles")[result_index]
        self.main_view_model.message_box_handler(message_box_dict["callback"][result_index])

    def center_application(self, screen):
        # get the size of the main window
        windowWidth = self.frameGeometry().width()
        windowHeight = self.frameGeometry().height()

        # calculate the top-left corner of the main window
        x = screen.width() // 2 - windowWidth // 2
        y = screen.height() // 2 - windowHeight // 2

        # set the position of the main window
        self.move(x, y)
        self.resize(screen.width() // 2, screen.height() / 1.1)

    def resize_window(self, size: tuple):
        self.resize(size)

def main():
    app = QtWidgets.QApplication([])
    # # Open the qss styles file and read in the css-alike styling code
    with open("style/styles.qss", "r") as f:
        style = f.read()

    # Set the stylesheet of the application
    app.setStyleSheet(style)
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(QtCore.Qt.white))  # type: ignore
    app.setPalette(palette)
    QtGui.QFontDatabase.addApplicationFont("assests/Roboto-Regular.ttf")
    window = MainView(main_view_model.MainViewModel(main_model.MainModel()))
    window.setWindowTitle("PDF Processor")
    window.navigation_view.setProperty("class", "nav-widget")
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
