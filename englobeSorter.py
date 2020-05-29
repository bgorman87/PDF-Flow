from PyQt5 import QtCore, QtGui, QtWidgets
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import argparse
import cv2
import os
import regex as re


# Find all break sheets in selection and sort them by job number If multiple break sheets for single job number sort
# by set number If set number = N/A then sort it by date cast // May lead to a set being out of order but only by 1
# most likely Append ordered sets of each job number with placement sheets sorted by date placed or record number
# This is when the queue folder can be re-analyzed to see if any placement sheets can be sent out
# Sometimes there are sieves and other forms that are submitted at the end and these can be sorted by
# date or record number
# Output all backend stuff to textbox to keep user informed
# At end of analysis ensure potential issues are noted such as missing set no. or break dates

# Have yet to even begin attempting naming schemes


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
    elif re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M) is not None:
        project_number = re.search(r"(P[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M).groups()
        project_number = project_number[-1]
    elif re.search(r"(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text, re.M) is not None:
        project_number = re.search(r"(1\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d+[.-\s]+\d{3})", text,
                                   re.M).groups()
        project_number = project_number[-1]
    elif re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d{4})", text, re.M) is not None:
        project_number = re.search(r"([0-2]\d+[.-\s]+\d+[.-\s]\d+[.-\s]+\d{4})", text, re.M).groups()
        project_number = project_number[-1]
    else:
        project_number = "N/A"
    project_number = project_number.replace(" ", "")
    return project_number


# Perform image preprocessing based on image src and input args


def preprocess_image(path, args, age_detect=None):
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
    cv2.imshow("Output", gray)
    # cv2.waitKey(0)
    cv2.imwrite(path, gray)
    return gray


class UiMainwindow(object):

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
        self.selectQueueFolder.setWhatsThis(_translate("MainWindow", "Chnage the queue folder location"))
        self.selectQueueFolder.setText(_translate("MainWindow", "Change"))
        self.selectQueueFolder.clicked.connect(self.select_queue_folder_handler)
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
        file_folder_string = "Queue Folder save location set to: \n" + self.folderName
        self.outputBox.appendPlainText(file_folder_string)

    def open_queue_folder_handler(self):
        os.startfile(self.folderName)
        open_queue_folder_string = "\nOpening queue folder in separate window"
        self.outputBox.appendPlainText(open_queue_folder_string)

    def select_queue_folder_handler(self):
        self.open_folder_dialog()

    def update(self):
        self.queueLocation.setText(self.folderName)

    def analyze_button_handler(self):
        self.outputBox.appendPlainText("\nAnalyzing...")
        self.data_processing()

    def analyze_queue_button_handler(self):
        self.outputBox.appendPlainText("Analyzing Queue Folder...")

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

    def data_processing(self):

        # construct the argument parse and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-p", "--preprocess", type=str, default="default",
                        help="type of preprocessing to be done")
        args = vars(ap.parse_args())

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

            # convert PDF files into images
            f_jpg = f.replace(".pdf", ".jpg")
            full_jpg = f.replace(".pdf", "-full.jpg")
            images_jpeg = convert_from_path(f)

            for image in images_jpeg:
                w, h = image.size
                # Set No. Location
                image.crop((w / 2, 0, w, h / 8)).save(f_jpg, 'JPEG')
                image.save(full_jpg, 'JPEG')
            preprocess_image(f_jpg, args)

            # load the image as a PIL/Pillow image, apply OCR, and then delete
            # the temporary file and original image file

            text = analyze_image(f_jpg)

            # os.remove(filename)
            os.remove(f_jpg)
            print(text)

            if text.lower().find("test") > 0:
                sheet_type = "Concrete break sheet"
                print(sheet_type)
                preprocess_image(full_jpg, args)
                image = cv2.imread(full_jpg)
                cv2.imwrite(f_jpg, image[1100:1550, 320:360])
                project_number = detect_projectnumber(analyze_image(f_jpg))
                print(project_number)

            split_name = f.split("/").pop()
            if text.find("Date Placed:") > 0:
                if re.search(r"Date Placed: (\d{2}.[A-z]{3}.\d{2})", text, re.M | re.I) is not None:
                    date_placed = re.search(r"Date Placed: (\d{2}.[A-z]{3}.\d{2})", text, re.M | re.I).groups()
                    date_placed = date_placed[-1].replace("\n", "")
                else:
                    date_placed = "N/A"
                print_string = "\nDetected " + split_name + " as a placement sheet\nProject Number: " + projectNumber + \
                               "\nDate Placed: " + date_placed
            elif text.find("Date Cast:") > 0:
                if re.search(r"Date Cast: (\d{2}.*[A-z]{3}.*\d+)", text, re.M | re.I) is not None:
                    date_cast = re.search(r"Date Cast: (\d{2}.*[A-z]{3}.*\d+)", text, re.M | re.I).groups()
                    date_cast = date_cast[-1].replace("\n", "")
                else:
                    date_cast = "N/A"
                if re.search(r"Set No:.(\d*).", text, re.M | re.I) is not None:
                    set_no = re.search(r"Set No:.(\d*).", text, re.M | re.I).groups()
                    set_no = set_no[-1]
                else:
                    set_no = "N/A"
                print_string = "\nDetected " + split_name + " as a break sheet\nProject Number: " + projectNumber + \
                               "\nDate Cast: " + date_cast + "\nSet No: " + set_no
            else:
                print_string = "\nDetected " + split_name + " as neither a break or placement sheet:\nProject Number: "\
                               + projectNumber
            self.outputBox.appendPlainText(print_string)
            self.listWidgetItem = QtWidgets.QListWidgetItem(projectNumber)
            self.listWidgetItem.setData(QtCore.Qt.UserRole, f)
            self.listWidget.addItem(self.listWidgetItem)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UiMainwindow()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
