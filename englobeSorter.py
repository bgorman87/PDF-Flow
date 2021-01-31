import os
import shutil

import regex as re
import win32com.client as win32
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from pdf2image import convert_from_path

from analysis import WorkerAnalyzeThread, detect_package_number
from project_info import project_info, json_setup

debug = False

# todo:- For dexter number rerun dexter number analysis
#           - asphalt sheets
#           - Make saving like e-mail, done after analyzing and editing the filename so that I wont have to deal
#               with crash issues
#           - Handle name too long errors PRIORITY
#           - Email button maybe looks at project number and creates email off that if previous analysis was done
#               this way I can load already named/analyzed files, and create emails


# set current working directory to variable to save files to
home_dir = os.getcwd()

print(os.getcwd())
# hard coded poppler path from current working directory
poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


def output(self):
    self.outputBox.appendPlainText("Analyzing...\n")


class UiMainwindow(object):

    def __init__(self):
        self.analyzeWorker = None
        self.fileNames = None
        self.analyzed = False
        self.progress = 0
        self.centralwidget = QtWidgets.QWidget()
        self.layoutGrid = QtWidgets.QGridLayout()
        self.tabWidget = QtWidgets.QTabWidget()
        self.label = QtWidgets.QLabel()
        self.tab = QtWidgets.QWidget()
        self.progressBar = QtWidgets.QProgressBar()
        self.gridLayout = QtWidgets.QGridLayout(self.tab)
        self.SelectFiles = QtWidgets.QPushButton(self.tab)
        self.line = QtWidgets.QFrame(self.tab)
        self.line_2 = QtWidgets.QFrame(self.tab)
        self.analyzeButton = QtWidgets.QPushButton(self.tab)
        self.emailButton = QtWidgets.QPushButton(self.tab)
        self.testBox = QtWidgets.QComboBox(self.tab)
        self.debugBox = QtWidgets.QCheckBox(self.tab)
        self.tab_2 = QtWidgets.QWidget()
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab_2)
        self.outputBox = QtWidgets.QPlainTextEdit(self.tab)
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.listWidget = QtWidgets.QListWidget(self.tab_2)
        self.fileRename = QtWidgets.QLineEdit(self.tab_2)
        self.fileRenameButton = QtWidgets.QPushButton(self.tab_2)
        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.graphicsView = QtWidgets.QGraphicsView(self.tab_2)
        self.status_bar = QtWidgets.QStatusBar()
        self.dialog = QtWidgets.QFileDialog()
        self.listWidgetItem = QtWidgets.QListWidgetItem()
        self.project_numbers = []
        self.project_numbers_short = []

    progress_update = QtCore.pyqtSignal(int)

    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.resize(650, 650)
        main_window.statusBar().setSizeGripEnabled(False)

        self.centralwidget = QtWidgets.QWidget(main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.layoutGrid = QtWidgets.QGridLayout(self.centralwidget)

        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layoutGrid.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("creatorLabel")
        self.layoutGrid.addWidget(self.label, 1, 0, 1, 3)

        self.tab.setObjectName("tab")
        self.gridLayout.setObjectName("gridLayout")

        self.SelectFiles.setObjectName("SelectFiles")
        self.gridLayout.addWidget(self.SelectFiles, 3, 0, 1, 2)

        self.outputBox.setObjectName("outputBox")
        self.outputBox.setReadOnly(True)
        self.gridLayout.addWidget(self.outputBox, 5, 0, 1, 8)

        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 2, 0, 1, 8)

        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 4, 0, 1, 8)

        self.analyzeButton.setObjectName("analyzeButton")
        self.gridLayout.addWidget(self.analyzeButton, 3, 2, 1, 2)

        self.emailButton.setObjectName("emailButton")
        self.gridLayout.addWidget(self.emailButton, 3, 4, 1, 2)

        self.testBox.setObjectName("testBox")
        self.gridLayout.addWidget(self.testBox, 3, 6, 1, 1)
        self.testBox.setEditable(True)
        self.testBox.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self.testBox.addItems(["Test", "Live"])
        self.testBox.setEditable(False)

        self.debugBox.setObjectName("debugBox")
        self.gridLayout.addWidget(self.debugBox, 3, 7, 1, 1)

        self.progressBar.setObjectName("progressBar")
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setStyle(QtWidgets.QStyleFactory.create("GTK"))
        self.progressBar.setTextVisible(False)
        self.gridLayout.addWidget(self.progressBar, 6, 0, 1, 8)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.label_4.setGeometry(QtCore.QRect(10, 10, 81, 16))
        self.label_4.setObjectName("combinedFilesLabel")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 2)

        self.listWidget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        self.listWidget.setObjectName("listWidget")
        self.gridLayout_2.addWidget(self.listWidget, 1, 0, 5, 5)

        self.fileRename.setObjectName("file rename")
        self.gridLayout_2.addWidget(self.fileRename, 6, 0, 1, 4)

        self.fileRenameButton.setObjectName("fileRenameButton")
        self.gridLayout_2.addWidget(self.fileRenameButton, 6, 4, 1, 1)

        self.label_3.setGeometry(QtCore.QRect(10, 140, 100, 16))
        self.label_3.setObjectName("pdfOutputLabel")
        self.gridLayout_2.addWidget(self.label_3, 7, 0, 1, 2)

        self.graphicsView.setGeometry(QtCore.QRect(10, 160, 320, 400))
        self.graphicsView.setObjectName("graphicsView")
        self.gridLayout_2.addWidget(self.graphicsView, 8, 0, 20, 5)
        self.graphicsView.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)

        self.tabWidget.addTab(self.tab_2, "")
        self.tabWidget.raise_()
        self.label.raise_()

        main_window.setCentralWidget(self.centralwidget)
        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("status bar")
        main_window.setStatusBar(self.status_bar)

        self.translate_ui(main_window)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(main_window)

        main_window.setTabOrder(self.SelectFiles, self.analyzeButton)
        main_window.setTabOrder(self.analyzeButton, self.outputBox)
        main_window.setTabOrder(self.outputBox, self.tab)
        main_window.setTabOrder(self.tab, self.tab_2)

    def translate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "Englobe Sorter"))
        self.label.setText(_translate("MainWindow", "Created By Brandon Gorman"))
        self.SelectFiles.setText(_translate("MainWindow", "Select Files"))
        self.SelectFiles.clicked.connect(self.select_files_handler)
        self.fileRenameButton.setWhatsThis(_translate("MainWindow", "Rename the currently selected file"))
        self.fileRenameButton.setText(_translate("MainWindow", "Rename"))
        self.fileRenameButton.clicked.connect(self.file_rename_button_handler)
        self.analyzeButton.setText(_translate("MainWindow", "Analyze"))
        self.analyzeButton.clicked.connect(self.analyze_button_handler)
        self.emailButton.setText(_translate("MainWindow", "E-Mail"))
        self.debugBox.setText(_translate("MainWindow", "Debug"))
        self.emailButton.clicked.connect(self.email_button_handler)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Input"))
        self.label_3.setText(_translate("MainWindow", "File Output Viewer:"))
        self.label_4.setText(_translate("MainWindow", "Combined Files:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Output"))
        self.listWidget.itemClicked.connect(self.list_widget_handler)
        self.listWidget.itemDoubleClicked.connect(self.rename_file_handler)

    def email_button_handler(self):
        if self.analyzed:
            signature_path = os.path.abspath(os.path.join(home_dir + r"\\Signature\\CONCRETE.htm"))
            if os.path.isfile(signature_path):
                with open(signature_path, "r") as file:
                    body_text = file.read()
            else:
                print("Signature File Not Found")
                pass
            all_list_titles = []
            all_list_data = []
            for i in range(self.listWidget.count()):
                all_list_data.append(self.listWidget.item(i).data(QtCore.Qt.UserRole).split("%%")[0])
                all_list_titles.append(self.listWidget.item(i).text())
            for i, project_number in enumerate(self.project_numbers):
                if self.project_numbers_short[i][0] == "P":
                    self.project_numbers_short[i] = self.project_numbers_short[i].replace("P-", "P-00")
                project_number, project_number_short, \
                recipients, recipients_cc, subject = project_info(project_number, self.project_numbers_short[i],
                                                                  all_list_data[i], None, self.analyzed)
                attachment = all_list_data[i]
                if "Dexter" in subject:
                    dexter_number = "NA"
                    if re.search(r"Dexter_([\d-]*)[_\dA-z]", all_list_titles[i], re.I) is not None:
                        dexter_number = re.search(r"Dexter_([\d-]*)[_\dA-z]", all_list_titles[i], re.I).groups()
                        dexter_number = dexter_number[-1]
                    subject = subject.replace("%%", dexter_number)
                try:
                    outlook = win32.Dispatch('outlook.application')
                    mail = outlook.CreateItem(0)
                    mail.To = recipients
                    mail.CC = recipients_cc
                    mail.Subject = subject
                    mail.HtmlBody = body_text
                    mail.Attachments.Add(attachment)
                    mail.Save()
                    e = "Drafted email for: {0}".format(all_list_titles[i])
                except Exception as e:
                    print(e)
                    pass
                self.outputBox.appendPlainText(e)
        else:
            self.outputBox.appendPlainText("There aren't any analyzed files to e-mail.")

    def debug_check(self):
        global debug
        if self.debugBox.isChecked():
            debug = True
        else:
            debug = False

    def select_files_handler(self):
        self.open_file_dialog()

    def open_file_dialog(self):
        self.dialog = QtWidgets.QFileDialog(directory=str(os.path.abspath(os.path.join(os.getcwd(), r"..\.."))))
        self.fileNames, filters = QtWidgets.QFileDialog.getOpenFileNames()

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
        file_path = self.listWidget.currentItem().data(QtCore.Qt.UserRole).split("%%")
        file_path_transit_src = file_path[0]
        file_path_project_src = file_path[1]  # Project path may be changed if project number updated so declare up here

        # See if project number is the edited string. If it is and description is == "SomeProjectDescription"
        # Then the project was previously not detected properly so assume the project edit is correct and find
        # details in the JSON file.
        # Before renaming occurs Old data = entry in the listWidget
        #                        New data = entry in the text edit box
        description = "SomeProjectDescription"
        old_project_number = ""
        new_project_number = ""
        project_number = ""
        project_number_short = ""
        old_package = ""
        old_title = self.listWidget.currentItem().text()
        project_details_changed = False
        new_title = self.fileRename.text()
        if re.search(r"-([\dPBpb\.-]+)_", old_title, re.I) is not None:
            old_project_number = re.search(r"-([\dPBpb\.-]+)_", old_title, re.I).groups()
            old_project_number = old_project_number[-1]
        elif re.search(r"-(NA)_", old_title, re.I) is not None:
            old_project_number = "NA"
        if re.search(r"-([\dPBpb\.-]+)_", new_title, re.I) is not None:
            new_project_number = re.search(r"-([\dPBpb\.-]+)_", new_title, re.I).groups()
            new_project_number = new_project_number[-1]
        if old_project_number != new_project_number:
            project_number, project_number_short, \
            description, file_path_project_src = project_info(new_project_number, new_project_number,
                                                              file_path_transit_src, None, False)
            project_details_changed = True
        if re.search(r"(\d+)-[\dA-z]", old_title, re.I) is not None:
            old_package = re.search(r"(\d+)-[\dA-z]", old_title, re.I).groups()
            old_package = old_package[-1]

        if project_details_changed:
            updated_file_details = old_title.replace("SomeProjectDescription", description)
            updated_package = detect_package_number(file_path_project_src, debug)[0]
            updated_file_details = updated_file_details.replace(old_package, updated_package)
            updated_file_details = updated_file_details.replace(old_project_number, project_number_short)
            rename_path_transit = os.path.abspath(os.path.join(
                file_path_transit_src.replace(file_path_transit_src.split("\\").pop(), ""),
                updated_file_details + ".pdf"))
            rename_path_project = os.path.abspath(os.path.join(file_path_project_src, updated_file_details + ".pdf"))
            os.rename(file_path_transit_src, rename_path_transit)
            if not os.path.isfile(file_path_project_src):
                file_path_project_src = rename_path_project
            if os.path.isfile(file_path_project_src):
                if file_path_project_src != file_path_transit_src:
                    os.rename(file_path_project_src, rename_path_project)
            else:
                shutil.copy(rename_path_transit, rename_path_project)
            self.listWidget.currentItem().setText(updated_file_details)
            self.fileRename.setText(updated_file_details)
            self.project_numbers_short[self.listWidget.currentRow()] = project_number_short
            self.project_numbers[self.listWidget.currentRow()] = project_number
        else:
            rename_path_transit = os.path.abspath(os.path.join(
                file_path_transit_src.replace(file_path_transit_src.split("\\").pop(), ""),
                str(self.fileRename.text()) + ".pdf"))
            rename_path_project = os.path.abspath(os.path.join(
                file_path_project_src.replace(file_path_project_src.split("\\").pop(), ""),
                str(self.fileRename.text()) + ".pdf"))
            os.rename(file_path_transit_src, rename_path_transit)
            if file_path_project_src != file_path_transit_src:  # If project and transit aren't the same, rename
                os.rename(file_path_project_src, rename_path_project)
            self.listWidget.currentItem().setText(self.fileRename.text())
        if debug:
            print('Renamed File Path: \n{0}\n{1}'.format(file_path_transit_src, file_path_project_src))
        data = rename_path_transit + "%%" + rename_path_project
        self.listWidget.currentItem().setData(QtCore.Qt.UserRole, data)

    def evt_analyze_complete(self, results):
        print_string = results[0]
        file_title = results[1]
        data = results[2]
        project_number = results[3]
        project_number_short = results[4]
        self.outputBox.appendPlainText(print_string)
        self.listWidgetItem = QtWidgets.QListWidgetItem(file_title)
        self.listWidgetItem.setData(QtCore.Qt.UserRole, data)
        self.listWidget.addItem(self.listWidgetItem)
        self.project_numbers.append(project_number)
        self.project_numbers_short.append(project_number_short)

    def evt_analyze_progress(self, val):
        self.progress += val
        self.progressBar.setValue(int(self.progress/len(self.fileNames)))

    def analyze_button_handler(self):
        if self.fileNames is not None:
            json_setup(self.testBox.currentText())
            self.debug_check()
            self.analyzed = False
            self.data_processing()
            self.analyzed = True
        else:
            self.outputBox.appendPlainText("Please select at least 1 file to analyze...\n")
        self.analyzeButton.setEnabled(True)

    def analyze_queue_button_handler(self):
        self.outputBox.appendPlainText("Analyzing Queue Folder...\n")

    def list_widget_handler(self):
        file_path = str(self.listWidget.currentItem().data(QtCore.Qt.UserRole)).split("%%")
        file_path_transit_src = file_path[0]
        image_jpeg = []
        try:
            image_jpeg = convert_from_path(file_path_transit_src, fmt="jpeg", poppler_path=poppler_path)
        except Exception as e:
            print(e)
        if image_jpeg:
            result = Image.new("RGB", (1700, len(image_jpeg) * 2200))
            scene = QtWidgets.QGraphicsScene()
            for count, temp in enumerate(image_jpeg, 1):
                x = 0
                y = (count - 1) * 2200
                result.paste(temp, (x, y))
            name_jpeg = file_path_transit_src.replace(".pdf", ".jpg")
            result.save(name_jpeg, 'JPEG')
            pix = QtGui.QPixmap(name_jpeg)
            pix = pix.scaledToWidth(self.graphicsView.width())
            item = QtWidgets.QGraphicsPixmapItem(pix)
            scene.addItem(item)
            self.graphicsView.setScene(scene)
            os.remove(name_jpeg)
            set_text = file_path_transit_src.split("\\").pop().replace(".pdf", "")
            self.fileRename.setText(set_text)
        else:
            print("image_jpeg list is empty")

    def data_processing(self):
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
            self.analyzeWorker = WorkerAnalyzeThread(f, debug, self.analyzed)
            self.analyzeWorker.analyze_complete.connect(self.evt_analyze_complete)
            self.analyzeWorker.analyze_progress.connect(self.evt_analyze_progress)
            self.analyzeWorker.start()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UiMainwindow()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
