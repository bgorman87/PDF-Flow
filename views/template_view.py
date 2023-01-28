from PySide6 import QtWidgets
from view_models import template_view_model

class TemplateView(QtWidgets.QWidget):
    def __init__(self, view_model: template_view_model.TemplateViewModel):
        super().__init__()
        self.view_model = view_model
        self.main_layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel()
        self.label.setText("Template")
        self.main_layout.addWidget(self.label)
        self.setLayout(self.main_layout)