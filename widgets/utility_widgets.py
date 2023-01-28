from PySide6 import QtWidgets


class HorizontalLine(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.horizontal_layout = QtWidgets.QHBoxLayout()
        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.horizontal_layout.addWidget(self.line)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.horizontal_layout)
