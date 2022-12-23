import sys
import os
import io

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QRect, Slot, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QTextOption
import pytesseract

poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))
tesseract_path = str(os.path.abspath(
    os.path.join(os.getcwd(), r"Tesseract\tesseract.exe")))

class TemplateWidget(QWidget):
    """Widget used to display the file_profile template PDF, draw new bounding box for information, and to draw existing parameters bounding boxes"""

    def __init__(self, image_data, pil_image, parent=None):
        super(TemplateWidget, self).__init__(parent)
        self.pix = QPixmap()
        self.pil_image = pil_image
        self.pix.loadFromData(image_data)
        self.found_text = ''
        self.initial_width, self.initialHeight = self.pix.width(), self.pix.height()
        self.pix = self.pix.scaledToWidth(int(self.pix.width()/2))
        self.after_width, self.afterHeight = self.pix.width(), self.pix.height()
        self.width_ratio = self.after_width / self.initial_width
        self.height_ratio = self.afterHeight / self.initialHeight
        self.data_info = None
        self.profile_rect_info = None
        self.image_area_too_small = False

        self.begin, self.end = QPoint(), QPoint()
        self.last_point = QPoint()
        self.drawing = False
    
    def set_data_info(self, data_info, profile_rect_info):
        """Used to externally set class variable for use in paint event"""
        self.data_info = data_info
        self.profile_rect_info = profile_rect_info

    def reset_rect(self):
        """After creating new paramater or identifer, called to reset the curreently drawn rect"""
        self.begin, self.end = QPoint(), QPoint()
        self.update()

    def paintEvent(self, event):
        """Handles all of the painting for the existing parameter locations and names, as well as the drawing of a new bounding box"""
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.pix)
        if self.data_info != None:
            for data in self.data_info:
                data_rect = QRect(QPoint(int(data[0]*self.width_ratio), int(data[2]*self.width_ratio)), QPoint(int(data[1]*self.width_ratio), int(data[3]*self.width_ratio)))
                text_rect = QRectF(QPoint(int(data[0]*self.width_ratio), int(data[2]*self.width_ratio)-20), QPoint(int(data[1]*self.width_ratio), int(data[2]*self.width_ratio)))
                data_pen = QPen(QColor(255,165,0), 3, Qt.DashLine)
                painter.setPen(data_pen)
                painter.drawRect(data_rect)
                text_option = QTextOption(Qt.AlignLeft | Qt.AlignVCenter)
                text_option.setWrapMode(QTextOption.NoWrap)
                painter.drawText(text_rect, data[-1], text_option)
        if self.profile_rect_info != None:
            data_rect = QRect(
                QPoint(int(self.profile_rect_info[0]*self.width_ratio), int(self.profile_rect_info[2]*self.width_ratio)), 
                QPoint(int(self.profile_rect_info[1]*self.width_ratio), int(self.profile_rect_info[3]*self.width_ratio))
                )
            text_rect = QRectF(
                QPoint(int(self.profile_rect_info[0]*self.width_ratio), int(self.profile_rect_info[2]*self.width_ratio)-20), 
                QPoint(int(self.profile_rect_info[1]*self.width_ratio), int(self.profile_rect_info[2]*self.width_ratio))
                )
            data_pen = QPen(QColor(255,125,125), 3, Qt.DashLine)
            painter.setPen(data_pen)
            painter.drawRect(data_rect)
            text_option = QTextOption(Qt.AlignLeft | Qt.AlignVCenter)
            text_option.setWrapMode(QTextOption.NoWrap)
            painter.drawText(text_rect, f"Profile: " + self.profile_rect_info[-1], text_option)
        if not self.begin.isNull() and not self.end.isNull():
            rect = QRect(self.begin, self.end)
            pen = QPen(Qt.red, 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)
        

    def mousePressEvent(self, event):
        """Handles starting the creation of a new bounding box."""

        # Bounding box must be started within the bounds of the PDF template
        if event.button() == Qt.LeftButton and ((event.x() < self.pix.width() and event.x() > 0) and (event.y() < self.pix.height() and event.y() > 0)):
            self.drawing = True
            self.begin = event.pos()
            self.end = self.begin

    def mouseMoveEvent(self, event):
        """Handles updating bounding box currently being drawn."""
        if event.buttons() and Qt.LeftButton and self.drawing:

            # If mouse is outside of PDF template, then only draw bounding box to edge of PDF
            if event.x() < self.pix.width() and event.x() > 0 and event.y() < self.pix.height() and event.y() > 0:
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
                self.end = QPoint(end_x, end_y)
            self.update()

    def mouseReleaseEvent(self, event):
        """Handles setting final bounding box points as well as processing current bounding box text."""

        if event.button() == Qt.LeftButton and self.drawing:

            # If mouse is outside of PDF template, then only draw bounding box to edge of PDF
            if event.x() < self.pix.width() and event.x() > 0 and event.y() < self.pix.height() and event.y() > 0:
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
                self.end = QPoint(end_x, end_y)
            self.drawing = False
            self.update()
            # print(f"Info located at x1:{int(self.begin.x()/self.widthRatio)} y1:{int(self.begin.y()/self.widthRatio)} and x2:{int(self.end.x()/self.widthRatio)} and y2:{int(self.end.y()/self.widthRatio)}")
            
            # Because you can draw bounding box from right to left or left to right, ensure that self.begin and self.end are always the min and max respectively
            self.begin, self.end = QPoint(min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())), QPoint(max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y()))

            cropped_x_1 = int(self.begin.x()/self.width_ratio)
            cropped_y_1 = int(self.begin.y()/self.height_ratio)
            cropped_x_2 = int(self.end.x()/self.width_ratio)
            cropped_y_2 = int(self.end.y()/self.height_ratio)

            cropped_pil_image = self.pil_image.crop((cropped_x_1, cropped_y_1, cropped_x_2, cropped_y_2))
            width, height = cropped_pil_image.size
            if width > 5 and height > 5:
                self.image_area_too_small = False
            else:
                self.image_area_too_small = True
            self.analyze_area(cropped_pil_image)

    def analyze_area(self, cropped_pil_image):
        """Uses Tesseract to process cropped image and save to class variable found_text

        Args:
            cropped_pil_image (PILLOW Image): Pillow image of the file_profile template PDF which has been cropped to then user defined bounding box
        """   

        if self.image_area_too_small:
            self.found_text = "Image Area Too Small"
            return
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        ###  Page segmentation modes for config below (--psm) ###
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
        #   10    Treat the image as a single character.
        #   11    Sparse text. Find as much text as possible in no particular order.
        #   12    Sparse text with OSD.
        #   13    Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific.
        ##########################################################

        config_str = f"--psm {6}"
        self.found_text = pytesseract.image_to_string(cropped_pil_image, config=config_str).strip()
        
        print(f"Found: {self.found_text}")

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
        y_1 = int(self.begin.y()/self.width_ratio)
        y_2 = int(self.end.y()/self.width_ratio)
        return [x_1, x_2, y_1, y_2]