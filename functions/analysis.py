import argparse
import os
import random
import shutil
import sqlite3

import cv2
import pytesseract
import regex as re
from PyQt5.QtCore import *
from pdf2image import convert_from_path

from functions.date_formater import date_formatter, months
from functions.project_info import json_projects, project_info
from functions.project_number import detect_project_number

# hard coded tesseract and poppler path from current working directory
tesseract_path = str(os.path.abspath(os.path.join(os.getcwd(), r"Tesseract\tesseract.exe")))
poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


def integer_test(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


break_strengths = []


# Exception rule to break out of multi-level for loops when trying to identify project numbers
class ItemFound(Exception):
    pass

class WorkerSignals(QObject):
    
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    progress = pyqtSignal(int)


class WorkerAnalyzeThread(QRunnable):

    def __init__(self, file_name, debug, analyzed):
        super(WorkerAnalyzeThread, self).__init__()
        self.f = file_name
        self.debug = debug
        self.analyzed = analyzed
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        # create a sqlite3 table in memory in order to easily sort and manipulate the analyzed results
        self.db = sqlite3.connect(':memory:')
        self.cur = self.db.cursor()
        self.cur.execute('''CREATE TABLE files (Project TEXT, Date DATE, Type TEXT, Set_No TEXT, Age INTEGER)''')
        # till dexter number identification uin place use 00000000
        global break_strengths
        dexter_number = "0000000"
        # Each pdf page is stored as image info in an array called images_jpg
        images_jpeg = convert_from_path(self.f, poppler_path=poppler_path)
        # initialize variables in case no pages detected, prevents crashing
        project_number = "NA"
        project_number_short = "NA"
        sheet_type = "NA"
        project_number_found = False
        # need to iterate through the image info array to analyze each individual image.
        for image in images_jpeg:
            # Set / reset count to 0 for appending file names
            count = 0
            # reset variables in case some do not get detected
            set_number_found = False
            break_strengths_bool = False
            set_number = "NA"
            sheet_type = "NA"
            date_cast = "NA"
            break_ages = "NA"
            date_placed = "NA"
            date_tested = "NA"
            date_asphalt_tested = "NA"
            sieve_date_tested = "NA"

            jpg_replace_string = str(count) + ".jpg"
            # Get path variable to save pdf files as same name but as .jpg
            f_jpg = self.f.replace(".pdf", jpg_replace_string)
            f_placement_jpg = self.f.replace(".pdf", jpg_replace_string.replace(".jpg", "placement.jpg"))
            # Get path variable to save entire sheet separately
            jpg_full_replace_string = "-full" + str(count) + ".jpg"
            full_jpg = self.f.replace(".pdf", jpg_full_replace_string)

            # convert PDF files into images for analyzing
            # Tesseract doesnt directly read from PDF files
            # Get image size to crop full page to top right corner
            # Top right corner is first to analyze as the large englobe logo messes up tesseract
            w, h = image.size
            if self.debug:
                print('Image size (w, h): ({0}, {1})'.format(w, h))
            # save top right corner image as jpg
            image.crop((1200, 0, 1700, h / 8)).save(f_jpg, 'JPEG')
            image.crop((550, 175, 1150, 225)).save(f_placement_jpg, "JPEG")
            # save full image as .jpg
            image.save(full_jpg, 'JPEG')

            self.pre_process_image(f_jpg)
            self.pre_process_image(f_placement_jpg)

            if self.debug:
                image_test = cv2.imread(f_placement_jpg)
                cv2.imshow("Top Corner", image_test)
                cv2.waitKey(0)
            # Using tesseract on top right corner image, try and detect what type of sheet it is
            text = self.analyze_image(f_jpg)

            text2 = self.analyze_image(f_placement_jpg)

            # once analyzed, top right corner image is not required anymore, so delete
            os.remove(f_jpg)
            os.remove(f_placement_jpg)

            # Preprocess full image saved previously and analyze specific sections for remaining data
            self.pre_process_image(full_jpg)
            image = cv2.imread(full_jpg)

            # if top right image analysis yields "test" it is a concrete break sheet
            if (text.lower().find("test report") > 0 or "grout" in text.lower()) and\
                    text.lower().find("lacement") <= 0:
                sheet_type = "3"  # 3 = break
                # debug, print sheet type to screen
                if self.debug:
                    print('Sheet Type: {0}'.format(sheet_type))

                # Once a project number is found in a package, it stops looking, which speeds up analysis
                coordinates = [[315, 350, 1150, 1475], [630, 670, 250, 350], [630, 670, 1270, 1450],
                               [760, 1200, 1200, 1320], [760, 1200, 400, 475]]
                names = ["project number", "set number", "date cast", "break_strengths", "break ages"]
                for i in range(5):
                    try:
                        for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                            y1 = int(coordinates[i][0] / scale)
                            y2 = int(coordinates[i][1] * scale)
                            x1 = int(coordinates[i][2] / scale)
                            x2 = int(coordinates[i][3] * scale)
                            if self.debug:
                                print('y1: {0}\ny2: {1}\nx1: {2}\nx2: {3}'.format(y1, y2, x1, x2))
                            if y2 > 2200:
                                y2 = 2150
                            if x2 > 1700:
                                x2 = 1650
                            # crop image to project number location
                            cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                            # debug, show what project number image looks like to be analyzed
                            if self.debug:
                                cv2.imshow(names[i], image[y1:y2, x1:x2])
                                cv2.waitKey(0)
                            result = self.analyze_image(f_jpg)

                            if i == 0:
                                if not project_number_found:
                                    # analyze project number image for project number
                                    project_number, project_number_short = detect_project_number(result)
                                    for json_project in json_projects:
                                        project_no_json_spaceless = json_project.replace(".", "").replace(" ", "")
                                        project_no_spaceless = project_number.replace(".", "").replace(" ", "")
                                        if project_number != "NA" and (project_number_short in json_project or
                                                                       project_number in json_project or
                                                                       project_no_json_spaceless == project_no_spaceless):
                                            if project_number[0] == "0":
                                                project_number = project_number[1:]
                                                project_number_short = project_number_short[1:]
                                            project_number_found = True
                                            raise ItemFound
                                            # debug, print the project number
                                if self.debug:
                                    print('Project Number: {0}\nProject Number Short: {1}'.format(project_number,
                                                                                                  project_number_short))
                            elif i == 1:
                                if not set_number_found:
                                    if re.search(r"(\d+)", result, re.M + re.I) is not None:
                                        set_number = re.search(r"(\d+)", result, re.M + re.I).groups()
                                        set_number = set_number[-1]
                                        set_number_found = True
                                    else:
                                        set_number = "NA"
                                        # for consistency, add 0 in front of single digit set numbers
                                        # print('Length set_no: {0}'.format(len(set_number)))
                                    if len(set_number) < 2:
                                        set_number = "0" + str(set_number)
                                        # debug, print the set number
                                    if self.debug:
                                        print('Set Number: {0}'.format(set_number))
                                    if set_number_found: break
                            elif i == 2:
                                if re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{4})", result, re.M | re.I) is not None:
                                    date_cast = re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{4})", result, re.M + re.I) \
                                        .groups()
                                    date_cast = date_cast[-1].replace("\n", "")
                                    break
                                else:
                                    date_cast = "NA"
                                # debug, print the date cast
                                if self.debug:
                                    print('Date Cast: {0}'.format(date_cast))
                            elif i == 3:
                                break_strengths = result.split("\n")
                                if break_strengths != "NA":
                                    try:
                                        break_strengths = [break_strength for break_strength in break_strengths if
                                                       integer_test(break_strength[0])]
                                    except:
                                        break_strengths = "NA"
                                    break
                                # debug, print the break strengths
                                if self.debug:
                                    print('Break Strengths: {0}'.format(break_strengths))
                            elif i == 4:
                                if not break_strengths_bool:
                                    for num, character in enumerate(result):
                                        if integer_test(character):
                                            result = result[num:]
                                            break
                                    result = result.replace("\f", "")
                                    break_ages = result.split("\n")
                                    break_ages = [break_age for break_age in break_ages if break_age != ""]
                                    break_strengths_bool = False
                                    if integer_test(break_ages[0]) or break_ages[0] == "AP":
                                        # debug, print the latest break age
                                        if self.debug:
                                            print('All Break Ages: {0}'.format(break_ages))
                                        if len(break_strengths) > 0:
                                            try:
                                                break_ages = break_ages[len(break_strengths) - 1]
                                                break_strengths_bool = True
                                                break
                                            except Exception as e:
                                                print(e)
                                                break_strengths_bool = False
                                            if not break_strengths_bool:
                                                try:
                                                    break_ages = break_ages[-1]
                                                except Exception as e:
                                                    print(e)
                                                    break_ages = '999'
                                        else:
                                            break_ages = break_ages[0]
                                        if break_ages != "NA" and (integer_test(break_ages) or break_ages == "AP"):
                                            if break_ages.upper() == "AP":
                                                break_ages = "56"
                                            break
                                if not break_strengths_bool:
                                    try:
                                        break_ages = break_ages[-1]
                                    except Exception as e:
                                        print(e)
                                        break_ages = '999'
                                if self.debug:
                                    print('Latest Break Age: {0}'.format(break_ages))
                    except ItemFound:
                        pass
            elif text.lower().find("placement") > 0 or text2.lower().find("lacement") > 0:
                coordinates = [[310, 340, 380, 660], [645, 680, 1280, 1420]]
                names = ["project number", "date placed"]
                sheet_type = "1"  # 1 = "placement"
                # debug, print sheet type to screen
                if self.debug:
                    print('Sheet Type: {0}'.format(sheet_type))
                for i in range(2):
                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(coordinates[i][0] / scale)
                        y2 = int(coordinates[i][1] * scale)
                        x1 = int(coordinates[i][2] / scale)
                        x2 = int(coordinates[i][3] * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        if self.debug:
                            print('y1: {0}\ny2: {1}\nx1: {2}\nx2: {3}'.format(y1, y2, x1, x2))
                        # crop image to project number location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what project number image looks like to be analyzed
                        if self.debug:
                            cv2.imshow(names[i], image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        results = self.analyze_image(f_jpg)
                        if i == 0:
                            if not project_number_found:
                                # analyze project number image for project number
                                project_number, project_number_short = detect_project_number(results)
                                for json_project in json_projects:
                                    if project_number != "NA" and (project_number_short in json_project or
                                                                   project_number in json_project):
                                        if project_number[0] == "0":
                                            project_number = project_number[1:]
                                            project_number_short = project_number_short[1:]
                                        project_number_found = True
                                        break
                            else:
                                break
                            # debug, print the project number
                            if self.debug:
                                print('Project Number: {0}\nProject Number Short: {1}'.format(project_number,
                                                                                              project_number_short))
                        elif i == 1:
                            # analyze date placed image for date placed
                            if re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})", results, re.M | re.I) is not None:
                                date_placed = re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})", results,
                                                        re.M + re.I).groups()
                                date_placed = date_placed[-1].replace("\n", "")
                                break
                            elif re.search(r"(\d{4}-\d{2}-\d{2})", results, re.M | re.I) is not None:
                                date_placed = re.search(r"(\d{4}-\d{2}-\d{2})", results, re.M + re.I) \
                                    .groups()
                                date_placed_list = date_placed[-1].split("-")
                                placed_month = ""
                                for (month, month_int) in months.items():
                                    if month_int == int(date_placed_list[1])-1:
                                        placed_month = month
                                        break
                                date_placed = f"{date_placed_list[2]}-{placed_month}-{date_placed_list[0]}"
                                date_placed = date_placed.replace("\n", "")
                                break
                            else:
                                date_placed = "NA"
                            # debug, print the date cast
                            if self.debug:
                                print('Date Placed: {0}'.format(date_placed))
            elif text.lower().find("density") > 0:
                sheet_type = "5"  # 5 = "field density"
                coordinates = [[290, 350, 1050, 1550], [660, 725, 300, 475]]
                names = ["project number", "date placed"]
                # debug, print sheet type to screen
                if self.debug:
                    print('Sheet Type: {0}'.format(sheet_type))
                for i in range(2):
                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(coordinates[i][0] / scale)
                        y2 = int(coordinates[i][1] * scale)
                        x1 = int(coordinates[i][2] / scale)
                        x2 = int(coordinates[i][3] * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        if self.debug:
                            print('y1: {0}\ny2: {1}\nx1: {2}\nx2: {3}'.format(y1, y2, x1, x2))
                        # crop image to project number location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what project number image looks like to be analyzed
                        if self.debug:
                            cv2.imshow(names[i], image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        results = self.analyze_image(f_jpg)
                        if i == 0:
                            if not project_number_found:
                                # analyze project number image for project number
                                project_number, project_number_short = detect_project_number(results)
                                for json_project in json_projects:
                                    if project_number != "NA" and (project_number_short in json_project or
                                                                   project_number in json_project):
                                        if project_number[0] == "0":
                                            project_number = project_number[1:]
                                            project_number_short = project_number_short[1:]
                                        project_number_found = True
                                        break
                            else:
                                break
                            # debug, print the project number
                            if self.debug:
                                print('Project Number: {0}\nProject Number Short: {1}'.format(project_number,
                                                                                              project_number_short))
                        if i == 1:
                            if re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})", results, re.M | re.I) is not None:
                                date_tested = re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})", results, re.M + re.I) \
                                    .groups()
                                date_tested = date_tested[-1].replace("\n", "")
                                break
                            else:
                                date_tested = "NA"
                            # debug, print the date cast
                            if self.debug:
                                print('Date Tested: {0}'.format(date_tested))
            elif text.lower().find("sieve") > 0:
                sheet_type = "9"  # 9 = "sieve sheet"
                coordinates = [[290, 350, 1050, 1550], [650, 700, 1350, 1550]]
                names = ["project number", "date placed"]
                # debug, print sheet type to screen
                if self.debug:
                    print('Sheet Type: {0}'.format(sheet_type))
                for i in range(2):
                    for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                        y1 = int(coordinates[i][0] / scale)
                        y2 = int(coordinates[i][1] * scale)
                        x1 = int(coordinates[i][2] / scale)
                        x2 = int(coordinates[i][3] * scale)
                        if y2 > 2200:
                            y2 = 2150
                        if x2 > 1700:
                            x2 = 1650
                        if self.debug:
                            print('y1: {0}\ny2: {1}\nx1: {2}\nx2: {3}'.format(y1, y2, x1, x2))
                        # crop image to project number location
                        cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                        # debug, show what project number image looks like to be analyzed
                        if self.debug:
                            cv2.imshow(names[i], image[y1:y2, x1:x2])
                            cv2.waitKey(0)
                        results = self.analyze_image(f_jpg)
                        if i == 0:
                            if not project_number_found:
                                # analyze project number image for project number
                                project_number, project_number_short = detect_project_number(results)
                                for json_project in json_projects:
                                    if project_number != "NA" and (project_number_short in json_project or
                                                                   project_number in json_project):
                                        if project_number[0] == "0":
                                            project_number = project_number[1:]
                                            project_number_short = project_number_short[1:]
                                        project_number_found = True
                                        break
                            else:
                                break
                            # debug, print the project number
                            if self.debug:
                                print('Project Number: {0}\nProject Number Short: {1}'.format(project_number,
                                                                                              project_number_short))

                        if i == 1:
                            if re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})", results, re.M | re.I) \
                                    is not None:
                                sieve_date_tested = re.search(r"(\d{2}[\s-]+[A-z]{3}[\s-]\d{2})", results,
                                                              re.M + re.I).groups()
                                sieve_date_tested = sieve_date_tested[-1].replace("\n", "")
                                break
                            else:
                                sieve_date_tested = "NA"
                        # debug, print the date cast
                        if self.debug:
                            print('Date Tested: {0}'.format(sieve_date_tested))

            if sheet_type == "1":  # 1 = placement sheet
                params = [project_number_short, date_placed, sheet_type, set_number, break_ages]
            elif sheet_type == "3":  # 3 = break sheet
                params = [project_number_short, date_cast, sheet_type, set_number, break_ages]
            elif sheet_type == "5":  # 5 = field density
                params = [project_number_short, date_tested, sheet_type, set_number, break_ages]
            elif sheet_type == "7":  # 7 = asphalt field density
                params = [project_number_short, date_asphalt_tested, sheet_type, set_number, break_ages]
            elif sheet_type == "9":  # 9 = sieve sheet
                params = [project_number_short, sieve_date_tested, sheet_type, set_number, break_ages]
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

            self.cur.execute("INSERT INTO files VALUES(?,?,?,?,?)", params)
            self.db.commit()
            count += 1

            if "2102060" in project_number_short:  # Dexter Project
                if sheet_type == "3":  # == break
                    coordinates = [1600, 1850, 610, 1550]
                else:
                    coordinates = [1600, 2000, 2500, 1550]
                for scale in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1]:
                    y1 = int(coordinates[0] / scale)
                    y2 = int(coordinates[1] * scale)
                    x1 = int(coordinates[2] / scale)
                    x2 = int(coordinates[3] * scale)
                    if y2 >= 2200:
                        y2 = 2150
                    if x2 >= 1700:
                        x2 = 1650
                    # crop image to date placed location
                    cv2.imwrite(f_jpg, image[y1:y2, x1:x2])
                    # debug, show what date placed image looks like to be analyzed
                    if self.debug:
                        cv2.imshow("Dexter Number:", image[y1:y2, x1:x2])
                        cv2.waitKey(0)

                    # analyze date placed image for date cast
                    dexter_number_text = self.analyze_image(f_jpg)
                    if re.search(r"(\d{7}[-\s]\d+)", dexter_number_text, re.M | re.I) is not None:
                        dexter_number = re.search(r"(\d{7}[-\s]\d+)", dexter_number_text, re.M + re.I) \
                            .groups()
                        dexter_number = dexter_number[-1].replace("\n", "")
                        break
                    elif re.search(r"(\d{7})", dexter_number_text, re.M | re.I) is not None:
                        dexter_number = re.search(r"(\d{7})", dexter_number_text, re.M + re.I) \
                            .groups()
                        dexter_number = dexter_number[-1].replace("\n", "")
                        break
                    else:
                        dexter_number = "NA"
                # debug, print the date cast
                if self.debug:
                    print('Dexter Number: {0}'.format(dexter_number))
            if os.path.isfile(full_jpg):
                os.remove(full_jpg)
            if os.path.isfile(f_jpg):
                os.remove(f_jpg)
        self.cur.execute("SELECT * From files")
        if self.debug:
            print(self.cur.fetchall())
        self.cur.execute("SELECT * From files ORDER BY Project, Type, Date, Set_No, Age")
        records = self.cur.fetchall()
        if self.debug:
            print(records)

        placement_string = ""
        break_string = ""
        density_string = ""
        asphalt_string = ""
        sieve_string = ""

        # For multi page files, some files may not detect project number properly
        # so iterate through all pages and get project number from a successful detection
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

        density_date_array = []
        # iterate through the local database records and if sheet type is density, store date placed into an array
        for i in range(0, len(records)):
            if records[i][2] == "5":  # 5 = density
                density_date_array.append(records[i][1])
        if density_date_array:
            density_date = date_formatter(density_date_array)
            density_string = '_FieldDensity({0})'.format(density_date)

        asphalt_date_array = []
        # iterate through the local database records and if sheet type is asphalt, store date placed into an array
        for i in range(0, len(records)):
            if records[i][2] == "7":  # 7 = asphalt
                asphalt_date_array.append(records[i][1])
        if asphalt_date_array:
            asphalt_date = date_formatter(asphalt_date_array)
            asphalt_string = '_FieldDensity({0})'.format(asphalt_date)

        sieve_date_array = []
        # iterate through the local database records and if sheet type is sieve, store date placed into an array
        for i in range(0, len(records)):
            if records[i][2] == "9":  # 9 = sieve
                sieve_date_array.append(records[i][1])
        if sieve_date_array:
            sieve_date = date_formatter(sieve_date_array)
            sieve_string = '_SA({0})'.format(sieve_date)

        # initialize/reset date_array for each new input file
        break_age_array = []

        # iterate through the local database records and if sheet type is break sheet, store date cast into an array
        # need to format dates for each possible age from 0 - 56
        for i in range(0, len(records)):
            if records[i][2] == "3" and records[i][4] not in break_age_array:  # 3 = break
                break_age_array.append(records[i][4])
        for i, result in enumerate(break_age_array):
            if result is None:
                break_age_array[i] = 999
        try:
            break_age_array.sort(key=int, reverse=True)
        except ValueError:
            pass
        for age in break_age_array:
            break_set_no = []
            break_set_string = ""
            break_date_array = []
            for i in range(0, len(records)):
                if records[i][4] == age:
                    break_date_array.append(records[i][1])
                    break_set_no.append(records[i][3])
            # Formats the set numbers for the filename, hyphenating consecutive numbers
            current_set = -1
            if break_set_no:
                if "None" in break_set_no or None in break_set_no:
                    break_set_no.sort(key=str)
                else:
                    break_set_no.sort(key=int)
                for k, temp_set in enumerate(break_set_no):
                    if k == 0:
                        break_set_string = str(temp_set)
                    else:
                        if temp_set is not None and temp_set != "None":
                            if int(temp_set) == int(current_set) + 1:
                                replace_string = "-" + current_set
                                break_set_string = break_set_string.replace(replace_string, "") + "-" + str(temp_set)
                            else:
                                break_set_string = break_set_string + "," + str(temp_set)
                    current_set = temp_set
            if break_date_array:
                break_date = date_formatter(break_date_array)
                break_string = break_string + '_{0}dConcStrength_S{1}({2})' \
                    .format(age, break_set_string.replace("None", "NA"), break_date)

        # Placeholder package number till directory system is in place
        # package_number = "04"

        project_number, project_number_short, project_description, file_path = project_info(project_number,
                                                                                            project_number_short,
                                                                                            self.f,
                                                                                            sheet_type,
                                                                                            self.analyzed)

        package_number_highest_str, package_numbers = detect_package_number(file_path, self.debug)
        if self.debug:
            print("Max value = {0}".format(max(package_numbers)))
        if "P-00" in project_number_short:
            project_number_short = project_number_short.replace("P-00", "P-")
        if "Dexter" in project_description:
            project_description = project_description.replace("%%", dexter_number)
        file_title = package_number_highest_str + "-" + str(project_number_short) + "_" + project_description

        split_name = self.f.split("/").pop()
        if placement_string != "":
            file_title = file_title + placement_string
        if break_string != "":
            file_title = file_title + break_string
        if density_string != "":
            file_title = file_title + density_string
        if asphalt_string != "":
            file_title = file_title + asphalt_string
        if sieve_string != "":
            file_title = file_title + sieve_string
        if placement_string == "" and break_string == "" and \
                density_string == "" and asphalt_string == "" and sieve_string == "":
            if "Sheet_Type_Not_Found" not in split_name:
                file_title = "Sheet_Type_Not_Found_(" + split_name + ")"
            else:
                file_title = split_name

        # Wont happen much in full use but may encounter same file names during testing
        # Just add a random integer at end of file for now
        os.chdir(file_path)
        rename_path = os.path.abspath(os.path.join(self.f.replace(self.f.split("/").pop(), ""), file_title + ".pdf"))
        rename_path_project_dir = os.path.abspath(os.path.join(file_path, file_title + ".pdf"))
        if len(str(rename_path)) > 260 or len(str(rename_path_project_dir)) > 260:
            file_title = file_title.replace("Concrete", "Conc")
            rename_path = os.path.abspath(
                os.path.join(self.f.replace(self.f.split("/").pop(), ""), file_title + ".pdf"))
            rename_path_project_dir = os.path.abspath(os.path.join(file_path, file_title + ".pdf"))
        if len(str(rename_path)) > 260 or len(str(rename_path_project_dir)) > 260:
            file_title = file_title.replace("-2021", "")
            file_title = file_title.replace("-2022", "")
            rename_path = os.path.abspath(
                os.path.join(self.f.replace(self.f.split("/").pop(), ""), file_title + ".pdf"))
            rename_path_project_dir = os.path.abspath(os.path.join(file_path, file_title + ".pdf"))
        if len(str(rename_path)) > 260 or len(str(rename_path_project_dir)) > 260:
            cut1 = len(str(rename_path)) - 256
            cut2 = len(str(rename_path_project_dir)) - 256
            if cut1 > cut2:
                file_title = file_title[:-cut1] + "LONG"
            else:
                file_title = file_title[:-cut2] + "LONG"
            rename_path = os.path.abspath(
                os.path.join(self.f.replace(self.f.split("/").pop(), ""), file_title + ".pdf"))
            rename_path_project_dir = os.path.abspath(os.path.join(file_path, file_title + ".pdf"))
        if os.path.isfile(rename_path) or os.path.isfile(rename_path_project_dir):
            file_title = file_title + str(random.randint(1, 999))
            rename_path = os.path.abspath(
                os.path.join(self.f.replace(self.f.split("/").pop(), ""), file_title + ".pdf"))
            rename_path_project_dir = os.path.abspath(os.path.join(file_path, file_title + ".pdf"))
        try:
            os.rename(self.f, rename_path)
        except Exception as e:
            print(e)
        if rename_path != rename_path_project_dir:
            try:
                shutil.copy(rename_path, rename_path_project_dir)
            except Exception as e:
                print(e)

        print_string = split_name + " renamed to " + file_title + " and saved in project folder:\n" + file_path + \
                       '\n'
        data = rename_path + "%%" + rename_path_project_dir
        returns = [print_string, file_title, data, project_number, project_number_short]
        self.cur.execute("DELETE From files")
        self.signals.progress.emit(100)
        self.signals.result.emit(returns)

    def analyze_image(self, img_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        # config_str = "-l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz " \
        # "0123456789 --psm " + str(psm_arg)
        config_str = "--psm " + str(6)
        text = pytesseract.image_to_string(img_path, config=config_str)
        # If debug enabled, print all detected text
        if self.debug:
            print(f"Text Found: {text}")
        return text

    def pre_process_image(self, path, age_detect=None):
        # construct the argument parse and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-p", "--preprocess", type=str, default="default",
                        help="type of pre-processing to be done")
        args = vars(ap.parse_args())

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
        if self.debug:
            cv2.imshow("Output", gray)
        # cv2.waitKey(0)
        cv2.imwrite(path, gray)
        return gray


def detect_package_number(file_path, debug):
    only_files = [f_local[0:6] for f_local in os.listdir(file_path) if "pdf" in f_local[-4:].lower()]

    package_number_highest_str = "01"
    package_numbers = []
    if only_files:
        for file in only_files:
            if re.search(r"(\d+)[-.][\dA-z]", file, re.I) is not None:
                package_number = re.search(r"(\d+)[-.][\dA-z]", file, re.I).groups()
                if debug:
                    print("package_number: {0}\npackage_number[-1]: {1}".format(package_number,
                                                                                package_number[-1]))
                package_numbers.append(int(package_number[-1]))
    if package_numbers:
        package_number_highest_str = str(max(package_numbers) + 1)
        if len(package_number_highest_str) < 2:
            package_number_highest_str = "0" + package_number_highest_str
    return package_number_highest_str, package_numbers
