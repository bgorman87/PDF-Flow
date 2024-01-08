from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDialogButtonBox,
    QLineEdit,
    QFrame,
    QComboBox,
    QToolButton,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Signal
from widgets import utility_widgets
from utils import text_utils


class ApplyFoundData(QDialog):
    """Dialog box class used to display information for creating new profiles and applying parameters"""
    add_roi_signal = Signal()
    remove_roi_signal = Signal()

    def __init__(
        self,
        coords,
        found_text,
        dialog_type={"parameter": False, "profile": False, "project_number": False},
        confirm_callback=None,
        cancel_callback=None,
        parent=None,
    ):
        super(ApplyFoundData, self).__init__(parent)

        self.coords = coords
        self.primary_text = found_text
        self.secondary_text = ""
        self.layout = QVBoxLayout()
        self.description = QLineEdit()
        self.roi1 = None
        self.roi2 = None
        self.comparison_group = None
        self.comparison_result_label = None
        self.comparison_result_label = None
        self.confirm_callback = confirm_callback
        self.cancel_callback = cancel_callback

        self.button_box = QDialogButtonBox()
        self.confirm_button = self.button_box.addButton("Confirm", QDialogButtonBox.AcceptRole)
        self.button_box.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.button_box.setWindowTitle(self.windowTitle())
        self.button_box.accepted.connect(self.confirm_callback)
        self.button_box.rejected.connect(self.cancel_callback)

        # Determine which type of dialog to display and call corresponding method
        if dialog_type.get("parameter"):
            self._setup_parameter_dialog()
        elif dialog_type.get("profile"):
            self._setup_profile_dialog()
        elif dialog_type.get("project_number"):
            self._setup_project_number_dialog()

        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def _create_advanced_section(self):
        self.advanced_frame = QFrame()
        self.advanced_frame.setFrameShape(QFrame.StyledPanel)
        self.advanced_frame.setFrameShadow(QFrame.Plain)
        self.advanced_frame.setHidden(True)

        self.advanced_layout = QVBoxLayout()

        # ROI Layout
        self.roi_layout = QHBoxLayout()
        self.roi1 = utility_widgets.ROIGroupBox('ROI 1', 'roi1')
    
        # Process the text and determine the type of values
        lines = self.primary_text.split("\n")
        self.sample_values, self.sample_value_type = text_utils.process_and_determine_type([line.strip() for line in lines])

        self.roi1.set_sample_values(self.sample_values, self.sample_value_type)

        self.roi_layout.addWidget(self.roi1)

        self.advanced_layout.addLayout(self.roi_layout)

        self.roi1.add_roi_signal.connect(lambda: self.add_roi_signal.emit())
        self.roi1.process_method_changed.connect(lambda: self.roi_process_change(self.roi1))
        
        # Horizontal separator line
        # self.advanced_layout.addWidget(utility_widgets.HorizontalLine())

        # Regex Input
        self.regex_layout = QHBoxLayout()
        self.regex_layout.addWidget(QLabel("Regex Pattern:"))
        self.regex = QLineEdit()
        self.regex.setPlaceholderText("Regex...")
        self.regex_layout.addWidget(self.regex)
        # self.advanced_layout.addLayout(self.regex_layout)

        self.advanced_frame.setLayout(self.advanced_layout)
        return self.advanced_frame

    def roi_process_change(self, roi: utility_widgets.ROIGroupBox):
        if roi.roi_type == 'roi1':
            other_roi = self.roi2
        else:
            other_roi = self.roi1
            
        if roi.method == "index":
            self._handle_index_selected(roi, other_roi)
        elif roi.previous_method == "index":
            self._restore_roi_options(other_roi)

        if self.roi2 is not None:
            self.process_comparison_index_change()

    def process_comparison_index_change(self):
        self.comparison_result = self.compare_rois()
        self.comparison_result_label.setText("Comparison Result: " + str(self.comparison_result))

    def _handle_index_selected(self, roi, other_roi):
        self.comparison_operator_dropdown.setCurrentIndex(self.comparison_operator_dropdown.findData("equal"))
        self.comparison_group.setEnabled(False)
        
        self.options = [
            {"text": "Choose an option", "data": None},
            {"text": "Index of Minimum Value", "data": "min_index"},
            {"text": "Index of Maximum Value", "data": "max_index"},
            {"text": "Number of Items (Length)", "data": "length"},
        ]
        
        if other_roi is not None:
            self._update_roi_options(other_roi, self.options)

    def _restore_roi_options(self, roi: utility_widgets.ROIGroupBox):
        if self.comparison_group is not None:
            self.comparison_group.setEnabled(True)
        if roi is not None:
            self._update_roi_options(roi, roi.options)

    def _update_roi_options(self, roi: utility_widgets.ROIGroupBox, options):
        roi.process_method_changed.disconnect()
        roi.processing_method_dropdown.clear()
        for option in options:
            roi.processing_method_dropdown.addItem(option["text"], option["data"])

        # For any roi, add "index" option only if roi2 exists, and if one of the roi isn't already set to "index"
        if self.roi2 is not None and not (self.roi1.method == "index" or self.roi2.method == "index"):
            roi.processing_method_dropdown.addItem("Value at position", "index")
        
        roi.process_method_changed.connect(lambda: self.roi_process_change(roi))

    def set_secondary_values(self, secondary_text: str):
        self.secondary_text = secondary_text

    def show_roi2_and_comparison(self):

        # Comparison Group
        self.comparison_group = QGroupBox("Comparison")
        comparison_layout = QVBoxLayout()
        self.comparison_operator_dropdown = QComboBox()
        mathematical_operators = [
            {"text": "Choose an option", "data": None},
            {"text": "Max", "data": "max"},
            {"text": "Min", "data": "min"},
            {"text": "Equal To", "data": "equal"},
        ]
        for operator in mathematical_operators:
            self.comparison_operator_dropdown.addItem(operator["text"], operator["data"])

        self.comparison_operator_dropdown.currentIndexChanged.connect(self.process_comparison_index_change)

        comparison_layout.addStretch(1)
        comparison_layout.addWidget(self.comparison_operator_dropdown)
        comparison_layout.addStretch(1)

        self.comparison_result_label = QLabel("Comparison Result: ")

        comparison_layout.addWidget(self.comparison_result_label)
        self.comparison_group.setLayout(comparison_layout)

        self.roi2 = utility_widgets.ROIGroupBox('ROI 2', 'roi2')
        # Process the text and determine the type of values
        lines = self.secondary_text.split("\n")
        processed_roi2_values, roi2_values_type = text_utils.process_and_determine_type([line.strip() for line in lines])
        self.roi2.set_sample_values(processed_roi2_values)
        self.roi2.remove_roi_signal.connect(self.remove_roi2_and_comparison)
        self.roi2.process_method_changed.connect(lambda: self.roi_process_change(self.roi2))

        self.roi_layout.addWidget(self.comparison_group)
        self.roi_layout.addWidget(self.roi2)

    def remove_roi2_and_comparison(self):

        if not hasattr(self, 'roi_layout'):
            return

        if self.roi_layout.indexOf(self.comparison_group) != -1:
            self.roi_layout.removeWidget(self.comparison_group)
            self.comparison_group.setVisible(False)
            self.comparison_group.deleteLater()
            self.comparison_group = None
        
        if self.roi_layout.indexOf(self.roi2) != -1:
            self.roi_layout.removeWidget(self.roi2)
            self.roi2.setVisible(False)
            self.roi2.remove_roi_signal.disconnect()
            self.roi2.process_method_changed.disconnect()
            self.roi2.deleteLater()
            self.roi2 = None
            self.secondary_text = ""

        self._restore_roi_options(self.roi1)

        self.remove_roi_signal.emit()

        self.roi1.add_roi_btn.setEnabled(True)
        self.advanced_frame.adjustSize()
        self.adjustSize()

    def compare_rois(self):
        roi1_value = self.roi1.extra_value
        roi2_value = self.roi2.extra_value

        # Check if either ROI value is None and its corresponding method is not set to "index"
        # If either is true, then it hasn't been selected yet so don't compare 
        if (roi1_value is None and self.roi1.method !="index") or (roi2_value is None and self.roi2.method !="index"):
            return

        # If any ROI has chosen "index", then fetch the actual value from the opposite ROI list.
        if self.roi1.method == "index":
            try:
                roi1_value = self.roi1.sample_values[roi2_value]
                self.roi1.extra_value = roi1_value
                self.roi1.reset_label_formats()
                self.roi1.value_labels[roi2_value].setStyleSheet("font-weight: bold; color: #66bb6a;")
                return roi1_value
            except IndexError:
                message_box = QMessageBox()
                message_box.setWindowTitle("Error")
                message_box.setText("Choices for ROI 1 and ROI 2 resulted in an invalid number. Please review before continuing.")
                message_box.exec()

        elif self.roi2.method == "index":
            try:
                roi2_value = self.roi2.sample_values[roi1_value]
                self.roi2.extra_value = roi2_value
                self.roi2.reset_label_formats()
                self.roi2.value_labels[roi1_value].setStyleSheet("font-weight: bold; color: #66bb6a;")
                return roi2_value
            except IndexError:
                message_box = QMessageBox()
                message_box.setWindowTitle("Error")
                message_box.setText("Choices for ROI 1 and ROI 2 resulted in an invalid number. Please review before continuing.")
                message_box.exec()

    
        # Extract the chosen comparison operation
        comparison_operator = self.comparison_operator_dropdown.currentData()

        # Perform the comparison based on the selected operator
        if comparison_operator == "equal":
            result = roi1_value == roi2_value
        elif comparison_operator == "min":
            result = min(roi1_value, roi2_value)
        elif comparison_operator == "max":
            result = max(roi1_value, roi2_value)
        else:
            result = ""

        return result


    def _setup_parameter_dialog(self):
        self.confirm_button.setEnabled(False)
        self.message_layout = QHBoxLayout()
        message = QLabel("Data Description:<span style='color: red;'>*</span>")
        self.description.setPlaceholderText("date, client_id, project_tag ...etc")
        self.description.setMinimumSize(250, 0)
        self.description.textChanged.connect(self.handle_description_change)
        self.message_layout.addWidget(message)
        self.message_layout.addWidget(self.description)
        self.layout.addLayout(self.message_layout)

        self.scanned_text_layout = QHBoxLayout()
        message2 = QLabel("Scanned Text:")
        self.text_input = QLineEdit(self.primary_text)
        self.text_input.setEnabled(False)
        self.scanned_text_layout.addWidget(message2)
        self.scanned_text_layout.addWidget(self.text_input)
        self.layout.addLayout(self.scanned_text_layout)

        # Advanced section
        self.advanced_toggle_button = QToolButton()
        self.advanced_toggle_button.setText("Advanced ▼")
        self.advanced_toggle_button.setCheckable(True)
        self.advanced_toggle_button.toggled.connect(self._toggle_advanced_section)
        self.layout.addWidget(self.advanced_toggle_button)

        self.layout.addWidget(self._create_advanced_section())

        self.setWindowTitle("Parameter Entry")

    def handle_description_change(self, text):
        if text:
            self.confirm_button.setEnabled(True)
            self.confirm_button.setToolTip("")
        else:
            self.confirm_button.setEnabled(False)
            self.confirm_button.setToolTip("Please enter a description")

    def _toggle_advanced_section(self, checked):
        if checked:
            self.advanced_toggle_button.setText("Advanced ▲")
            self.advanced_frame.setHidden(False)
            for index in range(self.scanned_text_layout.count()):
                widget = self.scanned_text_layout.itemAt(index).widget()
                if widget:  # check if it's really a widget
                    widget.hide()
        else:
            self.advanced_toggle_button.setText("Advanced ▼")
            self.advanced_frame.setHidden(True)
            for index in range(self.scanned_text_layout.count()):
                widget = self.scanned_text_layout.itemAt(index).widget()
                if widget:  # check if it's really a widget
                    widget.show()
        self.adjustSize()

    def _setup_profile_dialog(self):
        self.confirm_button.setEnabled(False)
        message = QLabel(
            "Unique Profile Name:<span style='color: red;'>*</span>"
        )
        self.description.setPlaceholderText(
            "formal_report, invoice, client_report_2, ...etc"
        )
        self.description.textChanged.connect(self.handle_description_change)
        self.layout.addWidget(message)
        self.layout.addWidget(self.description)

        message2 = QLabel(
            f"If you are aware of the possible consequences, you can manually input text if scanned result is not as desired."
        )
        self.layout.addWidget(message2)

        self.text_input = QLineEdit(self.primary_text)
        self.layout.addWidget(self.text_input)

        self.setWindowTitle("File Profile Entry")

    def _setup_project_number_dialog(self):
        message2 = QLabel(
            f"If project number produced acceptable results Continue on.\nOtherwise Cancel and try again by adjusting the selection area."
        )
        self.layout.addWidget(message2)
        self.text_input = QLineEdit(self.primary_text)
        self.layout.addWidget(self.text_input)

        self.setWindowTitle("Project Number Entry")
