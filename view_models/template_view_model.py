import collections
import io
from typing import NamedTuple

import pdf2image
from PySide6 import QtCore, QtWidgets

from functions import analysis
from view_models import main_view_model
from widgets import apply_data_type_dialog, file_template_creation, loading_widget


class TemplateViewModel(QtCore.QObject):

    project_number_status_update = QtCore.Signal()
    unique_parameter_status_update = QtCore.Signal()
    loaded_profile_label_update = QtCore.Signal()
    unique_file_identifier_button_status = QtCore.Signal()
    template_pixmap_update = QtCore.Signal()
    profile_file_loaded_status = QtCore.Signal()
    rects_found = QtCore.Signal()

    def __init__(self, main_view_model: main_view_model.MainViewModel):
        super().__init__()
        self.main_view_model = main_view_model
        self._project_button_enabled = False
        self._template_id_button_enabled = False
        self._loaded_profile_label_text = ""
        self._unique_file_id_button_enabled = False
        self._parameter_button_enabled = False
        self._image_jpeg = None
        self._img_byte_arr = None
        self._current_file_profile = 0
        self._parameter_rects = None
        self._profile_rect = None
        self._file_profile_path = ""
        self._profile_file_loaded = False

    def file_profile_template_dialog(self):
        """Opens dialog to choose files"""
        self._current_file_profile = 0
        # TODO: Update default search location before creating prod file

        self._file_profile_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            caption="Select a PDF To Use As Template", filter="PDF (*.pdf)"
        )
        if self._file_profile_path:
            self._thread_pool = QtCore.QThreadPool()
            self._loaded_profile_label_text = ""
            self.loaded_profile_label_update.emit()
            self.progress_popup = loading_widget.LoadingWidget(
                title="Template Check", text="Comparing file to existing profiles..."
            )
            self.analyze_worker = analysis.WorkerAnalyzeThread(
                file_name=self._file_profile_path,
                template=True,
                main_view_model=self.main_view_model
            )
            self.analyze_worker.signals.analysis_progress.connect(
                self.evt_loading_widget_progress
            )
            self.analyze_worker.signals.analysis_result.connect(
                self.evt_analyze_complete)
            self._thread_pool.start(self.analyze_worker)

    def evt_loading_widget_progress(self, value):
        self.progress_popup.update_val(value)

    def evt_analyze_complete(self, file_type: int):
        self._unique_file_id_button_enabled = True
        self.unique_file_identifier_button_status.emit()

        if not file_type or file_type[0] == 0:  # No file type detected therefore new template
            print("no file type found")
            self._project_button_enabled = False
            self.project_number_status_update.emit()

            self._parameter_button_enabled = False
            self.unique_parameter_status_update.emit()
            self.update_template_pixmap()
            return

        self._project_button_enabled = True
        self.project_number_status_update.emit()

        self._parameter_button_enabled = True
        self.unique_parameter_status_update.emit()

        profile_name = self.main_view_model.fetch_profile_description_by_profile_id(
            file_type[0])

        self._current_file_profile = file_type[0]
        self._loaded_profile_label_text = profile_name
        self.loaded_profile_label_update.emit()
        self.update_template_pixmap()
        self.paint_existing_data_rects(profile_id=file_type[0])

    @property
    def project_button_enabled(self) -> bool:
        return self._project_button_enabled

    @property
    def parameter_button_enabled(self) -> bool:
        return self._parameter_button_enabled

    @property
    def loaded_profile_label_text(self) -> str:
        return self._loaded_profile_label_text

    @property
    def unique_file_id_button_enabled(self) -> bool:
        return self._unique_file_id_button_enabled

    def update_template_pixmap(self):
        """Displays PDF file to be used for updating/creating a file_profile"""

        self._image_jpeg = pdf2image.convert_from_path(
            self._file_profile_path,
            fmt="jpeg",
            poppler_path=analysis.poppler_path,
            single_file=True,
        )
        self._img_byte_arr = io.BytesIO()
        self._image_jpeg[0].save(self._img_byte_arr, format="jpeg")
        self._img_byte_arr = self._img_byte_arr.getvalue()

        self.template_pixmap_update.emit()
        self._profile_file_loaded = True

    def update_window_size_from_widgets(self, template_widget: file_template_creation.TemplateWidget, *widgets: QtWidgets.QWidget):
        """Scales the window size according to the template widget and any oither vertically aldigned widgets passed to function.
        """

        updated_width = template_widget.scaled_width() + 25
        updated_height = template_widget.scaled_height() + 25
        for widget in widgets:
            updated_height += widget.height()

        self.main_view_model.update_window_size(
            int(updated_width), int(updated_height))

    def paint_existing_data_rects(self, profile_id: int):
        """Draws bounding boxes on top of loaded template file for user to see which data is already being analyzed for each profile"""

        self._parameter_rects = self.main_view_model.fetch_parameter_rects_and_desc(
            profile_id)
        self._profile_rect = self.main_view_model.fetch_profile_rect_and_desc(
            profile_id)

        if self._parameter_rects or self._profile_rect:
            self.rects_found.emit()

    @property
    def parameter_rects(self):
        return self._parameter_rects

    @property
    def profile_rect(self):
        return self._profile_rect

    @property
    def img_byte_array(self) -> io.BytesIO:
        return self._img_byte_arr

    @property
    def pil_image(self):
        return self._image_jpeg[0]

    def template_button_guard(self, template_display: file_template_creation.TemplateWidget) -> bool:
        """Checks if profile identifer can begin to be processed

        Args:
            template_display (file_template_creation.TemplateWidget): Template widget holding rect and text info

        Returns:
            bool: True if identier can be procssed, False if not
        """
        # If there is no rect started then nothing to find
        if template_display.begin.isNull():
            return False

        # If a pdf file isnt opened, then warn user and return
        if not self._profile_file_loaded:

            message_box_window_title = "No Profile Loaded"
            severity_icon = QtWidgets.QMessageBox.Information
            text_body = "You must first select a template file to open."
            buttons = [QtWidgets.QPushButton("Close")]
            button_roles = [QtWidgets.QMessageBox.RejectRole]
            callback = [None,]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }

            self.main_view_model.display_message_box(message_box_dict)
            return False

        # If there is no bounding box, let user know to draw one
        if template_display.begin.isNull():
            message_box_window_title = "Select Identifier"
            severity_icon = QtWidgets.QMessageBox.Information
            text_body = "Use the mouse to click and drag a bounding box around the desired profile identifier."
            buttons = [QtWidgets.QPushButton("Close")]
            button_roles = [QtWidgets.QMessageBox.RejectRole]
            callback = [None,]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }

            self.main_view_model.display_message_box(message_box_dict)
            return False

        # Bounding box can be too small and cause issues when analyzing text
        # If width and height less than 5 pixels, warn user and return
        if template_display.image_area_too_small:
            message_box_window_title = "Area Too Small"
            severity_icon = QtWidgets.QMessageBox.Information
            text_body = "Data area too small. Please choose a larger area."
            buttons = [QtWidgets.QPushButton("Close")]
            button_roles = [QtWidgets.QMessageBox.RejectRole]
            callback = [None,]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }

            self.main_view_model.display_message_box(message_box_dict)
            return False

        return True

    def apply_template_property(self, property_type: str, template_display: file_template_creation.TemplateWidget):
        """Handles creating a new file_profile based off of the bounding box for identifiable text"""

        # Check if rect and PDF are properly set-up for applying a profile id
        if not self.template_button_guard(template_display=template_display):
            return

        # Make sure the file_profile_field is not left blank
        # Display an error if left blank and bring the button box back up to retry.
        # If cancelled or requirements met, exit loop

        self.apply_template_property_dialog = apply_data_type_dialog.ApplyFoundData(
            template_display.true_coords(),
            template_display.found_text,
            dialog_type={property_type: True},
        )

        if not self.apply_template_property_dialog.exec():
            return

        name = (
            self.apply_template_property_dialog.description.text()
            .strip()
            .lower()
            .replace(" ", "_")
        )

        # Get a profile id or paramater id for the input
        # If an id exists then the name given is already in use
        db_id = None
        if property_type == "profile":
            db_id = self.main_view_model.fetch_profile_id_by_profile_name(
                profile_name=name)
        elif property_type == "parameter":
            db_id = self.main_view_model.fetch_parameter_id_by_name_and_profile_id(
                profile_id=self._current_file_profile, parameter_name=name)
        if property_type == "project_number":
            name = property_type

        # Check if user filled in profile_name and if its not already used
        # if so display message to user and use this function as a callback to bring it back up
        if name == "" or db_id is not None or ("project_number" == name.lower() and property_type != "project_number"):
            if name == "":
                message_box_window_title = "No Name"
                text_body = "Please enter a description/name."
            elif db_id is not None:
                message_box_window_title = "Name Not Unique"
                text_body = "Description/name already used for this profile. Please enter a unique value."
            else:
                message_box_window_title = "Reserved Name"
                text_body = "project_number is a reserved template keyword. To set the project_number paramater, use the 'Apply Project Number' button."
            severity_icon = QtWidgets.QMessageBox.Critical
            buttons = ["Close",]
            button_roles = [QtWidgets.QMessageBox.RejectRole,]
            callback = [lambda: self.apply_template_property(
                property_type=property_type, template_display=template_display),]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }
            self.main_view_model.display_message_box(message_box_dict)
            return

        [x_1, x_2, y_1, y_2] = template_display.true_coords()

        identifier = (
            self.apply_template_property_dialog.text_input.text().replace(
                "\n", " "
            )
        )
        if property_type == "profile":
            if not self.profile_conflict(identifier=identifier, name=name, x_1=x_1, x_2=x_2, y_1=y_1, y_2=y_2):
                self.add_new_profile(
                    profile_identifier=identifier,
                    profile_name=name,
                    x_1=x_1,
                    x_2=x_2,
                    y_1=y_1,
                    y_2=y_2,
                )
        else:

            if property_type == "parameter":
                regex = self.apply_template_property_dialog.regex.text()
                if not regex:
                    regex = None
            else:
                regex = None

            example_text = self.apply_template_property_dialog.text_input.text(
            ).strip().replace(" ", "-").replace("---", "-").replace("--", "-")
            example_text = self.main_view_model.scrub(example_text)
            self.add_new_parameter(
                profile_id=self._current_file_profile,
                parameter_name=name,
                regex=regex,
                x_1=x_1,
                x_2=x_2,
                y_1=y_1,
                y_2=y_2,
                example=example_text,
            )

    def profile_conflict(self, identifier: str, name: str, x_1: int, x_2: int, y_1: int, y_2: int) -> bool:
        # check if identiying text can be found in any of the existing profiles
        # taking into account new line chars. New line chars get saved into db as spaces
        # so convert detected text and check against db value
        unique_texts = self.main_view_model.fetch_all_profile_template_info()

        indentifier_text_found = False
        for profile_id, unique_text, profile_name in unique_texts:
            if (
                identifier.replace(
                    "\n", " ").strip().lower()
                in unique_text.replace("\n", " ").strip().lower()
                or unique_text.replace("\n", " ").strip().lower()
                in identifier.replace("\n", " ")
                .strip()
                .lower()
            ):
                indentifier_text_found = True
                break

        # if identifier already in database, check if current rect bounds intersects with matching profile entry
        identifier_intersects = False
        if indentifier_text_found:
            [db_x_1, db_x_2, db_y_1, db_y_2] = self.main_view_model.fetch_profile_rectangle_bounds_by_profile_id(
                profile_id=profile_id)

            RECTANGLE = collections.namedtuple("RECTANGLE", "x1 x2 y1 y2")
            current_box = RECTANGLE(x_1, x_2, y_1, y_2)
            found_box = RECTANGLE(db_x_1, db_x_2, db_y_1, db_y_2)

            if self.intersects_or_enclosed(current_box, found_box):
                identifier_intersects = True

        # If identifer text found and intersects warn user
        if indentifier_text_found and identifier_intersects:

            message_box_window_title = "Problematic Text and Location"
            severity_icon = QtWidgets.QMessageBox.Warning
            text_body = f"Potential profile conflict:\
                    \n\nThe location you chose produces identifying text '{identifier}'.\
                    \nExisting profile with name '{name}' has identidying text '{unique_text}' near the same location.\
                    \n\nIf you continue, these profiles may get mistaken for eachother during normal processing\
                    \n\nSelect Continue to add entry into database anyways \
                    \nSelect Cancel to choose another unique identifier"
            buttons = [QtWidgets.QPushButton(
                "Continue"), QtWidgets.QPushButton("Cancel")]
            button_roles = [QtWidgets.QMessageBox.YesRole,
                            QtWidgets.QMessageBox.RejectRole]
            callback = [
                lambda: self.add_new_profile(
                    profile_identifier=identifier,
                    profile_name=name,
                    x_1=x_1,
                    x_2=x_2,
                    y_1=y_1,
                    y_2=y_2
                ),
                None,
            ]
            message_box_dict = {
                "title": message_box_window_title,
                "icon": severity_icon,
                "text": text_body,
                "buttons": buttons,
                "button_roles": button_roles,
                "callback": callback
            }
            self.main_view_model.display_message_box(message_box_dict)
            return True

        return False

    def add_new_parameter(self, profile_id: int, parameter_name: str, regex: str, x_1: int, x_2: int, y_1: int, y_2: int, example: str):
        self.main_view_model.add_new_parameter(
            profile_id=profile_id,
            parameter_name=parameter_name,
            regex=regex,
            x_1=x_1,
            x_2=x_2,
            y_1=y_1,
            y_2=y_2,
            example=example,
        )
        self.paint_existing_data_rects(profile_id=profile_id)
        # TODO: add function here to update parameter list  in settings if currently
        # selected profile in settings is the one being updated.
        # self.main_view_model.parameter_update_list.emit(profile_id)

    def add_new_profile(self, profile_identifier: str, profile_name: str, x_1: int, x_2: int, y_1: int, y_2: int):
        self.main_view_model.add_new_profile(
            profile_identifier=profile_identifier,
            profile_name=profile_name,
            x_1=x_1,
            x_2=x_2,
            y_1=y_1,
            y_2=y_2,
        )

        self._project_button_enabled = True
        self.project_number_status_update.emit()

        self._parameter_button_enabled = True
        self.unique_parameter_status_update.emit()

        profile_id = self.main_view_model.fetch_profile_id_by_profile_name(
            profile_name=profile_name)
        self._current_file_profile = profile_id
        self.paint_existing_data_rects(profile_id=profile_id)

        self.main_view_model.profile_update_list.emit()

    def intersects_or_enclosed(self, rec1: NamedTuple, rec2: NamedTuple):
        """Checks whether two bounding boxes intersect or are enclosed by one another.

        Args:
            rec1 (NamedTuple): first bounding box = namedtuple('RECTANGLE', 'x1 x2 y1 y2')
            rec2 (NamedTuple): second bounding box = namedtuple('RECTANGLE', 'x1 x2 y1 y2')

        Returns:
            boolean: True if intersecting or enclosed by one another, False if completely seperate.
        """

        # Could simplify all x and y checks into single if statement but easier to read this way
        # Future me will appreciate

        def intersects():
            # Check if rec1 intersects rec2 or rec2 intersects rec1
            if (
                (rec2.x2 >= rec1.x1 and rec2.x2 <= rec1.x2)
                or (rec2.x1 >= rec1.x1 and rec2.x1 <= rec1.x2)
                or (
                    (rec1.x2 >= rec2.x1 and rec1.x2 <= rec2.x2)
                    or (rec1.x1 >= rec2.x1 and rec1.x1 <= rec2.x2)
                )
            ):
                x_match = True
            else:
                x_match = False
            if (
                (rec2.y2 >= rec1.y1 and rec2.y2 <= rec1.y2)
                or (rec2.y1 >= rec1.y1 and rec2.y1 <= rec1.y2)
            ) or (
                (rec1.y2 >= rec2.y1 and rec1.y2 <= rec2.y2)
                or (rec1.y1 >= rec2.y1 and rec1.y1 <= rec2.y2)
            ):
                y_match = True
            else:
                y_match = False
            if x_match and y_match:
                return True
            else:
                return False

        def enclosed():
            # Check if rec1 is enclosed by rec2 or rec2 is enclosed by rec1
            if (rec2.x1 >= rec1.x1 and rec2.x2 <= rec1.x2) or (
                rec1.x1 >= rec2.x1 and rec1.x2 <= rec2.x2
            ):
                x_match = True
            else:
                x_match = False
            if (rec2.y1 >= rec1.y1 and rec2.y2 <= rec1.y2) or (
                rec1.y1 >= rec2.y1 and rec1.y2 <= rec2.y2
            ):
                y_match = True
            else:
                y_match = False
            if x_match and y_match:
                return True
            else:
                return False

        return intersects() or enclosed()
