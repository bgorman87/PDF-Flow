from PySide6 import QtWidgets
from view_models import data_viewer_view_model

class DataViewerView(QtWidgets.QWidget):
    def __init__(self, view_model: data_viewer_view_model.DataViewerViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel()
        self.label.setText("Data Viewer")
        self.main_layout.addWidget(self.label)
        self.setLayout(self.main_layout)