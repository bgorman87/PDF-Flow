from PyQt5 import QtCore, QtGui, QtWidgets
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import argparse
import cv2
import os
import regex as re
import time
import sqlite3

debug = False

#############
# Changing scope of this project
# Assume scanned document has all required documents for single project number - Easy to do by hand
# No need for a queue folder
#############

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

# try sorting using sqlite3 in memory mode

db = sqlite3.connect(':memory:')
cur = db.cursor()
cur.execute('''CREATE TABLE files (Project TEXT, Date DATE, Type TEXT, Set_No INTEGER, Age INTEGER)''')


def output(self):
    self.outputBox.appendPlainText("Analyzing...\n")


def analyze_image(img_path):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Users\bgorm\AppData\Local\Tesseract-OCR\tesseract.exe'
    # text = pytesseract.image_to_string(Image.open(img_path), config="--psm 6")
    text = pytesseract.image_to_string(img_path, config="--psm 6")
    return text


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
        project_number_short = project_number
    elif re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M) is not None:
        project_number = re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M).groups()
        project_number = project_number[-1]
        project_number_short = re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+)", text, re.M).groups()
        project_number_short = project_number_short[-1]
    elif re.search(r"(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M) is not None:
        project_number = re.search(r"(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text,
                                   re.M).groups()
        project_number = project_number[-1]
        project_number_short = re.search(r"(1\d+[.-\s]+\d+)", text, re.M).groups()
        project_number_short = project_number_short[-1]
    elif re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d{4})", text, re.M) is not None:
        project_number = re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d{4})", text, re.M).groups()
        project_number = project_number[-1]
        project_number_short = re.search(r"([0-2]\d+[.-\s]+\d+)", text, re.M).groups()
        project_number_short = project_number_short[-1]
    else:
        project_number = "N/A"
        project_number_short = "N/A"
    project_number = project_number.replace(" ", "")
    project_number_short = project_number_short.replace(" ", "")
    return project_number, project_number_short


