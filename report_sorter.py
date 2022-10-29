import os
import shutil
import ctypes
import time


import regex as re
import win32com.client as win32
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from pdf2image import convert_from_path

from functions.analysis import WorkerAnalyzeThread, detect_package_number
from functions.data_handler import fetch_data, fetch_table_names, initialize_database
from functions.project_info import project_info, json_setup

debug = False

# set current working directory to variable to save files to
home_dir = os.getcwd()

# hard coded poppler path from current working directory
poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


def output(self):
    self.outputBox.appendPlainText("Analyzing...\n")


# noinspection PyTypeChecker
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        initialize_database()
        self.setObjectName("MainWindow")
        self.resize(850, 850)
        self.analyzeWorker = None  # Worker
        self.thread = None  # Thread
        self.fileNames = None  # Stores sleected file paths
        self.analyzed = False  # Stores analyzed state.
        self.progress = 0  # Initilize progress bar at 0
        self.project_numbers = []
        self.project_numbers_short = []
        # Displays how many threads can be utilized
        self.threadpool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" %
              self.threadpool.maxThreadCount())
        QtCore.QMetaObject.connectSlotsByName(self)

        # Used to place Tab Widget, Central Widget, and Creator Label
        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.layoutGrid = QtWidgets.QGridLayout(self.centralwidget)

        self.setCentralWidget(self.centralwidget)
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setObjectName("status bar")
        self.statusBar().setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)

        #-# Start of Tab Initialization #-#

        # Stores different tabs
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layoutGrid.addWidget(self.tabWidget, 0, 0, 1, 1)
        
        # Creator Label
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("creatorLabel")
        self.layoutGrid.addWidget(self.label, 1, 0, 1, 3)

        # Input Tab (Tab 1)
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")

        # Layout for Tab 1
        self.gridLayout = QtWidgets.QGridLayout(self.tab)
        self.gridLayout.setObjectName("gridLayout")

        # Line above action buttons
        self.line = QtWidgets.QFrame(self.tab)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 2, 0, 1, 8)

        # Action buttons on Input tab
        self.SelectFiles = QtWidgets.QPushButton(self.tab)
        self.SelectFiles.clicked.connect(self.select_files_handler)
        self.SelectFiles.setObjectName("SelectFiles")
        self.dialog = QtWidgets.QFileDialog()  # Used for file dialog popup
        self.gridLayout.addWidget(self.SelectFiles, 3, 0, 1, 2)

        # Action button to start file analysis
        self.analyzeButton = QtWidgets.QPushButton(self.tab)
        self.analyzeButton.clicked.connect(self.analyze_button_handler)
        self.analyzeButton.setObjectName("analyzeButton")
        self.gridLayout.addWidget(self.analyzeButton, 3, 2, 1, 2)

        # Action button to start email process
        self.emailButton = QtWidgets.QPushButton(self.tab)
        self.emailButton.clicked.connect(self.email_button_handler)
        self.emailButton.setObjectName("emailButton")
        self.gridLayout.addWidget(self.emailButton, 3, 4, 1, 2)

        # Drop list box to choose analysis type (Live/Test)
        # Live uses real client info, test uses dummy/local info
        self.testBox = QtWidgets.QComboBox(self.tab)
        self.testBox.setObjectName("testBox")
        self.gridLayout.addWidget(self.testBox, 3, 6, 1, 1)
        self.testBox.setEditable(True)
        self.testBox.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.testBox.addItems(["Test", "Live"])
        self.testBox.setEditable(False)

        # Box to create global debug variable
        # When checked additional info will display during analysis
        self.debugBox = QtWidgets.QCheckBox(self.tab)
        self.debugBox.setObjectName("debugBox")
        self.gridLayout.addWidget(self.debugBox, 3, 7, 1, 1)

        # Line below action buttons
        self.line_2 = QtWidgets.QFrame(self.tab)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.gridLayout.addWidget(self.line_2, 4, 0, 1, 8)

        # Output box to display info to user
        self.outputBox = QtWidgets.QPlainTextEdit(self.tab)
        self.outputBox.setObjectName("outputBox")
        self.outputBox.setReadOnly(True)
        self.gridLayout.addWidget(self.outputBox, 5, 0, 1, 8)

        # Progress bar to show analyze progress
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setStyle(QtWidgets.QStyleFactory.create("GTK"))
        self.progressBar.setTextVisible(False)
        self.gridLayout.addWidget(self.progressBar, 6, 0, 1, 8)

        # Output Tab (Tab 2)
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")

        # Layout for Tab 2
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_2.setObjectName("gridLayout_2")

        # Label for list widget below
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setGeometry(QtCore.QRect(10, 10, 81, 16))
        self.label_4.setObjectName("combinedFilesLabel")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 2)

        # Widget to hold analyzed files
        self.listWidget = QtWidgets.QListWidget(self.tab_2)
        self.listWidget.setGeometry(QtCore.QRect(10, 30, 320, 100))
        self.listWidget.setObjectName("listWidget")
        self.gridLayout_2.addWidget(self.listWidget, 1, 0, 5, 5)

        # Lines within the analyzed files widget above
        self.listWidgetItem = QtWidgets.QListWidgetItem()
        self.listWidget.itemClicked.connect(self.list_widget_handler)
        self.listWidget.itemDoubleClicked.connect(self.rename_file_handler)

        # Text editor line to edit file names
        self.fileRename = QtWidgets.QLineEdit(self.tab_2)
        self.fileRename.setObjectName("file rename")
        self.gridLayout_2.addWidget(self.fileRename, 6, 0, 1, 4)

        # Action button to call rename function
        self.fileRenameButton = QtWidgets.QPushButton(self.tab_2)
        self.fileRenameButton.clicked.connect(self.file_rename_button_handler)
        self.fileRenameButton.setObjectName("fileRenameButton")
        self.gridLayout_2.addWidget(self.fileRenameButton, 6, 4, 1, 1)

        # Title for JPG/PDF preview below
        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.label_3.setGeometry(QtCore.QRect(10, 140, 100, 16))
        self.label_3.setObjectName("pdfOutputLabel")
        self.gridLayout_2.addWidget(self.label_3, 7, 0, 1, 2)
        
        # Displays JPG of entire PDF
        # self.graphicsView = QtWidgets.QGraphicsView(self.tab_2)
        # self.graphicsView.setGeometry(QtCore.QRect(10, 160, 320, 400))
        # self.graphicsView.setObjectName("graphicsView")
        # self.gridLayout_2.addWidget(self.graphicsView, 8, 0, 20, 5)
        # self.graphicsView.setViewportUpdateMode(
        #     QtWidgets.QGraphicsView.FullViewportUpdate)

        # Displays PDF
        self.web = QtWebEngineWidgets.QWebEngineView()
        _qtweb_settings = QtWebEngineWidgets.QWebEngineSettings
        self.web.settings().setAttribute(_qtweb_settings.PluginsEnabled, True)
        self.web.settings().setAttribute(_qtweb_settings.PdfViewerEnabled, True)
        self.gridLayout_2.addWidget(self.web, 8, 0, 20, 5)

        ## Database Tab (Tab 3)
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.tabWidget.addTab(self.tab_3, "")

        # Layout for Tab 3
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_3)
        self.gridLayout_3.setObjectName("gridLayout_3")
        
        # Table widget to display DB results
        self.table = QtWidgets.QTableWidget()
        self.gridLayout_3.addWidget(self.table, 1, 0, 5, 4)
        
        self.database_table = QtWidgets.QComboBox(self.tab_3)
        self.database_table.setObjectName("database_table")
        self.gridLayout_3.addWidget(self.database_table, 6, 0, 1, 1)
        self.database_table.setEditable(True)
        self.database_table.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.database_table.addItems(fetch_table_names())
        self.database_table.setEditable(False)

        self.database_results = QtWidgets.QPushButton(self.tab_3)
        self.database_results.setObjectName("DatabaseResults")
        self.database_results.clicked.connect(self.database_fetch)
        self.gridLayout_3.addWidget(self.database_results, 6, 1, 1, 3)

        #-# End of Tab Initialization #-#
        
        # Translate UI if in another language
        self.translate_ui()

        # Set tab order (Can probably include more in future)
        self.setTabOrder(self.SelectFiles, self.analyzeButton)
        self.setTabOrder(self.analyzeButton, self.outputBox)
        self.setTabOrder(self.outputBox, self.tab)
        self.setTabOrder(self.tab, self.tab_2)
        self.setTabOrder(self.tab_2, self.tab_3)

        # Once finished initializing, show
        self.show()

    progress_update = QtCore.pyqtSignal(int)

    def translate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        
        self.setWindowTitle(_translate("MainWindow", "Report Sorter"))
        self.database_results.setText(_translate("MainWindow", "Fetch Table Results"))
        
        self.label.setText(_translate(
            "MainWindow", "Created By Brandon Gorman"))
        self.label_3.setText(_translate("MainWindow", "File Output Viewer:"))
        self.label_4.setText(_translate("MainWindow", "Combined Files:"))

        self.SelectFiles.setText(_translate("MainWindow", "Select Files"))
        self.fileRenameButton.setWhatsThis(_translate(
            "MainWindow", "Rename the currently selected file"))
        self.fileRenameButton.setText(_translate("MainWindow", "Rename"))
        self.analyzeButton.setText(_translate("MainWindow", "Analyze"))
        self.emailButton.setText(_translate("MainWindow", "E-Mail"))
        
        self.debugBox.setText(_translate("MainWindow", "Debug"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab), _translate("MainWindow", "Input"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_2), _translate("MainWindow", "Output"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_3), _translate("MainWindow", "Database"))

    def database_fetch(self):
        self.database_worker = fetch_data(self.database_table.currentText())
        self.database_worker.signals.result.connect(
                self.display_data)
        self.threadpool.start(self.database_worker)


    def display_data(self, data):
        self.table.setRowCount(0)
        try:
            data[0]
        except IndexError:
            self.table.setColumnCount(1)
            self.table.setItem(0,0,QtWidgets.QTableWidgetItem("No Data"))
            return
        
        self.table.setColumnCount(len(data[0]))
        for row, row_data in enumerate(data):
            self.table.insertRow(row)
            for column, item in enumerate(row_data):
                self.table.setItem(row, column, QtWidgets.QTableWidgetItem(str(item)))  


    def email_button_handler(self):
        signature_path = os.path.abspath(os.path.join(
            home_dir + r"\\Signature\\concrete.htm"))
        signature_path_28 = os.path.abspath(os.path.join(
            home_dir + r"\\Signature\\concrete28.htm"))
        if not self.analyzed and self.fileNames:
            if os.path.isfile(signature_path):
                with open(signature_path, "r") as file:
                    body_text = file.read()
                with open(signature_path_28, "r") as file:
                    body_text_28 = file.read()

            else:
                print("Signature File Not Found")
                body_text = ""
                pass
            msg = QtWidgets.QMessageBox()
            button_reply = msg.question(msg, "", "Do you want to create e-mails for non-analyzed files?",
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if button_reply == QtWidgets.QMessageBox.No:
                self.outputBox.appendPlainText("E-Mails not generated\n")
            elif button_reply == QtWidgets.QMessageBox.Yes:
                json_setup(self.testBox.currentText())
                for file in self.fileNames:
                    description = file.split("_")
                    description = description[1]
                    project_number, project_number_short, email_recipient_to, \
                        email_recipient_cc, email_recipient_subject = project_info(f=file,
                                                                                   analyzed=self.analyzed,
                                                                                   description=description)
                    title = file.split("/").pop()
                    attachment = file
                    if "Dexter" in email_recipient_subject:
                        dexter_number = "NA"
                        if re.search(r"Dexter_([\d-]*)[_\dA-z]", email_recipient_subject, re.I) is not None:
                            dexter_number = re.search(r"Dexter_([\d-]*)[_\dA-z]", email_recipient_subject,
                                                      re.I).groups()
                            dexter_number = dexter_number[-1]
                        email_recipient_subject = email_recipient_subject.replace(
                            "%%", dexter_number)
                    try:
                        outlook = win32.Dispatch('outlook.application')
                        mail = outlook.CreateItem(0)
                        mail.To = email_recipient_to
                        mail.CC = email_recipient_cc
                        mail.Subject = email_recipient_subject
                        if "28d" in title:
                            mail.HtmlBody = body_text_28
                        else:
                            mail.HtmlBody = body_text
                        mail.Attachments.Add(attachment)
                        mail.Save()
                        e = "Drafted email for: {0}".format(title)
                        self.outputBox.appendPlainText(e)
                    except Exception as e:
                        print(e)
                        self.outputBox.appendPlainText(e)
                        pass
        if self.analyzed:
            if os.path.isfile(signature_path):
                with open(signature_path, "r") as file:
                    body_text = file.read()
                with open(signature_path_28, "r") as file:
                    body_text_28 = file.read()
            else:
                print("Signature File Not Found")
                body_text = ""
                pass
            all_list_titles = []
            all_list_data = []
            for i in range(self.listWidget.count()):
                all_list_data.append(self.listWidget.item(
                    i).data(QtCore.Qt.UserRole).split("%%")[0])
                all_list_titles.append(self.listWidget.item(i).text())
            for i, project_number in enumerate(self.project_numbers):
                if self.project_numbers_short[i][0] == "P":
                    self.project_numbers_short[i] = self.project_numbers_short[i].replace(
                        "P-", "P-00")
                project_number, project_number_short, \
                    recipients, recipients_cc, subject = project_info(project_number, self.project_numbers_short[i],
                                                                      all_list_data[i], None, self.analyzed)
                attachment = all_list_data[i]
                if "Dexter" in subject:
                    dexter_number = "NA"
                    if re.search(r"Dexter_([\d-]*)[_\dA-z]", all_list_titles[i], re.I) is not None:
                        dexter_number = re.search(
                            r"Dexter_([\d-]*)[_\dA-z]", all_list_titles[i], re.I).groups()
                        dexter_number = dexter_number[-1]
                    subject = subject.replace("%%", dexter_number)
                try:
                    outlook = win32.Dispatch('outlook.application')
                    mail = outlook.CreateItem(0)
                    mail.To = recipients
                    mail.CC = recipients_cc
                    mail.Subject = subject
                    if "28d" in attachment:
                        mail.HtmlBody = body_text_28
                    else:
                        mail.HtmlBody = body_text
                    mail.Attachments.Add(attachment)
                    mail.Save()
                    e = "Drafted email for: {0}".format(all_list_titles[i])
                    self.outputBox.appendPlainText(e)
                except Exception as e:
                    print(e)
                    self.outputBox.appendPlainText(str(e))
                    pass

    def debug_check(self):
        global debug
        if self.debugBox.isChecked():
            debug = True
        else:
            debug = False

    def select_files_handler(self):
        self.open_file_dialog()

    def open_file_dialog(self):
        self.dialog = QtWidgets.QFileDialog(directory=str(
            os.path.abspath(os.path.join(os.getcwd(), "test_files"))))
        self.fileNames, filters = QtWidgets.QFileDialog.getOpenFileNames()

        tuple(self.fileNames)
        if len(self.fileNames) == 1:
            file_names_string = "(" + str(len(self.fileNames)) + \
                ")" + " file has been selected: \n"
        else:
            file_names_string = "(" + str(len(self.fileNames)) + \
                ")" + " files have been selected: \n"
        for item in self.fileNames:
            file_names_string = file_names_string + item + "\n"
        self.outputBox.appendPlainText(file_names_string)

    def rename_file_handler(self):
        if self.listWidget.isPersistentEditorOpen(self.listWidget.currentItem()):
            self.listWidget.closePersistentEditor(
                self.listWidget.currentItem())
            self.listWidget.editItem(self.listWidget.currentItem())
        else:
            self.listWidget.editItem(self.listWidget.currentItem())

    def file_rename_button_handler(self):
        file_path = self.listWidget.currentItem().data(QtCore.Qt.UserRole).split("%%")
        file_path_transit_src = file_path[0]
        # Project path may be changed if project number updated so declare up here
        file_path_project_src = file_path[1]

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
            old_project_number = re.search(
                r"-([\dPBpb\.-]+)_", old_title, re.I).groups()
            old_project_number = old_project_number[-1]
        elif re.search(r"-(NA)_", old_title, re.I) is not None:
            old_project_number = "NA"
        if re.search(r"-([\dPBpb\.-]+)_", new_title, re.I) is not None:
            new_project_number = re.search(
                r"-([\dPBpb\.-]+)_", new_title, re.I).groups()
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
            updated_file_details = old_title.replace(
                "SomeProjectDescription", description)
            updated_package = detect_package_number(
                file_path_project_src, debug)[0]
            updated_file_details = updated_file_details.replace(
                old_package, updated_package)
            updated_file_details = updated_file_details.replace(
                old_project_number, project_number_short)
            rename_transit_len = 260 - len(
                str(file_path_transit_src.replace(file_path_transit_src.split("\\").pop(), "")))
            rename_project_length = 260 - len(str(file_path_project_src))
            if len(updated_file_details) > rename_transit_len or len(updated_file_details) > rename_project_length:
                updated_file_details = updated_file_details.replace(
                    "Concrete", "Conc")
            if len(updated_file_details) > rename_transit_len or len(updated_file_details) > rename_project_length:
                updated_file_details = updated_file_details.replace(
                    "-2022", "")
                updated_file_details = updated_file_details.replace(
                    "-2021", "")
            if len(updated_file_details) > rename_transit_len or len(updated_file_details) > rename_project_length:
                if rename_project_length > rename_transit_len:
                    cut = rename_project_length + 4
                else:
                    cut = rename_transit_len + 4
                updated_file_details = updated_file_details.replace(".pdf", "")
                updated_file_details = updated_file_details[:-cut] + "LONG.pdf"
            rename_path_transit = os.path.abspath(os.path.join(
                file_path_transit_src.replace(
                    file_path_transit_src.split("\\").pop(), ""),
                updated_file_details + ".pdf"))
            rename_path_project = os.path.abspath(os.path.join(
                file_path_project_src, updated_file_details + ".pdf"))
            os.rename(file_path_transit_src, rename_path_transit)
            if not os.path.isfile(file_path_project_src):
                file_path_project_src = rename_path_project
            if os.path.isfile(file_path_project_src):
                if file_path_project_src != file_path_transit_src:
                    os.rename(file_path_project_src, rename_path_project)
            else:
                shutil.copy(rename_path_transit, rename_path_project)
            self.listWidget.currentItem().setText(updated_file_details)
            data = rename_path_transit + "%%" + rename_path_project
            self.listWidget.currentItem().setData(QtCore.Qt.UserRole, data)
            self.fileRename.setText(updated_file_details)
            self.project_numbers_short[self.listWidget.currentRow(
            )] = project_number_short
            self.project_numbers[self.listWidget.currentRow()] = project_number
        else:
            # 254 to accommodate the .pdf
            rename_transit_len = 254 - \
                len(file_path_transit_src.replace(
                    file_path_transit_src.split("\\").pop(), ""))
            rename_project_len = 254 - \
                len(file_path_project_src.replace(
                    file_path_project_src.split("\\").pop(), ""))
            if len(self.fileRename.text()) > rename_transit_len or len(self.fileRename.text()) > rename_project_len:
                print("Filename too long")
                if rename_transit_len > rename_project_len:
                    msg_string = f"Filename too long. Reduce by {len(self.fileRename.text()) - rename_transit_len}"
                else:
                    msg_string = f"Filename too long. Reduce by {len(self.fileRename.text()) - rename_project_len}"
                ctypes.windll.user32.MessageBoxW(
                    0, msg_string, "Filename Too Long", 1)
            else:
                rename_path_transit = os.path.abspath(os.path.join(
                    file_path_transit_src.replace(
                        file_path_transit_src.split("\\").pop(), ""),
                    str(self.fileRename.text()) + ".pdf"))
                rename_path_project = os.path.abspath(os.path.join(
                    file_path_project_src.replace(
                        file_path_project_src.split("\\").pop(), ""),
                    str(self.fileRename.text()) + ".pdf"))
                try:
                    os.rename(file_path_transit_src, rename_path_transit)
                except Exception:
                    pass
                if file_path_project_src != file_path_transit_src:  # If project and transit aren't the same, rename
                    try:
                        os.rename(file_path_project_src, rename_path_project)
                    except Exception:
                        pass
                self.listWidget.currentItem().setText(self.fileRename.text())
                if debug:
                    print('Renamed File Path: \n{0}\n{1}'.format(
                        file_path_transit_src, file_path_project_src))
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
        self.progressBar.setValue(int(self.progress / len(self.fileNames)))

    def analyze_button_handler(self):
        if self.fileNames is not None:
            json_setup(self.testBox.currentText())
            self.debug_check()
            self.analyzed = False
            self.progress = 0
            self.progressBar.setValue(0)
            self.outputBox.appendPlainText("Analysis Started...\n")
            self.data_processing()
            self.analyzed = True
        else:
            self.outputBox.appendPlainText(
                "Please select at least 1 file to analyze...\n")
        self.analyzeButton.setEnabled(True)

    def analyze_queue_button_handler(self):
        self.outputBox.appendPlainText("Analyzing Queue Folder...\n")

    def list_widget_handler(self):
        file_path = str(self.listWidget.currentItem().data(
            QtCore.Qt.UserRole)).split("%%")
        file_path_transit_src = file_path[0].replace("\\", "/")
        self.web.load(QtCore.QUrl(f"file:{file_path_transit_src}"))
        self.web.show()
        set_text = file_path_transit_src.split(
                "/").pop().replace(".pdf", "")
        self.fileRename.setText(set_text)
        
        
    # def list_widget_handler(self):
    #     file_path = str(self.listWidget.currentItem().data(
    #         QtCore.Qt.UserRole)).split("%%")
    #     file_path_transit_src = file_path[0]
    #     image_jpeg = []
    #     try:
    #         image_jpeg = convert_from_path(
    #             file_path_transit_src, fmt="jpeg", poppler_path=poppler_path)
    #     except Exception as e:
    #         print(e)
    #     if image_jpeg:
    #         result = Image.new("RGB", (1700, len(image_jpeg) * 2200))
    #         scene = QtWidgets.QGraphicsScene()
    #         for count, temp in enumerate(image_jpeg, 1):
    #             x = 0
    #             y = (count - 1) * 2200
    #             result.paste(temp, (x, y))
    #         name_jpeg = file_path_transit_src.replace(".pdf", ".jpg")
    #         result.save(name_jpeg, 'JPEG')
    #         pix = QtGui.QPixmap(name_jpeg)
    #         pix = pix.scaledToWidth(self.graphicsView.width())
    #         item = QtWidgets.QGraphicsPixmapItem(pix)
    #         scene.addItem(item)
    #         self.graphicsView.setScene(scene)
    #         os.remove(name_jpeg)
    #         set_text = file_path_transit_src.split(
    #             "\\").pop().replace(".pdf", "")
    #         self.fileRename.setText(set_text)
    #     else:
    #         print("image_jpeg list is empty")

    def data_processing(self):
        # iterate through all input files
        # for each file scan top right of sheet ((w/2, 0, w, h/8))
        # if top right of sheet contains "test" it's a concrete break sheet
        # pre-process entire image
        # from preprocessed image - crop to (1100,320, 1550, 360)
        # search resultant tesseract data for project_number
        # from preprocessed image - crop to (100, 675, 300, 750)
        # search resultant tesseract data for set_no
        # from preprocessed image - crop to (1260, 710, 1475, 750)
        # search resultant tesseract data for date_cast
        # from preprocessed image - crop to (1150, 830, 1350, 1100)
        # search resultant tesseract data for compressive strengths
        # split results by \n, last value in stored split should be the most recent break result
        # from preprocessed image - crop to (450, 830, 620, 1100)
        # search resultant tesseract data for age of cylinders when broken
        # split results by \n, find result in split equal to len(compressive_strength[splitdata])
        # this should return age of most recent broken cylinder

        # Import images from file path "f" using pdf to image to open
        for file_name in self.fileNames:
            self.analyzeWorker = WorkerAnalyzeThread(
                file_name=file_name, debug=debug, analyzed=self.analyzed)
            self.analyzeWorker.signals.progress.connect(
                self.evt_analyze_progress)
            self.analyzeWorker.signals.result.connect(
                self.evt_analyze_complete)
            # thread_pool.start(WorkerAnalyzeThread)
            self.threadpool.start(self.analyzeWorker)


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    window = MainWindow()
    app.exec_()
