from PyQt5 import QtCore, QtGui, QtWidgets
from PIL import Image
from pdf2image import convert_from_path, pdfinfo_from_path
import hashlib
import pytesseract
import argparse
import cv2
import os
import time
import regex as re
import sqlite3
import random
import json

json_filename = r"C:\Users\gormbr\OneDrive - EnGlobe Corp\Desktop\sorter_test.json"

# Read JSON data into the datastore variable
if json_filename:
    with open(json_filename, 'r') as f:
        datastore = json.load(f)

# todo Figure out why some forms (placements especially) are causing a crash without any info being output
#   Remove 0 from beginning of project numbers if there is one
#   Find out why the leading 0 in set number is disappearing and why set numbers >2 digits are only showing 2 digits
debug = False

# Biggest issues to solve currently
# 1 - Dealing with files containing undetected data
# Project number is most important as it will have save directory, project description short form, and required //
# emails. Therefore If first sheet does not return a properly structured project number, search next sheet
# and repeat until properly formatted number found. This can be done by scanning each document and iterating
# through detected project numbers for one that is properly formatted.
# Add each unidentified sheet to the list widget and upon double clicking, popup box appears
# where user can input the 5 max data points a sheet would need, or any missing or incorrect data points
# Once data is corrected, if any of the 5 data points were changed, redo the analysis
# 2 - Renaming bundles if need be (Wrong info or name too long)
# Find out FileNameTooLong Error and use Try Except statement
# 3 - Make program more robust by adding in more Try Except statements
# 4 - Have program create Outlook .msg file for each individual package
# 5 - Project Number Exceptions
# Not all Project numbers save to similar directory, therefore use sqlite to save directory for each project number
# Dexter Project numbers have their own dexter number so will need to search entire comments section for one, //
# and handle when one is not found

project_data_file = r"C:\Users\gormbr\OneDrive - EnGlobe Corp\Desktop\sorter_data.json"

db = sqlite3.connect(':memory:')
cur = db.cursor()
cur.execute('''CREATE TABLE files (Project TEXT, Date DATE, Type TEXT, Set_No TEXT, Age INTEGER)''')

tesseract_path = str(os.path.abspath(os.path.join(os.getcwd(), r"Tesseract\tesseract.exe")))
print(os.getcwd())
popplerpath = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


def output(self):
    self.outputBox.appendPlainText("Analyzing...\n")


