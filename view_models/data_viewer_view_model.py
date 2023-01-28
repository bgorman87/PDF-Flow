from PySide6 import QtCore
from view_models import main_view_model

class DataViewerViewModel(QtCore.QObject):
    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model