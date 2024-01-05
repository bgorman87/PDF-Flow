from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QGroupBox, QFrame

from utils import text_utils


class HorizontalLine(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.horizontal_layout = QHBoxLayout()
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.horizontal_layout.addWidget(self.line)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.horizontal_layout)
        

class ROIGroupBox(QGroupBox):
    add_roi_signal = Signal()
    remove_roi_signal = Signal()
    process_method_changed = Signal()


    def __init__(self, title: str, roi_type:str='default'):
        super(ROIGroupBox, self).__init__(title)

        self.sample_values = []
        self.value_labels = []
        self.roi_type = roi_type
        self.values_type = None
        self.extra_value = None
        self.method = None
        self.previous_method = None

        self.values_layout = QVBoxLayout(self)

        # Processing Method Dropdown
        self.processing_method_dropdown = QComboBox()
        self.options = [
            {"text": "Choose an option", "data": None},
            {"text": "Maximum Value", "data": "max"},
            {"text": "Minimum Value", "data": "min"},
            {"text": "Average (Mean)", "data": "mean"},
            {"text": "Middle Value (Median)", "data": "median"},
            {"text": "Index of Minimum Value", "data": "min_index"},
            {"text": "Index of Maximum Value", "data": "max_index"},
            {"text": "Number of Items (Length)", "data": "length"},
            {"text": "Total Sum", "data": "sum"},
            {"text": "First Value", "data": "first_value"},
            {"text": "Last Value", "data": "last_value"},
        ]
        for option in self.options:
            self.processing_method_dropdown.addItem(option["text"], option["data"])

        if roi_type == 'roi2':
            self.processing_method_dropdown.addItem("Value at position", "index")

        self.values_layout.addWidget(QLabel("Processing Method"))
        self.values_layout.addWidget(self.processing_method_dropdown)

        self.extra_value_label = QLabel()
        self.extra_value_label.setText("Returned Value: ")
        self.values_layout.addWidget(self.extra_value_label)

        # Connect signals
        self.processing_method_dropdown.currentIndexChanged.connect(self._update_display)

        self.values_layout.addWidget(HorizontalLine())

         # Add the ROI button
        self.add_roi_btn = QPushButton("Add ROI")
        if self.roi_type == 'roi1':
            self.add_roi_btn.clicked.connect(self._add_roi)
            self.values_layout.addWidget(self.add_roi_btn)
        else:
            self.add_roi_btn.setEnabled(False)

        # Remove the ROI button
        self.remove_roi_btn = QPushButton("Remove ROI")
        if self.roi_type == 'roi2':
            self.remove_roi_btn.clicked.connect(self._remove_roi)
            self.values_layout.addWidget(self.remove_roi_btn)
        else:
            self.remove_roi_btn.setEnabled(False)

    def _add_roi(self):
        self.add_roi_btn.setDisabled(True)
        self.add_roi_signal.emit()
        self.processing_method_dropdown.addItem("Value at position", "index")

    def _remove_roi(self):
        self.remove_roi_signal.emit()

    def set_sample_values(self, sample_values, sample_value_type=float):
        
        self.values_type = sample_value_type
        for label in self.value_labels:
            label.deleteLater()
        self.value_labels.clear()

        self.sample_values = sample_values
        insert_position = 0
        for value in self.sample_values:
            label = QLabel(str(value))
            self.value_labels.append(label)
            self.values_layout.insertWidget(insert_position, label)
            insert_position += 1

        self.values_layout.insertWidget(insert_position, HorizontalLine())

    def reset_label_formats(self):
        for label in self.value_labels:
            label.setStyleSheet("font-weight: normal;")

    def _update_display(self):
        self.previous_method = self.method
        self.method = self.processing_method_dropdown.currentData()
        
        self.reset_label_formats()   

        if self.method == "index":
            self.extra_value = None
            self.extra_value_label.setText("Returned Value: ")

        elif self.method == "max":
            self.extra_value = max(self.sample_values)
            result_idx = self.sample_values.index(self.extra_value)
            self.value_labels[result_idx].setStyleSheet("font-weight: bold; color: #66bb6a;")
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "min":
            self.extra_value = min(self.sample_values)
            result_idx = self.sample_values.index(self.extra_value)
            self.value_labels[result_idx].setStyleSheet("font-weight: bold; color: #66bb6a;")
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "mean":
            self.extra_value = sum(self.sample_values) / len(self.sample_values)
            if self.values_type == int:
                self.extra_value = int(self.extra_value)
            else:
                precision = text_utils.determine_precision(self.sample_values)
                self.extra_value = round(self.extra_value, precision)
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "median":
            sorted_values = sorted(self.sample_values)
            mid_idx = len(sorted_values) // 2
            if len(sorted_values) % 2 == 0:  # Even number of items
                self.extra_value = (sorted_values[mid_idx - 1] + sorted_values[mid_idx]) / 2
                if self.values_type == float:
                    precision = text_utils.determine_precision(self.sample_values)
                    self.extra_value = round(self.extra_value, precision)
            else:  # Odd number of items
                self.extra_value = sorted_values[mid_idx]
                result_idx = self.sample_values.index(self.extra_value)
                self.value_labels[result_idx].setStyleSheet("font-weight: bold; color: #66bb6a;")
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "min_index":
            result_idx = self.sample_values.index(min(self.sample_values))
            self.extra_value = result_idx
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "max_index":
            result_idx = self.sample_values.index(max(self.sample_values))
            self.extra_value = result_idx
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "length":
            self.extra_value = len(self.sample_values) - 1
            self.extra_value_label.setText(f"Returned Value: {len(self.sample_values)}")

        elif self.method == "sum":
            self.extra_value = sum(self.sample_values)
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "first_value":
            result_idx = 0
            self.extra_value = self.sample_values[result_idx]
            self.value_labels[result_idx].setStyleSheet("font-weight: bold; color: #66bb6a;")
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        elif self.method == "last_value":
            result_idx = len(self.sample_values) - 1
            self.extra_value = self.sample_values[result_idx]
            self.value_labels[result_idx].setStyleSheet("font-weight: bold; color: #66bb6a;")
            self.extra_value_label.setText(f"Returned Value: {self.extra_value}")

        else:
            self.extra_value = None
            self.extra_value_label.setText("Returned Value: ")

        self.process_method_changed.emit()