def analyze_image(img_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    text = pytesseract.image_to_string(img_path, config="--psm 6")
    # If debug enabled, print all detected text
    if debug:
        print(text)
    return text


def date_formatter(date_array):
    if date_array:
        date_day = []
        date_month = []
        date_year = []
        for temp_date in date_array:
            if temp_date is not None:
                if re.search(r"(\d+)[\s-]+", temp_date, re.I) is not None:
                    date_day_search = re.search(r"(\d+)[\s-]+", temp_date, re.I).groups()
                    date_day.append(date_day_search[-1])
                else:
                    date_day.append("NA")
                if re.search(r"\d+[\s-]+(\w+)[\s-]+", temp_date, re.I) is not None:
                    date_month_search = re.search(r"\d+[\s-]+(\w+)[\s-]+", temp_date, re.I).groups()
                    date_month.append(date_month_search[-1])
                else:
                    date_month.append("NA")
                if re.search(r"\d+[\s-]+\w+[\s-]+(\d+)", temp_date, re.I) is not None:
                    date_year_search = re.search(r"\d+[\s-]+\w+[\s-]+(\d+)", temp_date, re.I).groups()
                    date_year.append(date_year_search[-1])
                else:
                    date_year.append("NA")
            else:
                date_day.append("NA")
                date_month.append("NA")
                date_year.append("NA")

        year_unique = []
        for year in date_year:
            if year not in year_unique:
                year_unique.append(year)
        month_unique = []
        for month in date_month:
            if month not in month_unique:
                month_unique.append(month)

        date_string = ""

        for i, year in enumerate(year_unique):
            for k, month in enumerate(month_unique):
                date_day_string = ""
                day_unique = []
                for j in range(0, len(date_month)):
                    if date_year[j] == year and date_month[j] == month:
                        if date_day[j] not in day_unique:
                            day_unique.append(date_day[j])
                for j in range(0, len(day_unique)):
                    if j == 0:
                        date_day_string = day_unique[j]
                    else:
                        date_day_string = date_day_string + "," + day_unique[j]
                if k == 0:
                    date_string = date_day_string + "-" + month + "-" + year
                else:
                    date_string = date_string + "&" + date_day_string + "-" + month + "-" + year
        return date_string
    else:
        return "NO_DATES"


def detect_projectnumber(text):
    # Regex expressions for job numbers
    # B numbers: ^(B[.-\s]\d+[.-\s]+\d{1})
    # P numbers: ^(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})
    # 1900: ^(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})
    # 0200: ^([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d{4})
    # r = StringIO(text)
    if re.search(r"(B[.-\s]\d+[.-\s]+\d{1})", text, re.M) is not None:
        project_number = re.search(r"^(B[.-\s]\d+[.-\s]+\d{1})", text, re.M).group()
        project_number = project_number[-1]
        project_number = project_number.replace(" ", "")
        project_number_short = project_number
    elif re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M) is not None:
        project_number = re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M).groups()
        project_number = project_number[-1]
        project_number = project_number.replace(" ", "")
        project_number_short = re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+)", project_number, re.M).groups()
        project_number_short = project_number_short[-1]
    elif re.search(r"(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M) is not None:
        project_number = re.search(r"(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text,
                                   re.M).groups()
        project_number = project_number[-1]
        project_number = project_number.replace(" ", "")
        project_number_short = re.search(r"(1\d+[.-\s]+\d+)", project_number, re.M).groups()
        project_number_short = project_number_short[-1]
    elif re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d+)", text, re.M) is not None:
        project_number = re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d+)", text, re.M).groups()
        project_number = project_number[-1]
        project_number = project_number.replace(" ", "")
        project_number_short = re.search(r"([0-2]\d+[.-\s]+\d+)", project_number, re.M).groups()
        project_number_short = project_number_short[-1]
    elif re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+)", text, re.M) is not None:
        project_number = re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+)", text, re.M).groups()
        project_number = project_number[-1]
        project_number = project_number.replace(" ", "")
        project_number_short = re.search(r"([0-2]\d+[.-\s]+\d+)", project_number, re.M).groups()
        project_number_short = project_number_short[-1]
    else:
        project_number = "NA"
        project_number_short = "NA"
    project_number_short = project_number_short.replace(" ", "")
    return project_number, project_number_short