# Perform image pre-processing based on image src and input args


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
        gray = cv2.threshold(gray, 0, 255,
                             cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        gray = cv2.medianBlur(gray, 3)
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
        main_window.resize(361, 630)

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
        self.gridLayout.addWidget(self.SelectFiles, 3, 0, 1, 1)

        self.queueLocation = QtWidgets.QLineEdit(self.tab)
        self.queueLocation.setObjectName("queueLocation")
        self.gridLayout.addWidget(self.queueLocation, 1, 0, 1, 3)

        self.selectQueueFolder = QtWidgets.QPushButton(self.tab)
        self.selectQueueFolder.setObjectName("selectQueueFolder")
        self.gridLayout.addWidget(self.selectQueueFolder, 1, 3, 1, 2)

        self.outputBox = QtWidgets.QPlainTextEdit(self.tab)
        self.outputBox.setObjectName("outputBox")
        self.outputBox.setReadOnly(True)
        self.gridLayout.addWidget(self.outputBox, 5, 0, 1, 5)

        self.analyzeQueueButton = QtWidgets.QPushButton(self.tab)
        self.analyzeQueueButton.setObjectName("analyzeQueueButton")
        self.gridLayout.addWidget(self.analyzeQueueButton, 3, 4, 1, 1)

        self.openQueueFolder = QtWidgets.QPushButton(self.tab)
        self.openQueueFolder.setObjectName("openQueueFolder")
        self.gridLayout.addWidget(self.openQueueFolder, 3, 2, 1, 2)

        self.line = QtWidgets.QFrame(self.tab)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 4, 0, 1, 5)

        self.label_2 = QtWidgets.QLabel(self.tab)
        self.label_2.setObjectName("queueFolderLabel")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 2)

        self.line_2 = QtWidgets.QFrame(self.tab)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 2, 0, 1, 5)

        self.analyzeButton = QtWidgets.QPushButton(self.tab)
        self.analyzeButton.setObjectName("analyzeButton")
        self.gridLayout.addWidget(self.analyzeButton, 3, 1, 1, 1)

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
        self.gridLayout_2.addWidget(self.fileRename, 6, 0, 1, 3)

        self.fileRenameButton = QtWidgets.QPushButton(self.tab)
        self.fileRenameButton.setObjectName("fileRenameButton")
        self.gridLayout.addWidget(self.fileRenameButton, 6, 3, 1, 2)

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

        main_window.setTabOrder(self.queueLocation, self.selectQueueFolder)
        main_window.setTabOrder(self.selectQueueFolder, self.SelectFiles)
        main_window.setTabOrder(self.SelectFiles, self.analyzeButton)
        main_window.setTabOrder(self.analyzeButton, self.openQueueFolder)
        main_window.setTabOrder(self.openQueueFolder, self.outputBox)
        main_window.setTabOrder(self.outputBox, self.tab)
        main_window.setTabOrder(self.tab, self.tab_2)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "Englobe Sorter"))
        self.label.setText(_translate("MainWindow", "Created By: Brandon Gorman"))
        self.SelectFiles.setText(_translate("MainWindow", "Select Files"))
        self.SelectFiles.clicked.connect(self.select_files_handler)
        self.selectQueueFolder.setWhatsThis(_translate("MainWindow", "Change the queue folder location"))
        self.selectQueueFolder.setText(_translate("MainWindow", "Change"))
        self.selectQueueFolder.clicked.connect(self.select_queue_folder_handler)
        self.fileRenameButton.setWhatsThis(_translate("MainWindow", "Rename the currently selected file"))
        self.fileRenameButton.setText(_translate("MainWindow", "Rename"))
        self.analyzeQueueButton.setText(_translate("MainWindow", "Analyze Queue"))
        self.analyzeQueueButton.clicked.connect(self.analyze_queue_button_handler)
        self.openQueueFolder.setText(_translate("MainWindow", "Open Queue"))
        self.label_2.setText(_translate("MainWindow", "Queue Folder:"))
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
        self.dialog = QtWidgets.QFileDialog()
        self.fileNames, self.filters = QtWidgets.QFileDialog.getOpenFileNames()

        tuple(self.fileNames)
        if len(self.fileNames) == 1:
            file_names_string = "(" + str(len(self.fileNames)) + ")" + " file has been selected: \n"
        else:
            file_names_string = "(" + str(len(self.fileNames)) + ")" + " files have been selected: \n"
        for item in self.fileNames:
            file_names_string = file_names_string + item + "\n"
        self.outputBox.appendPlainText(file_names_string)

    def open_folder_dialog(self):
        self.dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        self.folderName = self.dialog.selectedFiles()[0]
        if self.dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.update()
        file_folder_string = "Queue Folder save location set to: " + self.folderName + "\n"
        self.outputBox.appendPlainText(file_folder_string)

    def open_queue_folder_handler(self):
        os.startfile(self.folderName)
        open_queue_folder_string = "Opening queue folder in separate window\n"
        self.outputBox.appendPlainText(open_queue_folder_string)

    def select_queue_folder_handler(self):
        self.open_folder_dialog()

    def rename_file_handler(self):
        if self.listWidget.isPersistentEditorOpen(self.listWidget.currentItem()):
            self.listWidget.closePersistentEditor(self.listWidget.currentItem())
            self.listWidget.editItem(self.listWidget.currentItem())
        else:
            self.listWidget.editItem(self.listWidget.currentItem())

    def update(self):
        self.queueLocation.setText(self.folderName)

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
        image_jpeg = convert_from_path(image_pdf, fmt="jpeg")
        name_jpeg = image_pdf.replace(".pdf", ".jpg")
        for temp in image_jpeg:
            temp.save(name_jpeg, 'JPEG')
        pix = QtGui.QPixmap(name_jpeg)
        pix = pix.scaledToWidth(self.graphicsView.width())
        item = QtWidgets.QGraphicsPixmapItem(pix)
        scene = QtWidgets.QGraphicsScene()
        scene.addItem(item)
        self.graphicsView.setScene(scene)
        self.outputBox.appendPlainText(str(self.listWidget.currentItem().data(QtCore.Qt.UserRole)))
        os.remove(name_jpeg)
        self.fileRename.setText(image_pdf)

    def data_processing(self):
        # construct the argument parse and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-p", "--preprocess", type=str, default="default",
                        help="type of pre-processing to be done")
        args = vars(ap.parse_args())

        # initialize database into memory
        cur.execute("SELECT * From files")
        print(cur.fetchall())

        # iterate through all input files
        # for each file scan top right of sheet ((w/2, 0, w, h/8))
        # if top left of sheet contains "test" its a concrete break sheet
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

        # if top left of sheet contains "placement" it is a placement sheet
        # if top left of sheet contains "field or density" it is a density report

        ################################################################################################################
        # Concrete break sheet "test" important locations
        # Set no. Location - (100, 675, 300, 750)
        # Standard break sheet - Age at test Location (450, 830, 620, 1100)
        # Standard break sheet - Compressive strength Location - (1150, 830, 1350, 1100)
        # Standard break sheet - date cast location - (1260, 710, 1475, 750)
        # Standard break sheet - project number location - (1100, 320, 1550, 360)
        ################################################################################################################

        for f in self.fileNames:

            # initialize variables in case some do not get detected
            project_number = "N/A"
            project_number_short = "N/A"
            set_number = "N/A"
            sheet_type = "N/A"
            date_cast = "N/A"
            break_ages = "N/A"
            sheet_type_file = "N/A"
            date_placed = "N/A"

            # Get path variable to save pdf files as same name but as .jpg
            f_jpg = f.replace(".pdf", ".jpg")
            # Get path variable to save entire sheet separately
            full_jpg = f.replace(".pdf", "-full.jpg")
            # Import images from file path "f" using pdf2image to open
            images_jpeg = convert_from_path(f)

            # convert PDF files into images for analyzing
            # Tesseract doesnt directly read from PDF files
            for image in images_jpeg:
                # Get image size to crop full page to top right corner
                # Top right corner is first to analyze as the large englobe logo messes up tesseract
                w, h = image.size
                # save top right corner image as jpg
                image.crop((1300, 0, 1700, h / 8)).save(f_jpg, 'JPEG')
                # save full image as .jpg
                image.save(full_jpg, 'JPEG')
            pre_process_image(f_jpg, args)

            # Using tesseract on top right corner image, try and detect what type of sheet it is
            text = analyze_image(f_jpg)

            # once analyzed, top right corner image is not required anymore, so delete
            os.remove(f_jpg)
            # debug, print resultant analysis text to screen
            if debug:
                print(text)

            # if top right image analysis yields "test" it is a concrete break sheet
            if text.lower().find("test") > 0 & text.lower().find("placement") <= 0:
                sheet_type = "break"
                sheet_type_file = "dConcStrength_S"
                # debug, print sheet type to screen
                if debug:
                    print(sheet_type)
                # Preprocess full image saved previously and analyze specific sections for remaining data
                pre_process_image(full_jpg, args)
                image = cv2.imread(full_jpg)
                # crop image to project number location
                cv2.imwrite(f_jpg, image[320:360, 1100:1550])
                # debug, show what project number image looks like to be analyzed
                if debug:
                    cv2.imshow("ProjectNumber", image[320:360, 1100:1550])
                    cv2.waitKey(0)
                # analyze project number image for project number
                project_number, project_number_short = detect_projectnumber(analyze_image(f_jpg))
                # debug, print the project number
                if debug:
                    print(project_number)
                    print(project_number_short)

                # crop image to set number location
                cv2.imwrite(f_jpg, image[675:750, 100:300])
                # debug, show what set number image looks like to be analyzed
                if debug:
                    cv2.imshow("Set Number", image[675:750, 100:300])
                    cv2.waitKey(0)
                # analyze set number image for set number
                set_number_text = analyze_image(f_jpg)
                if re.search(r"Set No: (\d+)\s", set_number_text, re.M + re.I) is not None:
                    set_number = re.search(r"Set No: (\d+)\s", set_number_text, re.M + re.I).groups()
                    set_number = set_number[-1]
                else:
                    set_number = "N/A"
                # for consistency, add 0 in front of single digit set numbers
                if len(set_number) < 2:
                    set_number = "0" + str(set_number)
                # debug, print the set number
                if debug:
                    print(set_number)

                # crop image to date cast location
                cv2.imwrite(f_jpg, image[710:750, 1260:1475])
                # debug, show what date cast image looks like to be analyzed
                if debug:
                    cv2.imshow("Date Cast:", image[710:750, 1260:1475])
                    cv2.waitKey(0)
                # analyze date cast image for date cast
                date_cast_text = analyze_image(f_jpg)
                if re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_cast_text, re.M | re.I) is not None:
                    date_cast = re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_cast_text, re.M + re.I).groups()
                    date_cast = date_cast[-1].replace("\n", "")
                else:
                    date_cast = "N/A"
                # debug, print the date cast
                if debug:
                    print(date_cast)

                # crop image to break strengths location
                cv2.imwrite(f_jpg, image[830:1100, 1150:1350])
                # debug, show what break strengths looks like to be analyzed
                if debug:
                    cv2.imshow("Break Strengths", image[830:1100, 1150:1350])
                    cv2.waitKey(0)
                # analyze break strengths for break strengths
                break_strengths_text = analyze_image(f_jpg)
                break_strengths = break_strengths_text.split("\n")
                # debug, print the break strengths
                if debug:
                    print(break_strengths)

                # crop image to latest break age location
                cv2.imwrite(f_jpg, image[830:1100, 450:620])
                # debug, show what latest break age looks like to be analyzed
                if debug:
                    cv2.imshow("Break Strengths", image[830:1100, 450:620])
                    cv2.waitKey(0)
                # analyze latest break age for age
                break_age_text = analyze_image(f_jpg)
                break_ages = break_age_text.split("\n")
                # debug, print the latest break age
                if debug:
                    print(break_ages)
                if len(break_strengths) > 0:
                    break_ages = break_ages[len(break_strengths) - 1]
                else:
                    break_ages = break_ages[0]
                if debug:
                    print(break_ages)

            elif text.lower().find("placement") > 0:
                sheet_type = "placement"
                sheet_type_file = "_ConcretePlacement("
                # debug, print sheet type to screen
                if debug:
                    print(sheet_type)
                # Preprocess full image saved previously and analyze specific sections for remaining data
                pre_process_image(full_jpg, args)
                image = cv2.imread(full_jpg)
                # crop image to project number location
                cv2.imwrite(f_jpg, image[310:350, 1050:1550])
                # debug, show what project number image looks like to be analyzed
                if debug:
                    cv2.imshow("ProjectNumber", image[310:350, 1050:1550])
                    cv2.waitKey(0)
                # analyze project number image for project number
                project_number, project_number_short = detect_projectnumber(analyze_image(f_jpg))
                # debug, print the project number
                if debug:
                    print(project_number)
                    print(project_number_short)

                # crop image to date placed location
                cv2.imwrite(f_jpg, image[700:740, 1250:1450])
                # debug, show what date placed image looks like to be analyzed
                if debug:
                    cv2.imshow("Date Cast:", image[700:740, 1250:1450])
                    cv2.waitKey(0)
                # analyze date placed image for date cast
                date_placed_text = analyze_image(f_jpg)
                if re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_placed_text, re.M | re.I) is not None:
                    date_placed = re.search(r"(\d+[\s-]+[A-z]{3}.*\d+)", date_placed_text, re.M + re.I).groups()
                    date_placed = date_placed[-1].replace("\n", "")
                else:
                    date_placed = "N/A"
                # debug, print the date cast
                if debug:
                    print(date_placed)

            # Need a way to determine package number
            package_number = "04"

            split_name = f.split("/").pop()
            if sheet_type == "placement":
                file_title = package_number + "-" + project_number_short + "_SomeProjDesc_" + sheet_type_file + \
                             date_placed + ").pdf"
                print_string = "Detected " + split_name + " as a " + sheet_type + " sheet - Project Number: " + project_number \
                               + " - date placed: " + date_placed + "\n"
            elif sheet_type == "break":
                file_title = package_number + "-" + project_number_short + "_SomeProjDesc_" + break_ages + \
                             sheet_type_file + set_number + "(" + date_cast.replace(" ", "-") + ").pdf"
                print_string = "Detected " + split_name + " as a " + sheet_type + " sheet - Project Number: " + project_number \
                               + " - set number: " + set_number + " - date cast: " + date_cast + "\n"
            else:
                file_title = "Sheet_Type_Not_Found_(" + split_name + ").pdf"
                print_string = "Sheet_Type_Not_Found_(" + split_name + ").pdf\n"

            if sheet_type == "break":
                params = [project_number_short, date_cast, sheet_type, set_number, break_ages]
            else:
                params = [project_number_short, date_placed, sheet_type, set_number, break_ages]
            # Turn "N/A" results into None results to help with sorting in sqlite3
            count = 1
            for item in params:
                if item == "N/A":
                    # tuples cannot be indexed and assigned values like this
                    params[count] = None
                count += 1
            cur.execute("INSERT INTO files VALUES(?,?,?,?,?)", params)
            db.commit()

            self.outputBox.appendPlainText(print_string)
            self.listWidgetItem = QtWidgets.QListWidgetItem(file_title)
            self.listWidgetItem.setData(QtCore.Qt.UserRole, f)
            self.listWidget.addItem(self.listWidgetItem)

            os.remove(full_jpg)
            os.remove(f_jpg)

        cur.execute("SELECT * From files")
        print(cur.fetchall())
        cur.execute("SELECT * From files ORDER BY Project, Type, Date, Set_No, Age")
        print(cur.fetchall())


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UiMainwindow()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
