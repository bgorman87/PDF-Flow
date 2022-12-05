import argparse
import os
import io
import random
import shutil
import sqlite3
import datetime

import debugpy

import cv2
import pytesseract
import regex as re
from PyQt5.QtCore import *
from pdf2image import convert_from_path
from functions.data_handler import db_connect, db_file_path, db_disconnect, scrub, WorkerSignals

from functions.date_formater import date_formatter, months
from functions.project_info import project_info
from functions.project_number import detect_project_number


# hard coded tesseract and poppler path from current working directory
tesseract_path = str(os.path.abspath(
    os.path.join(os.getcwd(), r"Tesseract\tesseract.exe")))
poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler\bin")))


def valid_date(date_string):
    try:
        datetime.datetime.strptime(date_string, "%d %b %Y")
        return True
    except (ValueError, TypeError):
        return False


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


class WorkerAnalyzeThread(QRunnable):

    def __init__(self, file_name, test, analyzed):
        super(WorkerAnalyzeThread, self).__init__()
        self.file = file_name
        self.file_dir_path = self.file.replace(self.file.split("/").pop(), "")
        self.test = test
        self.analyzed = analyzed
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        debugpy.debug_this_thread()
        
        # Each pdf page is stored as image info in an array called images_jpg
        images_jpeg = convert_from_path(
                self.file, fmt="jpeg", poppler_path=poppler_path, single_file=True)

        # initialize variables in case no pages detected, prevents crashing
        sheet_type = "NA"
        project_number_found = False
        # need to iterate through the image info array to analyze each individual image.

        try:
            connection, cursor = db_connect(db_file_path)
            try:
                file_type_select_query = """SELECT * FROM profiles;"""
                profiles = cursor.execute(
                    file_type_select_query).fetchall()
            except Exception as e:
                print(e)
            finally:
                db_disconnect(connection, cursor)
        except ConnectionError as e:
            print(e)

        image = images_jpeg[0]
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='jpeg')
        img_byte_arr = img_byte_arr.getvalue()
       
        image_width, image_height = image.size

        # For each image, connect to database and select all rows in profiles
        # Checking each unique id area for the unique identifier text
        # If identifier text found, the sheet is that type (return profile_id)
        file_type = 0
        for file_profile in profiles:
            
            file_identifier_text = file_profile[1]
            file_id_x1 = file_profile[2]
            file_id_x2 = file_profile[3]
            file_id_y1 = file_profile[4]
            file_id_y2 = file_profile[5]
            description = file_profile[6]
            file_pattern = file_profile[7]

            # crop image to file_profile location
            cropped_image = image.crop((file_id_x1, file_id_y1, file_id_x2,
                                        file_id_y2))

            # Using tesseract on cropped image, check if its equal to the unique_text
            text = self.analyze_image(cropped_image)
            if file_identifier_text.strip().lower() in scrub(text).strip().lower():
                file_type = file_profile[0]
                break

        # If no file_profile set default values or return
        if file_type == 0:
            new_file_name = "No Profile - " + self.file.split("/").pop()[:-4]
            pass
        else:
            try:
                connection, cursor = db_connect(db_file_path)
                try:
                    file_type_select_query = """SELECT * FROM profile_paramaters WHERE profile_id=?;"""
                    file_profile_data_pieces = cursor.execute(
                        file_type_select_query, (file_type,)).fetchall()
                except Exception as e:
                    print(e)
                finally:
                    db_disconnect(connection, cursor)
            except ConnectionError as e:
                print(e)


            # Iterate through each location that desired data is expected
            data = {}
            for file_profile_data_piece in file_profile_data_pieces:
                for scale in [1.0, 1.01, 1.02, 1.03, 1.04, 1.05]:
                    x1 = int(file_profile_data_piece[4] / scale)
                    x2 = int(file_profile_data_piece[5] * scale)
                    y1 = int(file_profile_data_piece[6] / scale)
                    y2 = int(file_profile_data_piece[7] * scale)

                    # crop image to desired location
                    cropped_image = image.crop((x1, y1, x2, y2))
                    
                    result = self.analyze_image(cropped_image)
                    
                    if file_profile_data_piece[3] is None:
                        data[file_profile_data_piece[2]] = result
                        break
                    print(f"regex: {file_profile_data_piece[3]}")
                    data_point = re.search(
                        rf"{file_profile_data_piece[3]}", result, re.M + re.I)
                    data[file_profile_data_piece[2]] = data_point
                    if data_point is not None:
                        data_point = data_point.groups()
                        data_point = data_point[-1].replace("\n", "")
                        data[file_profile_data_piece[2]] = data_point
                        break

                    # TODO: Check which is faster: Detecting project number every time or selecting from Files DB first and chekcing if Project number already found
                    # if "project number" in file_profile[2]:
                    #     project_number, project_number_short = detect_project_number(
                    #         result)
                    #     try:
                    #         connection, cursor = db_connect(db_file_path)
                    #         try:
                    #             data_point = cursor.execute(
                    #                 f"SELECT project_number FROM project_data WHERE project_number='{scrub(project_number)}';").fetchone()
                    #             if result:
                    #                 data_point = data_point[0]
                    #                 raise ItemFound
                    #         except (TypeError, AttributeError) as e:
                    #             print(f"Project Detection Error: {e}")
                    #         finally:
                    #             db_disconnect(connection, cursor)
                    #     except ConnectionError as e:
                    #         print(
                    #             f"Project Detection DB Connection Error: {e}")
                    # # file_profile[3] = regex search string
                    # elif file_profile[3] is not None:
                    #     data_point = re.search(
                    #         rf"{file_profile[3]}", result, re.M + re.I)
                    #     if data_point is not None:
                    #         data_point = data_point.groups()
                    #         # print(data_point)
                    #         data_point = data_point[-1].replace("\n", "")
                    #         raise ItemFound

            doc_number = detect_package_number(self.file_dir_path)
            if file_pattern is None:
                new_file_name = f"{doc_number}"
                for key in data.keys():
                    new_file_name += f"-{data[key]}"
            else:
                new_file_name = file_pattern
                new_file_name = new_file_name.replace("{doc_num}", doc_number)
                for key in data.keys():
                    new_file_name = new_file_name.replace("".join(["{", key, "}"]), data[key])


        os.chdir(self.file_dir_path)
        rename_path = os.path.abspath(os.path.join(self.file_dir_path, new_file_name + ".pdf"))
        
        if len(str(rename_path)) > 260:
            cut = len(str(rename_path)) - 256
            new_file_name = new_file_name[:-cut] + "LONG"
            rename_path = os.path.abspath(os.path.join(self.file_dir_path, new_file_name + ".pdf"))

        if os.path.isfile(rename_path):
            new_file_name = new_file_name[:-3] + str(random.randint(1, 999))
            rename_path = os.path.abspath(os.path.join(self.file_dir_path, new_file_name + ".pdf"))

        try:
            os.rename(self.file, rename_path)
        except Exception as e:
            print(e)

        # if rename_path != rename_path_project_dir:
        #     try:
        #         shutil.copy(rename_path, rename_path_project_dir)
        #     except Exception as e:
        #         print(e)
        prev_file_name = self.file.split("/")[-1]
        print_string = f"{prev_file_name} renamed to {new_file_name}\n"
        returns = [print_string, new_file_name, rename_path]
        self.signals.progress.emit(100)
        self.signals.result.emit(returns)

    def analyze_image(self, img_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        config_str = "--psm " + str(6)
        return pytesseract.image_to_string(img_path, config=config_str).strip()


    # Preprocessing doesnt seem to help OCR results. Pending future removal.
    # def pre_process_image(self, path, age_detect=None):
    #     # construct the argument parse and parse the arguments
    #     ap = argparse.ArgumentParser()
    #     ap.add_argument("-p", "--preprocess", type=str, default="default",
    #                     help="type of pre-processing to be done")
    #     args = vars(ap.parse_args())

    #     # load the image and convert it to grayscale
    #     image = cv2.imread(path)
    #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #     # If sheet_type is none, then it is the first search trying to find sheet type
    #     if age_detect is not None:
    #         gray = cv2.resize(src=gray, dsize=(0, 0), fx=2.5,
    #                           fy=2.5, interpolation=cv2.INTER_LINEAR)
    #     # check to see if we should apply thresholding to preprocess the
    #     # image
    #     if args["preprocess"] == "thresh":
    #         gray = cv2.threshold(gray, 0, 255,
    #                              cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    #     # make a check to see if median blurring should be done to remove noise
    #     elif args["preprocess"] == "blur":
    #         gray = cv2.medianBlur(gray, 3)
    #     # perform threshold and blur
    #     elif args["preprocess"] == "default":
    #         gray = cv2.bitwise_not(gray)
    #         gray = cv2.threshold(gray, 0, 255,
    #                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    #         gray = cv2.medianBlur(gray, 3)

    #         kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    #         gray = cv2.erode(gray, kernel, iterations=1)
    #         gray = cv2.bitwise_not(gray)
    #     # perform canny edge detection
    #     elif args["preprocess"] == "canny":
    #         gray = cv2.Canny(gray, 100, 200)
    #     # write the grayscale image to disk as a temporary file so we can
    #     # apply OCR to it
    #     # filename = "{}.png".format(os.getpid())
    #     # cv2.imwrite(filename, gray)
    #     # cv2.imshow("Image", image)
    #     cv2.imwrite(path, gray)
    #     return gray

# TODO : Look at speeding this up. Big time sink when folders have hundreds of files and analyzing multiple files at once. 
def detect_package_number(file_path):
    """Checks file_path directory for all pdf files to determine the current document number

    Args:
        file_path (str): Patch to project files directory

    Returns:
        str: Document number for current file being analyzed
    """
    only_files = [f_local[0:6] for f_local in os.listdir(
        file_path) if "pdf" in f_local[-4:].lower()]

    package_number_highest_str = "01"
    package_numbers = []
    if only_files:
        for file in only_files:
            if re.search(r"(\d+)[-.][\dA-z]", file, re.I) is not None:
                package_number = re.search(
                    r"(\d+)[-.][\dA-z]", file, re.I).groups()
                package_numbers.append(int(package_number[-1]))
    if package_numbers:
        package_number_highest_str = str(max(package_numbers) + 1)
        if len(package_number_highest_str) < 2:
            package_number_highest_str = "0" + package_number_highest_str
    return package_number_highest_str


if __name__ == "__main__":
    print("This file is not meant to be run directly.")