def pre_process_image(path, args, age_detect=None):
    # load the image and convert it to grayscale
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # If sheet_type is none, then it is the first search trying to find sheet type
    if age_detect is not None:
        gray = cv2.resize(src=gray, dsize=(0, 0), fx=2.5, fy=2.5, interpolation=cv2.INTER_LINEAR)
    # check to see if we should apply thresholding to preprocess the
    # image
    if args["preprocess"] == "thresh":
        gray = cv2.threshold(gray, 0, 255,
                             cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # make a check to see if median blurring should be done to remove noise
    elif args["preprocess"] == "blur":
        gray = cv2.medianBlur(gray, 3)
    # perform threshold and blur
    elif args["preprocess"] == "default":
        gray = cv2.bitwise_not(gray)
        gray = cv2.threshold(gray, 0, 255,
                             cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        gray = cv2.medianBlur(gray, 3)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        gray = cv2.erode(gray, kernel, iterations=1)
        gray = cv2.bitwise_not(gray)
    # perform canny edge detection
    elif args["preprocess"] == "canny":
        gray = cv2.Canny(gray, 100, 200)

    # write the grayscale image to disk as a temporary file so we can
    # apply OCR to it
    # filename = "{}.png".format(os.getpid())
    # cv2.imwrite(filename, gray)
    # cv2.imshow("Image", image)
    if debug:
        cv2.imshow("Output", gray)
    # cv2.waitKey(0)
    cv2.imwrite(path, gray)
    return gray


class UiMainwindow(object):

    def __init__(self):
        self.fileNames = None

    progress_update = QtCore.pyqtSignal(int)

    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.resize(600, 900)

        self.centralwidget = QtWidgets.QWidget(main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.layoutGrid = QtWidgets.QGridLayout()
        self.centralwidget.setLayout(self.layoutGrid)

        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(10, 0, 348, 591))
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layoutGrid.addWidget(self.tabWidget)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 590, 141, 21))
        self.label.setObjectName("creatorLabel")
        self.layoutGrid.addWidget(self.label)

        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout = QtWidgets.QGridLayout(self.tab)
        self.gridLayout.setObjectName("gridLayout")

        self.SelectFiles = QtWidgets.QPushButton(self.tab)
        self.SelectFiles.setObjectName("SelectFiles")
        self.gridLayout.addWidget(self.SelectFiles, 3, 0, 1, 2)

        self.outputBox = QtWidgets.QPlainTextEdit(self.tab)
        self.outputBox.setObjectName("outputBox")
        self.outputBox.setReadOnly(True)
        self.gridLayout.addWidget(self.outputBox, 5, 0, 1, 4)

        self.line = QtWidgets.QFrame(self.tab)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 2, 0, 1, 4)

        self.line_2 = QtWidgets.QFrame(self.tab)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 4, 0, 1, 4)

        self.analyzeButton = QtWidgets.QPushButton(self.tab)
        self.analyzeButton.setObjectName("analyzeButton")
        self.gridLayout.addWidget(self.analyzeButton, 3, 2, 1, 2)

        self.tab_2 = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab, "")
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setGeometry(QtCore.QRect(10, 10, 81, 16))
        self.label_4.setObjectName("combinedFilesLabel")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 2)

        self.listWidget = QtWidgets.QListWidget(self.tab_2)
        self.listWidget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        self.listWidget.setObjectName("listWidget")
        self.gridLayout_2.addWidget(self.listWidget, 1, 0, 5, 5)

        self.fileRename = QtWidgets.QLineEdit(self.tab_2)
        self.fileRename.setObjectName("filerenamer")
        self.gridLayout_2.addWidget(self.fileRename, 6, 0, 1, 4)

        self.fileRenameButton = QtWidgets.QPushButton(self.tab_2)
        self.fileRenameButton.setObjectName("fileRenameButton")
        self.gridLayout_2.addWidget(self.fileRenameButton, 6, 4, 1, 1)

        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.label_3.setGeometry(QtCore.QRect(10, 140, 100, 16))
        self.label_3.setObjectName("pdfOutputLabel")
        self.gridLayout_2.addWidget(self.label_3, 7, 0, 1, 2)

        self.graphicsView = QtWidgets.QGraphicsView(self.tab_2)
        self.graphicsView.setGeometry(QtCore.QRect(10, 160, 320, 400))
        self.graphicsView.setObjectName("graphicsView")
        self.gridLayout_2.addWidget(self.graphicsView, 8, 0, 20, 5)
        self.graphicsView.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)

        self.tabWidget.addTab(self.tab_2, "")
        self.tabWidget.raise_()
        self.label.raise_()

        main_window.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.retranslate_ui(main_window)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(main_window)

        main_window.setTabOrder(self.SelectFiles, self.analyzeButton)
        main_window.setTabOrder(self.analyzeButton, self.outputBox)
        main_window.setTabOrder(self.outputBox, self.tab)
        main_window.setTabOrder(self.tab, self.tab_2)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "Englobe Sorter"))
        self.label.setText(_translate("MainWindow", "Created By: Brandon Gorman"))
        self.SelectFiles.setText(_translate("MainWindow", "Select Files"))
        self.SelectFiles.clicked.connect(self.select_files_handler)
        self.fileRenameButton.setWhatsThis(_translate("MainWindow", "Rename the currently selected file"))
        self.fileRenameButton.setText(_translate("MainWindow", "Rename"))
        self.fileRenameButton.clicked.connect(self.file_rename_button_handler)
        self.analyzeButton.setText(_translate("MainWindow", "Analyze"))
        self.analyzeButton.clicked.connect(self.analyze_button_handler)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Input"))
        self.label_3.setText(_translate("MainWindow", "File Output Viewer:"))
        self.label_4.setText(_translate("MainWindow", "Combined Files:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Output"))
        self.listWidget.itemClicked.connect(self.list_widget_handler)
        self.listWidget.itemDoubleClicked.connect(self.rename_file_handler)

    def select_files_handler(self):
        self.open_file_dialog()

    def open_file_dialog(self):
        self.dialog = QtWidgets.QFileDialog(directory=str(os.path.abspath(os.path.join(os.getcwd(), r"..\.."))))
        self.fileNames, self.filters = QtWidgets.QFileDialog.getOpenFileNames()

        tuple(self.fileNames)
        if len(self.fileNames) == 1:
            file_names_string = "(" + str(len(self.fileNames)) + ")" + " file has been selected: \n"
        else:
            file_names_string = "(" + str(len(self.fileNames)) + ")" + " files have been selected: \n"
        for item in self.fileNames:
            file_names_string = file_names_string + item + "\n"
        self.outputBox.appendPlainText(file_names_string)

    def rename_file_handler(self):
        if self.listWidget.isPersistentEditorOpen(self.listWidget.currentItem()):
            self.listWidget.closePersistentEditor(self.listWidget.currentItem())
            self.listWidget.editItem(self.listWidget.currentItem())
        else:
            self.listWidget.editItem(self.listWidget.currentItem())

    def file_rename_button_handler(self):
        # try:
        file_path = self.listWidget.currentItem().data(QtCore.Qt.UserRole)
        if debug:
            print('Renamed File Path: {0}'.format(file_path))
        os.chdir(file_path.replace(file_path.split("\\").pop(), ""))
        rename_path = os.path.abspath(os.path.join(os.getcwd(), str(self.fileRename.text()) + ".pdf"))
        os.rename(self.listWidget.currentItem().data(QtCore.Qt.UserRole), rename_path)
        self.listWidget.currentItem().setData(QtCore.Qt.UserRole, rename_path)
        self.listWidget.currentItem().setText(self.fileRename.text())
        # except Exception as e:
        #     print(e)

    def analyze_button_handler(self):
        self.analyzeButton.setEnabled(False)
        time.sleep(1)
        if self.fileNames is not None:
            self.outputBox.appendPlainText("Analyzing...\n")
            time.sleep(1)
            self.data_processing()
        else:
            self.outputBox.appendPlainText("Please select at least 1 file to analyze...\n")
        self.analyzeButton.setEnabled(True)

    def analyze_queue_button_handler(self):
        self.outputBox.appendPlainText("Analyzing Queue Folder...\n")

    def list_widget_handler(self):
        image_pdf = str(self.listWidget.currentItem().data(QtCore.Qt.UserRole))
        try:
            image_jpeg = convert_from_path(image_pdf, fmt="jpeg", poppler_path=popplerpath)
        except Exception as e:
            print(e)
        if image_jpeg:
            result = Image.new("RGB", (1700, len(image_jpeg) * 2200))
            scene = QtWidgets.QGraphicsScene()
            for count, temp in enumerate(image_jpeg, 1):
                x = 0
                y = (count - 1) * 2200
                result.paste(temp, (x, y))
            name_jpeg = image_pdf.replace(".pdf", ".jpg")
            result.save(name_jpeg, 'JPEG')
            pix = QtGui.QPixmap(name_jpeg)
            pix = pix.scaledToWidth(self.graphicsView.width())
            item = QtWidgets.QGraphicsPixmapItem(pix)
            scene.addItem(item)
            self.graphicsView.setScene(scene)
            os.remove(name_jpeg)
            set_text = self.listWidget.currentItem().text().split("/").pop().replace(".pdf", "")
            self.fileRename.setText(set_text)
        else:
            print("image_jpeg list is empty")

    def data_processing(self):
        # construct the argument parse and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-p", "--preprocess", type=str, default="default",
                        help="type of pre-processing to be done")
        args = vars(ap.parse_args())

        # iterate through all input files
        # for each file scan top right of sheet ((w/2, 0, w, h/8))
        # if top right of sheet contains "test" its a concrete break sheet
        # pre process entire image
        # from preprocessed image - crop to (1100,320, 1550, 360)
        # search resultant tesseract data for project_number
        # from preprocessed image - crop to (100, 675, 300, 750)
        # search resultant tesseract data for set_no
        # from preprocessed image - crop to (1260, 710, 1475, 750)
        # search resultant tesseract data for date_cast
        # from preprocessed image - crop to (1150, 830, 1350, 1100)
        # search resultant tesseract data for compressive strengths
        # split results by \n, last value in stored split should be most recent break result
        # from preprocessed image - crop to (450, 830, 620, 1100)
        # search resultant tesseract data for age of cylinders when broken
        # split results by \n, find result in split equal to len(compressive_strength[splitdata])
        # this should return age of most recent broken cylinder

        # Import images from file path "f" using pdf2image to open
        for f in self.fileNames:
            # Each pdf page is stored as image info in an array called images_jpg
            images_jpeg = convert_from_path(f, poppler_path=popplerpath)

            # initialize variables in case no pages detected, prevent crashing
            project_number = "NA"
            project_number_short = "NA"
            set_number = "NA"
            sheet_type = "NA"
            date_cast = "NA"
            break_ages = "NA"
            sheet_type_file = "NA"
            date_placed = "NA"

            # need to iterate through the image info array to analyze each individual image.
            for image in images_jpeg:
                # Set / reset count to 0 for appending file names
                count = 0
                # reset variables in case some do not get detected
                project_number = "NA"
                project_number_short = "NA"
                set_number = "NA"
                sheet_type = "NA"
                date_cast = "NA"
                break_ages = "NA"
                date_placed = "NA"

                jpg_replace_string = str(count) + ".jpg"
                # Get path variable to save pdf files as same name but as .jpg
                f_jpg = f.replace(".pdf", jpg_replace_string)
                # Get path variable to save entire sheet separately
                jpg_full_replace_string = "-full" + str(count) + ".jpg"
                full_jpg = f.replace(".pdf", jpg_full_replace_string)

                # convert PDF files into images for analyzing
                # Tesseract doesnt directly read from PDF files
                # Get image size to crop full page to top right corner
                # Top right corner is first to analyze as the large englobe logo messes up tesseract
                w, h = image.size
                if debug:
                    print('Image size (w, h): ({0}, {1})'.format(w, h))
                # save top right corner image as jpg
                image.crop((1300, 0, 1700, h / 8)).save(f_jpg, 'JPEG')
                # save full image as .jpg
                image.save(full_jpg, 'JPEG')
                pre_process_image(f_jpg, args)

                # Using tesseract on top right corner image, try and detect what type of sheet it is
                text = analyze_image(f_jpg)

                # once analyzed, top right corner image is not required anymore, so delete
                os.remove(f_jpg)

                # if top right image analysis yields "test" it is a concrete break sheet
                if text.lower().find("test") > 0 & text.lower().find("placement") <= 0:
                    sheet_type = "3"  # 3 = break
                    # debug, print sheet type to screen
                    if debug:
                        print('Sheet Type: {0}'.format(sheet_type))
                    # Preprocess full image saved previously and analyze specific sections for remaining data
                    pre_process_image(full_jpg, args)
                    image = cv2.imread(full_jpg)
                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(300 / scale)
                        y2 = int(360 * scale)
                        x1 = int(1100 / scale)
                        x2 = int(1550 * scale)
                        if debug:
                            print('y1: {0}\ny2: {1}\nx1: {2}\nx2: {3}'.format(y1, y2, x1, x2))
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        # crop image to project number location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what project number image looks like to be analyzed
                        if debug:
                            cv2.imshow("ProjectNumber", image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        # analyze project number image for project number
                        project_number, project_number_short = detect_projectnumber(analyze_image(f_jpg))
                        if project_number is not "NA":
                            if project_number[0] == "0":
                                project_number = project_number[1:]
                                project_number_short = project_number_short[1:]
                            break

                    # debug, print the project number
                    if debug:
                        print('Project Number: {0}\nProject Number Short: {1}'.format(project_number,
                                                                                      project_number_short))

                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(675 / scale)
                        y2 = int(750 * scale)
                        x1 = int(100 / scale)
                        x2 = int(400 * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what set number image looks like to be analyzed
                        if debug:
                            cv2.imshow("Set Number", image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        # analyze set number image for set number
                        set_number_text = analyze_image(f_jpg)
                        if re.search(r"Set No[:\s]+(\d+)", set_number_text, re.M + re.I) is not None:
                            set_number = re.search(r"Set No[:\s]+(\d+)", set_number_text, re.M + re.I).groups()
                            set_number = set_number[-1]
                            break
                        elif re.search(r"SetNo[:\s]+(\d+)", set_number_text, re.M + re.I) is not None:
                            set_number = re.search(r"SetNo[:\s]+(\d+)", set_number_text, re.M + re.I).groups()
                            set_number = set_number[-1]
                            break
                        else:
                            set_number = "NA"
                        # for consistency, add 0 in front of single digit set numbers
                        # print('Length set_no: {0}'.format(len(set_number)))
                    if len(set_number) < 2:
                        set_number = "0" + str(set_number)

                    # debug, print the set number
                    if debug:
                        print('Set Number: {0}'.format(set_number))

                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(710 / scale)
                        y2 = int(750 * scale)
                        x1 = int(1260 / scale)
                        x2 = int(1475 * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        # crop image to date cast location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what date cast image looks like to be analyzed
                        if debug:
                            cv2.imshow("Date Cast:", image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        # analyze date cast image for date cast
                        date_cast_text = analyze_image(f_jpg)
                        if re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_cast_text, re.M | re.I) is not None:
                            date_cast = re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_cast_text, re.M + re.I).groups()
                            date_cast = date_cast[-1].replace("\n", "")
                            break
                        else:
                            date_cast = "NA"

                    # debug, print the date cast
                    if debug:
                        print('Date Cast: {0}'.format(date_cast))

                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(830 / scale)
                        y2 = int(1100 * scale)
                        x1 = int(1150 / scale)
                        x2 = int(1350 * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        # crop image to break strengths location
                        cv2.imwrite(f_jpg,
                                    image[y1:y2, x1:x2])
                        # debug, show what break strengths looks like to be analyzed
                        if debug:
                            cv2.imshow("Break Strengths", image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        # analyze break strengths for break strengths
                        break_strengths_text = analyze_image(f_jpg)
                        break_strengths = break_strengths_text.split("\n")
                        if break_strengths is not "NA":
                            break
                    # debug, print the break strengths
                    if debug:
                        print('Break Strengths: {0}'.format(break_strengths))

                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(830 / scale)
                        y2 = int(1100 * scale)
                        x1 = int(450 / scale)
                        x2 = int(620 * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        # crop image to latest break age location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what latest break age looks like to be analyzed
                        if debug:
                            cv2.imshow("Break Strengths", image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        # analyze latest break age for age
                        break_age_text = analyze_image(f_jpg)
                        break_ages = break_age_text.split("\n")
                        # debug, print the latest break age
                        if debug:
                            print('All Break Ages: {0}'.format(break_ages))
                        if len(break_strengths) > 0:
                            break_ages = break_ages[len(break_strengths) - 1]
                        else:
                            break_ages = break_ages[0]
                        if break_ages is not "NA":
                            break

                    if debug:
                        print('Latest Break Age: {0}'.format(break_ages))

                elif text.lower().find("placement") > 0:
                    sheet_type = "1"  # 1 = "placement"
                    sheet_type_file = "ConcretePlacement("
                    # debug, print sheet type to screen
                    if debug:
                        print('Sheet Type: {0}'.format(sheet_type))
                    # Preprocess full image saved previously and analyze specific sections for remaining data
                    pre_process_image(full_jpg, args)
                    image = cv2.imread(full_jpg)
                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(290 / scale)
                        y2 = int(350 * scale)
                        x1 = int(1050 / scale)
                        x2 = int(1550 * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        if debug:
                            print('y1: {0}\ny2: {1}\nx1: {2}\nx2: {3}'.format(y1, y2, x1, x2))
                        # crop image to project number location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what project number image looks like to be analyzed
                        if debug:
                            cv2.imshow("ProjectNumber", image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        # analyze project number image for project number
                        project_number, project_number_short = detect_projectnumber(analyze_image(f_jpg))
                        if project_number != "NA":
                            break
                    # debug, print the project number
                    if debug:
                        print('Project Number: {0}\nProject Number Short: {1}'.format(project_number,
                                                                                      project_number_short))
                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(700 / scale)
                        y2 = int(740 * scale)
                        x1 = int(1250 / scale)
                        x2 = int(1450 * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        # crop image to date placed location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what date placed image looks like to be analyzed
                        if debug:
                            cv2.imshow("Date Cast:", image[y1:y2, x1:x2])
                            cv2.waitKey(0)

                        # analyze date placed image for date cast
                        date_placed_text = analyze_image(f_jpg)
                        if re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_placed_text, re.M | re.I) is not None:
                            date_placed = re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_placed_text, re.M + re.I).groups()
                            date_placed = date_placed[-1].replace("\n", "")
                            break
                        else:
                            date_placed = "NA"
                    # debug, print the date cast
                    if debug:
                        print('Date Placed: {0}'.format(date_placed))

                if sheet_type == "3":  # 3 = break
                    params = [project_number_short, date_cast, sheet_type, set_number, break_ages]
                else:
                    params = [project_number_short, date_placed, sheet_type, set_number, break_ages]
                # Turn "NA" results into None results to help with sorting in sqlite3
                count = 0
                for item in params:
                    if item == "NA":
                        params[count] = None
                    count += 1
                if os.path.isfile(full_jpg):
                    os.remove(full_jpg)
                if os.path.isfile(f_jpg):
                    os.remove(f_jpg)
                cur.execute("INSERT INTO files VALUES(?,?,?,?,?)", params)
                db.commit()
                count += 1

            cur.execute("SELECT * From files")
            if debug:
                print(cur.fetchall())
            cur.execute("SELECT * From files ORDER BY Project, Type, Date, Set_No, Age")
            records = cur.fetchall()
            if debug:
                print(records)

            # TODO Finish file naming for sieve, density, and undetected sheet types

            placement_string = ""
            break_string = ""
            density_string = ""
            sieve_string = ""

            # For multi page files, some files may not detect project number properly so iterate through all pages and get
            # project number from a successful detection
            for i in range(0, len(records)):
                if records[i][0] is not None:
                    project_number_short = records[i][0]

            # initialize/reset date_array for each new input file
            placement_date_array = []
            # iterate through the local database records and if sheet type is placement, store date placed into an array
            for i in range(0, len(records)):
                if records[i][2] == "1":  # 1 = placement
                    placement_date_array.append(records[i][1])
            if placement_date_array:
                placement_date = date_formatter(placement_date_array)
                placement_string = '_ConcretePlacement({0})'.format(placement_date)

            # initialize/reset date_array for each new input file
            break_date_array = []
            break_age_array = []

            # iterate through the local database records and if sheet type is break sheet, store date cast into an array
            # need to format dates for each possible age from 0 - 99
            for i in range(0, len(records)):
                if records[i][2] == "3" and records[i][4] not in break_age_array:  # 3 = break
                    break_age_array.append(records[i][4])
            break_age_array.reverse()
            for age in break_age_array:
                break_set_no = []
                break_set_string = ""
                break_date_array = []
                for i in range(0, len(records)):
                    if records[i][4] == age:
                        break_date_array.append(records[i][1])
                        break_set_no.append(records[i][3])
                if break_set_no:
                    for k, temp_set in enumerate(break_set_no):
                        if k == 0:
                            break_set_string = str(temp_set)
                        else:
                            break_set_string = break_set_string + "," + str(temp_set)
                if break_date_array:
                    break_date = date_formatter(break_date_array)
                    break_string = break_string + '_{0}dConcStrength_S{1}({2})' \
                        .format(age, break_set_string.replace("None", "NA"), break_date)

            # Placeholder package number till directory system is in place
            # package_number = "04"

            for project_data in datastore:
                if project_number_short.replace(".", "") == project_data["project_number"].replace(".", "") or \
                        project_number_short.replace("-", "") == project_data["project_number"].replace("-", ""):
                    project_description = project_data["project_description"]
                    file_path = project_data["project_directory"]
                    break
                elif (project_number_short.replace(".", "") in project_data["project_number"].replace(".", "") or
                        project_number_short.replace("-", "") in project_data["project_number"].replace("-", "")) and \
                        project_number[-1] == project_data["project_number"][-1]:
                    project_description = project_data["project_description"]
                    file_path = project_data["project_directory"]
                else:
                    project_description = "SomeProjectDescription"
                    file_path = f.replace(f.split("/").pop(), "")

            # Wont happen much in full use but may encounter same file names during testing
            # Just add a random integer at end of file for now
            os.chdir(file_path)
            rename_path = os.path.abspath(os.path.join(os.getcwd(), file_title + ".pdf"))
            if os.path.isfile(rename_path):
                file_title = file_title + str(random.randint(1, 999))
                rename_path = os.path.abspath(os.path.join(os.getcwd(), file_title + ".pdf"))
            os.rename(f, rename_path)

            only_files = [f for f in os.listdir(os.getcwd()) if os.path.isfile(os.path.join(os.getcwd(), f))]
            package_number_old = 0

            if only_files:
                for file in only_files:
                    package_number = int(re.search(r"(\d+)-[\dA-z]", file, re.I))
                    if package_number > package_number_old:
                        package_number_highest = package_number
                    package_number_old = package_number
            else:  # No files in directory yet
                package_number_highest = "01"

            file_title = package_number_highest + "-" + str(project_number_short) + "_" + project_description

            split_name = f.split("/").pop()
            if placement_string != "":
                file_title = file_title + placement_string
            if break_string != "":
                file_title = file_title + break_string
            if placement_string == "" and break_string == "":
                file_title = "Sheet_Type_Not_Found_(" + split_name + ")"

            print_string = split_name + " renamed to " + file_title + "\n"
            self.outputBox.appendPlainText(print_string)
            self.listWidgetItem = QtWidgets.QListWidgetItem(file_title)
            self.listWidgetItem.setData(QtCore.Qt.UserRole, rename_path)
            self.listWidget.addItem(self.listWidgetItem)

            cur.execute("DELETE From files")


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UiMainwindow()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
