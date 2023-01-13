from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QTextFormat, QIcon, QFont, QTextCharFormat, QTextBlockFormat, QTextImageFormat, QPixmap, QColor
from PySide6.QtWidgets import (QComboBox, QFontComboBox, QDialog, QFrame,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFormLayout, QLineEdit, 
    QCheckBox, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QColorDialog)


class EmailSignatureEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.has_typed = False
        self.widget_layout = QVBoxLayout(self)
        self.widget_title_layout = QHBoxLayout()
        self.widget_label = QLabel()
        self.widget_label.setText(QCoreApplication.translate("Form", u"Email Editor", None))
        self.widget_title_line = QFrame()
        self.widget_title_line.setFrameShape(QFrame.HLine)
        self.widget_title_line.setFrameShadow(QFrame.Sunken)
        self.widget_title_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.widget_title_layout.addWidget(self.widget_label)
        self.widget_title_layout.addWidget(self.widget_title_line)

        self.widget_layout.addLayout(self.widget_title_layout)

        self.horizontal_option_layout = QHBoxLayout()

        self.font_combo_box = QFontComboBox()
        font = QFont()
        font.setFamilies([u"Calibri"])
        self.font_combo_box.setCurrentFont(font)
        self.font_combo_box.currentFontChanged.connect(self.changeFontFamily)

        self.horizontal_option_layout.addWidget(self.font_combo_box)

        self.font_choice_seperator = QFrame()
        self.font_choice_seperator.setFrameShape(QFrame.VLine)
        self.font_choice_seperator.setFrameShadow(QFrame.Sunken)
        self.horizontal_option_layout.addWidget(self.font_choice_seperator)

        self.bold_button = QPushButton()
        self.bold_button.setMaximumSize(QSize(24, 24))
        icon = QIcon()
        icon.addFile(u"assets/icons/bold.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.bold_button.setIcon(icon)
        self.bold_button.setIconSize(QSize(12, 12))
        self.bold_button.setCheckable(True)
        self.bold_button.toggled.connect(self.toggleBold)
        self.horizontal_option_layout.addWidget(self.bold_button)

        self.italic_button = QPushButton()
        self.italic_button.setMaximumSize(QSize(24, 24))
        icon1 = QIcon()
        icon1.addFile(u"assets/icons/italic.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.italic_button.setIcon(icon1)
        self.italic_button.setIconSize(QSize(12, 12))
        self.italic_button.setCheckable(True)
        self.italic_button.toggled.connect(self.toggleItalic)
        self.horizontal_option_layout.addWidget(self.italic_button)

        self.underline_button = QPushButton()
        self.underline_button.setMaximumSize(QSize(24, 24))
        icon2 = QIcon()
        icon2.addFile(u"assets/icons/underline_new.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.underline_button.setIcon(icon2)
        self.underline_button.setIconSize(QSize(12, 12))
        self.underline_button.setCheckable(True)
        self.underline_button.toggled.connect(self.toggleUnderline)
        self.horizontal_option_layout.addWidget(self.underline_button)

        self.color_button = QPushButton()
        self.color_button.setMaximumSize(QSize(24, 24))
        icon8_pixmap = QPixmap(12, 12)
        icon8_pixmap.fill(QColor(0, 0, 0))
        painter = QPainter(icon8_pixmap)
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(0, 0, 11, 11)
        painter.end()
        icon8 = QIcon(icon8_pixmap)
        self.color_button.setIcon(icon8)
        self.color_button.setIconSize(QSize(12, 12))
        self.color_button.clicked.connect(self.toggleColor)
        self.horizontal_option_layout.addWidget(self.color_button)

        self.font_size_combo_box = QComboBox()
        for size in [8,9,10,11,12,14,16,18,20,22,24,26,28,36,48,72]:
            self.font_size_combo_box.addItem(f"{size}")
        self.font_size_combo_box.setCurrentIndex(4)
        self.font_size_combo_box.currentIndexChanged.connect(self.changeFontSize)
        self.horizontal_option_layout.addWidget(self.font_size_combo_box)

        self.alignment_seperator = QFrame()
        self.alignment_seperator.setFrameShape(QFrame.VLine)
        self.alignment_seperator.setFrameShadow(QFrame.Sunken)
        self.horizontal_option_layout.addWidget(self.alignment_seperator)

        self.align_left_button = QPushButton()
        self.align_left_button.setMaximumSize(QSize(24, 24))
        icon3 = QIcon()
        icon3.addFile(u"assets/icons/align left.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.align_left_button.setIcon(icon3)
        self.align_left_button.setIconSize(QSize(12, 12))
        self.align_left_button.setCheckable(True)
        self.align_left_button.clicked.connect(lambda: self.setAlignment(Qt.AlignLeft))
        self.horizontal_option_layout.addWidget(self.align_left_button)

        self.align_center_button = QPushButton()
        self.align_center_button.setMaximumSize(QSize(24, 24))
        icon4 = QIcon()
        icon4.addFile(u"assets/icons/align center.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.align_center_button.setIcon(icon4)
        self.align_center_button.setIconSize(QSize(12, 12))
        self.align_center_button.setCheckable(True)
        self.align_center_button.clicked.connect(lambda: self.setAlignment(Qt.AlignCenter))
        self.horizontal_option_layout.addWidget(self.align_center_button)

        self.align_right_button = QPushButton()
        self.align_right_button.setMaximumSize(QSize(24, 24))
        icon5 = QIcon()
        icon5.addFile(u"assets/icons/align right.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.align_right_button.setIcon(icon5)
        self.align_right_button.setIconSize(QSize(12, 12))
        self.align_right_button.setCheckable(True)
        self.align_right_button.clicked.connect(lambda: self.setAlignment(Qt.AlignRight))
        self.horizontal_option_layout.addWidget(self.align_right_button)

        self.link_seperator = QFrame()
        self.link_seperator.setFrameShape(QFrame.VLine)
        self.link_seperator.setFrameShadow(QFrame.Sunken)
        self.horizontal_option_layout.addWidget(self.link_seperator)

        self.add_picture_button = QPushButton()
        self.add_picture_button.setMaximumSize(QSize(24, 24))
        icon6 = QIcon()
        icon6.addFile(u"assets/icons/insert image.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.add_picture_button.setIcon(icon6)
        self.add_picture_button.setIconSize(QSize(14, 14))
        self.add_picture_button.clicked.connect(self.insertImage)
        self.horizontal_option_layout.addWidget(self.add_picture_button)

        self.add_link_button = QPushButton()
        self.add_link_button.setMaximumSize(QSize(24, 24))
        icon7 = QIcon()
        icon7.addFile(u"assets/icons/insert link new.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.add_link_button.setIcon(icon7)
        self.add_link_button.setIconSize(QSize(16, 16))
        self.add_link_button.clicked.connect(self.show_hyperlink_dialog)
        self.horizontal_option_layout.addWidget(self.add_link_button)

        self.widget_layout.addLayout(self.horizontal_option_layout)

        self.text_edit_area = QTextEdit()
        self.text_edit_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        font_family = self.font_combo_box.currentText()
        self.text_edit_area.setCurrentFont(QFont(font_family))
        self.text_edit_area.setFontPointSize(12.0)

        # Anytime the cursor changes, update the formatting buttons/dropdowns
        # This will make it so that whether or not the user clicks or uses arrow keys
        # The buttons will update with whatever formatting is present on that character/line
        self.text_edit_area.cursorPositionChanged.connect(self.updateFormatting)
        self.widget_layout.addWidget(self.text_edit_area)


    # Whenever the cursor changes position, update all of the formatting options to where the cursor is placed
    # Only do this if the user has already typed, and if the user is not currently just sleecting text
    def updateFormatting(self):
        if self.has_typed:
            # Get the current cursor position
            cursor = self.text_edit_area.textCursor()

            # Get the current character format
            charFormat = cursor.charFormat()

            # Update the formatting controls based on the current character format
            self.bold_button.toggled.disconnect()
            self.bold_button.setChecked(charFormat.font().bold())
            self.bold_button.toggled.connect(self.toggleBold)

            self.italic_button.toggled.disconnect()
            self.italic_button.setChecked(charFormat.font().italic())
            self.italic_button.toggled.connect(self.toggleItalic)

            self.underline_button.toggled.disconnect()
            self.underline_button.setChecked(charFormat.font().underline())
            self.underline_button.toggled.connect(self.toggleUnderline)

            self.font_combo_box.currentFontChanged.disconnect()
            self.font_combo_box.setCurrentText(charFormat.font().family())
            self.font_combo_box.currentFontChanged.connect(self.changeFontFamily)

            fontSize = charFormat.font().pointSize()
            if fontSize > 0:
                self.font_size_combo_box.currentIndexChanged.disconnect()
                self.font_size_combo_box.setCurrentText(str(fontSize))
                self.font_size_combo_box.currentIndexChanged.connect(self.changeFontSize)
            # Set the color icon to the characters color
            # This will create a 12x12px box filled with text color
            # and will have a 1px black border
            pixmap = QPixmap(12,12)
            pixmap.fill(charFormat.foreground().color())
            painter = QPainter(pixmap)
            pen = QPen(QColor(0, 0, 0))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(0, 0, 11, 11)
            painter.end()
            icon = QIcon(pixmap)
            self.color_button.setIcon(icon)

            # Get the current block format to update the alignments
            blockFormat = cursor.blockFormat()

            # Update the alignment buttons based on the current block format
            self.align_left_button.clicked.disconnect()
            self.align_left_button.setChecked(blockFormat.alignment() == Qt.AlignLeft)
            self.align_left_button.clicked.connect(lambda: self.setAlignment(Qt.AlignLeft))

            self.align_center_button.clicked.disconnect()
            self.align_center_button.setChecked(blockFormat.alignment() == Qt.AlignCenter)
            self.align_center_button.clicked.connect(lambda: self.setAlignment(Qt.AlignCenter))

            self.align_right_button.clicked.disconnect()
            self.align_right_button.setChecked(blockFormat.alignment() == Qt.AlignRight)
            self.align_right_button.clicked.connect(lambda: self.setAlignment(Qt.AlignRight))

        # cursor can only change once user types something so set true
        self.has_typed = True

    def toggleColor(self):
        """Set the color of the selected text."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_edit_area.setTextColor(color)
            pixmap = QPixmap(12,12)
            pixmap.fill(color)
            painter = QPainter(pixmap)
            pen = QPen(QColor(0, 0, 0))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(0, 0, 11, 11)
            painter.end()
            icon = QIcon(pixmap)
            self.color_button.setIcon(icon)
        self.text_edit_area.setFocus()

    def toggleBold(self):
        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Create a new text char format
        charFormat = QTextCharFormat()

        # Check if the bold button is checked
        if self.bold_button.isChecked():
            # Set the font weight to bold
            charFormat.setFontWeight(QFont.Bold if charFormat.fontWeight() != QFont.Bold else QFont.Normal)
        else:
            # Set the font weight to normal
            charFormat.setFontWeight(QFont.Normal if charFormat.fontWeight() != QFont.Normal else QFont.Bold)

        # Set the new char format for the selected text or new text
        cursor.mergeCharFormat(charFormat)
        self.text_edit_area.mergeCurrentCharFormat(charFormat)
        self.text_edit_area.setFocus()

    def toggleItalic(self):
        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Create a new text char format
        charFormat = QTextCharFormat()

        # Check if the italic button is checked
        if self.italic_button.isChecked():
            # Set the font style to italic
            charFormat.setFontItalic(True)
        else:
            # Set the font style to normal
            charFormat.setFontItalic(False)

        # Set the new char format for the selected text or new text
        cursor.mergeCharFormat(charFormat)
        self.text_edit_area.mergeCurrentCharFormat(charFormat)
        self.text_edit_area.setFocus()

    def toggleUnderline(self):
        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Create a new text char format
        charFormat = QTextCharFormat()

        # Check if the underline button is checked
        if self.underline_button.isChecked():
            # Set the font underline to true
            charFormat.setFontUnderline(True)
        else:
            # Set the font underline to false
            charFormat.setFontUnderline(False)

        # Set the new char format for the selected text or new text
        cursor.mergeCharFormat(charFormat)
        self.text_edit_area.mergeCurrentCharFormat(charFormat)
        self.text_edit_area.setFocus()

    def changeFontFamily(self, font):
        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Create a new text char format
        charFormat = QTextCharFormat()

        # Get the font family from the QFont object
        fontFamily = font.family()

        # Set the font family to the selected font
        charFormat.setFontFamily(fontFamily)

        # Set the new char format for the selected text or new text
        cursor.mergeCharFormat(charFormat)
        self.text_edit_area.mergeCurrentCharFormat(charFormat)
        self.text_edit_area.setFocus()


    def changeFontSize(self, index):
        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Create a new text char format
        charFormat = QTextCharFormat()

        # Get the font size from the selected index
        size = int(self.font_size_combo_box.itemText(index))

        # Set the font size to the selected size
        charFormat.setFontPointSize(size)

        # Set the new char format for the selected text or new text
        cursor.mergeCharFormat(charFormat)
        self.text_edit_area.mergeCurrentCharFormat(charFormat)
        self.text_edit_area.setFocus()

    def setAlignment(self, alignment):
        # Update the alignment buttons based on the current block format
        self.align_left_button.setChecked(alignment == Qt.AlignLeft)
        self.align_center_button.setChecked(alignment == Qt.AlignCenter)
        self.align_right_button.setChecked(alignment == Qt.AlignRight)
        
        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Create a new text block format
        blockFormat = QTextBlockFormat()

        # Set the alignment for the block format
        blockFormat.setAlignment(alignment)

        # Set the block format for the selected text or new text
        cursor.setBlockFormat(blockFormat)
        self.text_edit_area.setAlignment(alignment)
        self.text_edit_area.setFocus()

    def insertImage(self):
        # Get the image file name
        fileName, _ = QFileDialog.getOpenFileName(self, "Insert Image", "", "Images (*.png *.xpm *.jpg *.bmp *.gif)")

        # Return if no file was selected
        if not fileName:
            return

        # Create a new image format
        imageFormat = QTextImageFormat()

        # Set the image source
        imageFormat.setName(fileName)

        # Get the current cursor position
        cursor = self.text_edit_area.textCursor()

        # Insert the image at the cursor position
        cursor.insertImage(imageFormat)

    def show_hyperlink_dialog(self):
        # Create an instance of the HyperlinkDialog and show it
        dialog = HyperlinkDialog(self)
        dialog.show()


class HyperlinkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the form layout and widgets
        layout = QFormLayout()
        self.text_edit = QLineEdit()
        self.url_edit = QLineEdit()
        self.new_window_checkbox = QCheckBox()
        self.insert_button = QPushButton("Insert")

        # Add the widgets to the layout and set their labels
        layout.addRow("Text:", self.text_edit)
        layout.addRow("URL:", self.url_edit)
        layout.addRow("Open in new window:", self.new_window_checkbox)
        layout.addRow(self.insert_button)
        self.setLayout(layout)

        # Connect the insert button's clicked signal to the insert_link slot
        self.insert_button.clicked.connect(self.insert_link)

    def insert_link(self):
           # Get the link text and URL from the form
            link_text = self.text_edit.text()
            link_url = self.url_edit.text()

            # Create a QTextCharFormat object with the link URL set as a property and blue color and underline style
            char_format = QTextCharFormat()
            char_format.setAnchor(True)
            char_format.setAnchorHref(link_url)
            char_format.setAnchorNames(link_url) # Set the anchor name to the link URL

            # If the open in new window checkbox is checked, set the target property to _blank
            if self.new_window_checkbox.isChecked():
                char_format.setAnchorNames(["_blank"])

            # Create a QTextCursor object and insert the linked text
            cursor = self.parent().text_edit_area.textCursor()
            cursor.insertText(link_text, char_format)

            # Close the dialog
            self.close()