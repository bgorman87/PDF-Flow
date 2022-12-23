from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QProgressDialog, QMessageBox

class LoadingWidget(QProgressDialog):
    def __init__(self,title, text, start=0, end=100, val=0):
        super().__init__(parent=None)
        self.setWindowTitle(title)  
        self.setLabelText(text)  
        self.setMinimum(start)
        self.setMaximum(end)
        self.setWindowModality(Qt.WindowModal)
        self.setAutoClose(True)
        self.setAutoReset(True)
        self.setValue(val)
        self.show()

    def update_val(self, value):
        self.setValue(value)

   