import io
import os
import sys

import pytesseract
from PySide6 import QtCore, QtGui, QtWidgets
from utils.path_utils import resource_path

tesseract_path = resource_path(os.path.join("Tesseract","tesseract.exe"))


class TemplateWidget(QtWidgets.QWidget):
    """Widget used to display the file_profile template PDF, draw new bounding box for information, and to draw existing parameters bounding boxes"""
    secondary_rect_complete_signal = QtCore.Signal(str)

    def __init__(self, image_data=None, pil_image=None):
        super(TemplateWidget, self).__init__()
        self.pix = QtGui.QPixmap()
        self.pil_image = pil_image
        self.initial_width = 0
        self.initial_height = 0
        self.width_ratio = 0
        self.height_ratio = 0
        self.drawing_secondary = False
        self._image_data = image_data
        if self._image_data is not None:
            self.initialize_pdf()
        

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        self.found_text = ''
        self.secondary_text = ''
        self.data_info = None
        self.profile_rect_info = None
        self.image_area_too_small = False

        self.begin, self.end = QtCore.QPoint(), QtCore.QPoint()
        self.secondary_begin, self.secondary_end = QtCore.QPoint(), QtCore.QPoint()
        self.last_point = QtCore.QPoint()
        self.drawing = False

    def initialize_pdf(self):
        self.pix.loadFromData(self._image_data)
        self.initial_width, self.initial_height = self.pix.width(), self.pix.height()
        self.pix = self.pix.scaledToWidth(int(self.pix.width()/2))
        self.after_width, self.after_height = self.pix.width(), self.pix.height()
        self.width_ratio = self.after_width / self.initial_width
        self.height_ratio = self.after_height / self.initial_height

    def set_width_ratio(self, width: int):
        self.width_ratio = width / self.initial_width

    def set_height_ratio(self, height: int):
        self.height_ratio = height / self.initial_height

    # This will resize the pixmap but need to include parameters to adjust the paint event rectangles
    def resizeEvent(self, event):
        if self._image_data is not None:
            # Update the pixmap when the widget is resized only when a PDF is loaded
            self.set_width_ratio(event.size().width())
            self.set_height_ratio(event.size().height())

            image = QtGui.QImage()
            image.loadFromData(self._image_data)
            image = image.scaled(event.size(), aspectMode=QtCore.Qt.IgnoreAspectRatio, mode=QtCore.Qt.SmoothTransformation)
            
            self.pix = QtGui.QPixmap.fromImage(image)
            self.reset_rects()
            self.update()

    def set_data_info(self, data_info, profile_rect_info):
        """Used to externally set class variable for use in paint event"""
        self.data_info = data_info
        self.profile_rect_info = profile_rect_info
        self.reset_rects()

    def reset_rects(self):
        """After creating new parameter or identifier, called to reset the currently drawn rect"""
        self.begin, self.end = QtCore.QPoint(), QtCore.QPoint()
        self.secondary_begin, self.secondary_end = QtCore.QPoint(), QtCore.QPoint()
        self.update()

    def reset_secondary_rects(self):
        """Resets secondary rect after removing a secondary parameter"""
        self.secondary_begin, self.secondary_end = QtCore.QPoint(), QtCore.QPoint()
        self.update()

    def paintEvent(self, event):
        """Handles all of the painting for the existing parameter locations and names, as well as the drawing of a new bounding box"""
        painter = QtGui.QPainter(self)
        painter.drawPixmap(QtCore.QPoint(), self.pix)

        # List of colors for dual parameters
        dual_colors = [
            QtGui.QColor(255, 69, 0), QtGui.QColor(50, 205, 50),
            QtGui.QColor(70, 130, 180), QtGui.QColor(255, 215, 0),
            QtGui.QColor(139, 0, 139), QtGui.QColor(255, 105, 180),
            QtGui.QColor(165, 42, 42), QtGui.QColor(255, 160, 122),
            QtGui.QColor(100, 149, 237), QtGui.QColor(144, 238, 144),
            QtGui.QColor(255, 182, 193), QtGui.QColor(255, 228, 196)
        ]
        dual_color_index = 0

        if self.data_info is not None:
            for data_entry in self.data_info:
                primary_coords = data_entry['primary']['coords']
                secondary_coords = data_entry.get('secondary', {}).get('coords', None)

                # Get primary rectangle and text_rect for title
                primary_rect = QtCore.QRect(QtCore.QPoint(int(primary_coords[0]*self.width_ratio), int(primary_coords[2]*self.height_ratio)), 
                                            QtCore.QPoint(int(primary_coords[1]*self.width_ratio), int(primary_coords[3]*self.height_ratio)))

                text_height = 20
                text_rect = QtCore.QRectF(
                    QtCore.QPoint(int(primary_coords[0]*self.width_ratio), int(primary_coords[2]*self.height_ratio) - text_height),
                    QtCore.QPoint(int(primary_coords[1]*self.width_ratio), int(primary_coords[2]*self.height_ratio)))

                primary_color = QtGui.QColor(255, 165, 0)  # Default orange color for single parameter

                if secondary_coords:
                    # If dual parameter, get a color from the dual_colors list and increment the index
                    primary_color = dual_colors[dual_color_index % len(dual_colors)]
                    dual_color_index += 1

                # Draw primary box and its title
                self.paint_box_and_text(painter, primary_rect, text_rect, data_entry['primary']['description'], primary_color)

                # If secondary rectangle exists, draw it with the same color but no title
                if secondary_coords:
                    secondary_rect = QtCore.QRect(QtCore.QPoint(int(secondary_coords[0]*self.width_ratio), int(secondary_coords[2]*self.height_ratio)), 
                                                QtCore.QPoint(int(secondary_coords[1]*self.width_ratio), int(secondary_coords[3]*self.height_ratio)))
                    self.paint_box_and_text(painter, secondary_rect, None, None, primary_color)
                    self.draw_dashed_line_between_rects(painter, primary_rect, secondary_rect, primary_color)


        if self.profile_rect_info != None:
            data_rect = QtCore.QRect(
                QtCore.QPoint(int(self.profile_rect_info[0]*self.width_ratio), int(
                    self.profile_rect_info[2]*self.height_ratio)),
                QtCore.QPoint(int(self.profile_rect_info[1]*self.width_ratio), int(
                    self.profile_rect_info[3]*self.height_ratio))
            )
            text_rect = QtCore.QRectF(
                QtCore.QPoint(int(self.profile_rect_info[0]*self.width_ratio), int(
                    self.profile_rect_info[2]*self.height_ratio)-20),
                QtCore.QPoint(int(self.profile_rect_info[1]*self.width_ratio), int(
                    self.profile_rect_info[2]*self.height_ratio))
            )
            profile_text = f"Profile: {self.profile_rect_info[-1]}"
            self.paint_box_and_text(painter, data_rect, text_rect, profile_text, QtGui.QColor(255, 125, 125))
        if not self.begin.isNull() and not self.end.isNull():
            rect = QtCore.QRect(self.begin, self.end)
            pen = QtGui.QPen(QtCore.Qt.red, 3, QtCore.Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

        if not self.secondary_begin.isNull() and not self.secondary_end.isNull():
            rect = QtCore.QRect(self.secondary_begin, self.secondary_end)
            pen = QtGui.QPen(QtCore.Qt.blue, 3, QtCore.Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    def paint_box_and_text(self, painter: QtGui.QPainter, data_bounds: QtCore.QRect, text_bounds: QtCore.QRect, text: str, pen_color: QtGui.QColor):
        
        painter.setPen(QtCore.Qt.NoPen) 
        painter.setBrush(QtCore.Qt.NoBrush)

        # Draw the bounding box of the data
        data_pen = QtGui.QPen(pen_color, 3, QtCore.Qt.DashLine)
        painter.setPen(data_pen)
        painter.drawRect(data_bounds)

        if text_bounds == None or text == None:
            painter.setPen(QtCore.Qt.NoPen) 
            painter.setBrush(QtCore.Qt.NoBrush)
            return
        
        # Get font size and generate transparent backdrop
        font_metrics = QtGui.QFontMetrics(painter.font())
        text_width = font_metrics.boundingRect(text).width()
        text_bounds.setRight(text_bounds.left() + text_width + 10)               
        background_color = QtGui.QColor(0, 0, 0, 128)  # semi-transparent black
        text_pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        painter.setBrush(background_color)
        painter.setPen(QtCore.Qt.NoPen)  # no border for the background rectangle
        painter.drawRect(text_bounds)

        # Add margin to text bounds and draw text
        text_bounds.setLeft(text_bounds.left() + 5)  # add a left margin to the text
        painter.setPen(text_pen)  # reset to the desired text color
        text_option = QtGui.QTextOption(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        text_option.setWrapMode(QtGui.QTextOption.NoWrap)
        painter.drawText(text_bounds, text, text_option)

        painter.setPen(QtCore.Qt.NoPen) 
        painter.setBrush(QtCore.Qt.NoBrush)

    def draw_dashed_line_between_rects(self, painter: QtGui.QPainter, rect1: QtCore.QRect, rect2: QtCore.QRect, pen_color: QtGui.QColor):
        center1 = rect1.center()
        center2 = rect2.center()

        intersection1 = self.line_rect_intersection(center1, center2, rect1)
        intersection2 = self.line_rect_intersection(center1, center2, rect2)

        data_pen = QtGui.QPen(pen_color, 3, QtCore.Qt.DashLine)
        painter.setPen(data_pen)
        painter.drawLine(intersection1, intersection2)
        

    def line_rect_intersection(self, line_p1: QtCore.QPoint, line_p2: QtCore.QPoint, rect: QtCore.QRect) -> QtCore.QPoint:
        lines = [
            QtCore.QLineF(rect.topLeft(), rect.topRight()),
            QtCore.QLineF(rect.topRight(), rect.bottomRight()),
            QtCore.QLineF(rect.bottomRight(), rect.bottomLeft()),
            QtCore.QLineF(rect.bottomLeft(), rect.topLeft())
        ]

        target_line = QtCore.QLineF(line_p1, line_p2)
        for line in lines:
            intersection = line.intersects(target_line)
            if intersection and intersection[0] == QtCore.QLineF.BoundedIntersection:
                try:
                    return intersection[1]
                except IndexError:
                    pass

        # If for some reason there's no intersection (which shouldn't happen), just return the center of the rect.
        return rect.center()

    def mousePressEvent(self, event):
        """Handles starting the creation of a new bounding box."""

        # Bounding box must be started within the bounds of the PDF template
        if event.button() == QtCore.Qt.LeftButton and ((event.x() < self.pix.width() and event.x() > 0) and (event.y() < self.pix.height() and event.y() > 0)):
            self.drawing = True
            if self.drawing_secondary:
                self.secondary_begin = event.pos()
                self.secondary_end = self.secondary_begin
            else:
                self.begin = event.pos()
                self.end = self.begin
            

    def mouseMoveEvent(self, event):
        """Handles updating bounding box currently being drawn."""
        if event.buttons() and QtCore.Qt.LeftButton and self.drawing:

            # If mouse is outside of PDF template, then only draw bounding box to edge of PDF
            if event.x() < self.pix.width() and event.x() > 0 and event.y() < self.pix.height() and event.y() > 0:
                if self.drawing_secondary:
                    self.secondary_end = event.pos()
                else:
                    self.end = event.pos()
            else:
                if event.x() < 0:
                    end_x = 1
                elif event.x() > self.pix.width():
                    end_x = self.pix.width()
                else:
                    end_x = event.x()
                if event.y() < 0:
                    end_y = 1
                elif event.y() > self.pix.height():
                    end_y = self.pix.height()
                else:
                    end_y = event.y()
                if self.drawing_secondary:
                    self.secondary_end = QtCore.QPoint(end_x, end_y)
                else:
                    self.end = QtCore.QPoint(end_x, end_y)
            self.update()

    def mouseReleaseEvent(self, event):
        """Handles setting final bounding box points as well as processing current bounding box text."""

        if event.button() == QtCore.Qt.LeftButton and self.drawing:

            # If mouse is outside of PDF template, then only draw bounding box to edge of PDF
            if event.x() < self.pix.width() and event.x() > 0 and event.y() < self.pix.height() and event.y() > 0:
                if self.drawing_secondary:
                    self.secondary_end = event.pos()
                else:
                    self.end = event.pos()
            else:
                if event.x() < 0:
                    end_x = 1
                elif event.x() > self.pix.width():
                    end_x = self.pix.width()
                else:
                    end_x = event.x()
                if event.y() < 0:
                    end_y = 1
                elif event.y() > self.pix.height():
                    end_y = self.pix.height()
                else:
                    end_y = event.y()
                if self.drawing_secondary:
                    self.secondary_end = QtCore.QPoint(end_x, end_y)
                else:
                    self.end = QtCore.QPoint(end_x, end_y)
                    
            self.drawing = False
            self.update()
            # print(f"Info located at x1:{int(self.begin.x()/self.widthRatio)} y1:{int(self.begin.y()/self.widthRatio)} and x2:{int(self.end.x()/self.widthRatio)} and y2:{int(self.end.y()/self.widthRatio)}")

            if self.drawing_secondary:
                (self.secondary_begin, self.secondary_end) = self.determine_begin_end(self.secondary_begin, self.secondary_end)
                x_begin, y_begin = self.secondary_begin.x(), self.secondary_begin.y()
                x_end, y_end = self.secondary_end.x(), self.secondary_end.y()
            else:
                (self.begin, self.end) = self.determine_begin_end(self.begin, self.end)
                x_begin, y_begin = self.begin.x(), self.begin.y()
                x_end, y_end = self.end.x(), self.end.y()

            cropped_x_1 = int(x_begin/self.width_ratio)
            cropped_y_1 = int(y_begin/self.height_ratio)
            cropped_x_2 = int(x_end/self.width_ratio)
            cropped_y_2 = int(y_end/self.height_ratio)

            cropped_pil_image = self.pil_image.crop(
                (cropped_x_1, cropped_y_1, cropped_x_2, cropped_y_2))
            width, height = cropped_pil_image.size
            if width > 5 and height > 5:
                self.image_area_too_small = False
            else:
                self.image_area_too_small = True

            self.analyze_area(cropped_pil_image)

            if self.drawing_secondary:
                self.drawing_secondary = False
                self.secondary_rect_complete_signal.emit(self.secondary_text)
                print("emitted")

    def determine_begin_end(self, begin, end):

        begin_fixed = QtCore.QPoint(min(begin.x(), end.x()), min(begin.y(), end.y()))
        end_fixed = QtCore.QPoint(max(begin.x(), end.x()), max(begin.y(), end.y()))

        return begin_fixed, end_fixed


    def analyze_area(self, cropped_pil_image):
        """Uses Tesseract to process cropped image and save to class variable found_text

        Args:
            cropped_pil_image (PILLOW Image): Pillow image of the file_profile template PDF which has been cropped to then user defined bounding box
        """

        if self.image_area_too_small:
            self.found_text = "Image Area Too Small"
            return
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        config_str = f"--psm {6}"
        # Page segmentation modes for config_str "--psm {mode}"
        # mode   Description
        #   0    Orientation and script detection (OSD) only.
        #   1    Automatic page segmentation with OSD.
        #   2    Automatic page segmentation, but no OSD, or OCR.
        #   3    Fully automatic page segmentation, but no OSD. (Default)
        #   4    Assume a single column of text of variable sizes.
        #   5    Assume a single uniform block of vertically aligned text.
        # > 6    Assume a single uniform block of text.
        #   7    Treat the image as a single text line.
        #   8    Treat the image as a single word.
        #   9    Treat the image as a single word in a circle.
        #  10    Treat the image as a single character.
        #  11    Sparse text. Find as much text as possible in no particular order.
        #  12    Sparse text with OSD.
        #  13    Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific.
        ##########################################################

        if self.drawing_secondary:
            self.secondary_text = pytesseract.image_to_string(
                cropped_pil_image, config=config_str).strip()
        else:
            self.found_text = pytesseract.image_to_string(
                cropped_pil_image, config=config_str).strip()

        print(f"Found: {self.found_text}", type(self.found_text))

    def get_secondary_parameter_rect(self):
        # Remove any existing rects and text
        print("Getting secondary parameter rect")
        self.drawing_secondary = True
        print("Drawing secondary", self.drawing_secondary)

    def scaled_width(self):
        """Returns the scaled width of the current file_profile template. \n
        Could just call .pix.width() directly but easier to understand when called from outside of this class.

        Returns:
            float: Width of the currently shown file_profile template
        """
        return self.pix.width()

    def scaled_height(self):
        """Returns the scaled height of the current file_profile template. \n
        Could just call .pix.height() directly but easier to understand when called from outside of this class.

        Returns:
            float: Height of the currently shown file_profile template
        """
        return self.pix.height()

    def true_coords(self):
        """Formats current scaled bounding box locations to actual locations for full sized file.

        Returns:
            list: List format [x_1, x_2, y_1, y_2]
        """
        x_1 = int(self.begin.x()/self.width_ratio)
        x_2 = int(self.end.x()/self.width_ratio)
        y_1 = int(self.begin.y()/self.height_ratio)
        y_2 = int(self.end.y()/self.height_ratio)
        return [x_1, x_2, y_1, y_2]
    
    def true_secondary_coords(self):
        """Formats current scaled secondary bounding box locations to actual locations for full sized file.

        Returns:
            list: List format [x_1, x_2, y_1, y_2]
        """
        x_1 = int(self.secondary_begin.x()/self.width_ratio)
        x_2 = int(self.secondary_end.x()/self.width_ratio)
        y_1 = int(self.secondary_begin.y()/self.height_ratio)
        y_2 = int(self.secondary_end.y()/self.height_ratio)
        return [x_1, x_2, y_1, y_2]
