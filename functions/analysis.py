"""
This module handles all of the document analysis
"""

import datetime
import io
import os
import random
import shutil

import pytesseract
import regex as re
from pdf2image import convert_from_path
from PySide6 import QtCore
from view_models import main_view_model
from typing import Any
import debugpy

from utils import utils

# from functions.date_formater import date_formatter, months
# from functions.project_info import project_info
# from functions.project_number import detect_project_number


# hard coded tesseract and poppler path from current working directory
tesseract_path = utils.resource_path("Tesseract/tesseract.exe")
# poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler/bin")))
poppler_path = f"{os.path.abspath('/usr/bin')}"
print(poppler_path)


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


# # Exception rule to break out of multi-level for loops when trying to identify project numbers
# class ItemFound(Exception):
#     pass
class AnalysisSignals(QtCore.QObject):
    analysis_result = QtCore.Signal(list)
    analysis_progress = QtCore.Signal(int)

class WorkerAnalyzeThread(QtCore.QRunnable):


    def __init__(self, file_name: str, main_view_model: main_view_model.MainViewModel, template: bool = False):
        super(WorkerAnalyzeThread, self).__init__()
        self.file = file_name
        self.file_dir_path = self.file.replace(self.file.split("/").pop(), "")
        self.template = template
        self.main_view_model = main_view_model
        self.signals = AnalysisSignals()

    @QtCore.Slot()
    def run(self):
        debugpy.debug_this_thread()
        # Each pdf page is stored as image info in an array called images_jpg
        images_jpeg = convert_from_path(
            self.file, fmt="jpeg", poppler_path=poppler_path, single_file=True)
        image = images_jpeg[0]
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='jpeg')
        img_byte_arr = img_byte_arr.getvalue()

        # For each image, connect to database and select all rows in profiles
        # Checking each unique id area for the unique identifier text
        # If identifier text found, the sheet is that type (return profile_id)
        file_type = self.find_file_profile(pdf_image=image)

        if self.template:
            self.signals.analysis_progress.emit(100)
            self.signals.analysis_result.emit([file_type])
            return

        if file_type == 0:
            file_title = self.file.replace(
                self.file_dir_path, "").replace(".pdf", "")
            print_string = f"No profile found for: {file_title}.pdf"
            returns = [print_string, file_title, self.file, None, None, file_type]
            self.signals.analysis_progress.emit(90)
            self.signals.analysis_result.emit(returns)
            return

        self.main_view_model.update_profile_used_count_by_profile_id(
            profile_id=file_type)
        parameter_data = self.find_parameter_data(
            profile_id=file_type, pdf_image=image)

        project_number = parameter_data.get("project_number")
        # If project_number specified in database, try to get directory info
        if project_number is not None:
            rename_path_project_dir = self.main_view_model.fetch_project_directory_by_project_number(
                project_number=project_number)
            if not rename_path_project_dir:

                project_numbers = self.main_view_model.fetch_all_project_numbers()
                project_directories = self.main_view_model.fetch_all_project_directories()
                for project_dir, temp_project_number in zip(project_directories, project_numbers):
                    if project_number in temp_project_number or temp_project_number in project_number:
                        rename_path_project_dir = project_dir
                        break

        doc_number = detect_package_number(
            self.file_dir_path, rename_path_project_dir)

        file_pattern = self.main_view_model.fetch_profile_file_name_pattern_by_profile_id(
            file_type)

        # If no file pattern just add each parameter value separated by hyphen
        # else format according to supplied pattern
        if file_pattern is None:
            new_file_name = f"{doc_number}"
            for key in parameter_data.keys():
                new_file_name += f"-{parameter_data[key]}"
        else:
            new_file_name = file_pattern
            new_file_name = new_file_name.replace("{doc_num}", doc_number)
            for key in parameter_data.keys():
                new_file_name = new_file_name.replace(
                    "".join(["{", key, "}"]), parameter_data[key])

        rename_path = os.path.abspath(os.path.join(
            self.file_dir_path, new_file_name + ".pdf"))

        if len(str(rename_path)) > 260:
            cut = len(str(rename_path)) - 256
            new_file_name = new_file_name[:-cut] + "LONG"
            rename_path = os.path.abspath(os.path.join(
                self.file_dir_path, new_file_name + ".pdf"))

        if os.path.isfile(rename_path):
            new_file_name = new_file_name[:-3] + str(random.randint(1, 999))
            rename_path = os.path.abspath(os.path.join(
                self.file_dir_path, new_file_name + ".pdf"))

        try:
            os.rename(self.file, rename_path)
        except Exception as e:
            print(f"Error renaming file in original location: {e}")

        if rename_path_project_dir is not None:
            try:
                shutil.copy(rename_path, rename_path_project_dir)
            except FileNotFoundError as e:
                file_name = rename_path.replace("\\", "/").split("/")[-1]
                if rename_path_project_dir == "":
                    self.main_view_model.add_console_text(f"No project directory found for {file_name}")
                else:
                    self.main_view_model.add_console_text(f"Error copying {file_name} to project directory: {rename_path_project_dir}")
                self.main_view_model.add_console_alerts(1)
            except shutil.SameFileError as e:
                pass


        rename_project_data_path = os.path.join(rename_path_project_dir, new_file_name + ".pdf")
        prev_file_name = self.file.split("/")[-1]
        print_string = f"{prev_file_name} renamed to {new_file_name}"
        returns = [print_string, new_file_name,
                   rename_path, rename_project_data_path, project_number, file_type]
        self.signals.analysis_progress.emit(90)
        self.signals.analysis_result.emit(returns)

    def find_file_profile(self, pdf_image: io.BytesIO) -> int:

        profiles = self.main_view_model.fetch_all_file_profiles(
            order_by="count")

        for file_profile in profiles:

            file_identifier_text = file_profile[1]
            active_profile_name = file_profile[2]
            file_id_x1 = file_profile[3]
            file_id_x2 = file_profile[4]
            file_id_y1 = file_profile[5]
            file_id_y2 = file_profile[6]
            file_pattern = file_profile[7]
            profile_count = file_profile[8]

            # crop image to file_profile location
            cropped_pdf_image = pdf_image.crop((file_id_x1, file_id_y1, file_id_x2,
                                                file_id_y2))

            # Using tesseract on cropped image, check if its equal to the unique_text
            text = self.analyze_image(cropped_pdf_image)
            if file_identifier_text.strip().lower() in self.main_view_model.scrub(text.replace("\n", " ")).strip().lower():
                file_type = file_profile[0]
                return file_type

        return 0

    def find_parameter_data(self, profile_id: int, pdf_image: io.BytesIO) -> dict:
        file_profile_parameters = self.main_view_model.fetch_active_parameters_by_profile_id(
            profile_id=profile_id)
        # Iterate through each location of each paramater
        data = {}
        for file_profile_parameter in file_profile_parameters[1:]:
            [x_1, x_2, y_1, y_2] = self.main_view_model.fetch_parameter_rectangle_by_name_and_profile_id(profile_id=profile_id, parameter_name=file_profile_parameter)
            parameter_regex = self.main_view_model.fetch_parameter_regex_by_parameter_name_and_profile_id(profile_id=profile_id, parameter_name=file_profile_parameter)
            for scale in [1.0, 1.01, 1.02, 1.03, 1.04, 1.05]:
                scaled_x_1 = int(x_1 / scale)
                scaled_x_2 = int(x_2 * scale)
                scaled_y_1 = int(y_1 / scale)
                scaled_y_2 = int(y_2 * scale)

                # crop image to desired location
                cropped_image = pdf_image.crop((scaled_x_1, scaled_y_1, scaled_x_2, scaled_y_2))

                result = self.analyze_image(cropped_image)

                if not parameter_regex:
                    data[file_profile_parameter] = self.main_view_model.scrub(result.replace(
                        "\n", "").replace(" ", "-").replace("---", "-").replace("--", "-"))
                    break
                print(f"regex: {parameter_regex}")
                data_point = re.search(
                    rf"{parameter_regex}", result, re.M + re.I)
                data[file_profile_parameter] = data_point
                if data_point is not None:
                    data_point = data_point.groups()
                    # Get rid of any extra hyphens, random spaces, new line characters, and then feed it into scrub to get rid of non alpha-numeric
                    data_point = self.main_view_model.scrub(
                        data_point[-1].replace("\n", "").replace(" ", "-").replace("---", "-").replace("--", "-"))
                    data[file_profile_parameter] = data_point
                    break
        return data

    def analyze_image(self, img_path):
        # pytesseract.pytesseract.tesseract_cmd = tesseract_path
        config_str = "--psm " + str(6)
        return pytesseract.image_to_string(img_path, config=config_str).strip()

# TODO : Look at speeding this up. Big time sink when folders have hundreds of files and analyzing multiple files at once.\
# Chances
def detect_package_number(file_path: str, project_file_path: str) -> str:
    """Checks project_file_path directory for all pdf files to determine the current document number. If unable it'll resort to checking file_path.

    Args:
        file_path (str): Path to original files directory
        project_file_path (str): Path to project files directory

    Returns:
        str: Document number for current file being analyzed
    """
    try:
        only_files = [f_local[0:6] for f_local in os.listdir(
            project_file_path) if "pdf" in f_local[-4:].lower()]
    except:
        only_files = [f_local[0:6] for f_local in os.listdir(
            file_path) if "pdf" in f_local[-4:].lower()]
        pass

    package_number_highest_str = "01"
    package_numbers = []
    if only_files:
        for file in only_files:
            try:
                package_number = re.search(
                    r"(\d+)[-.][\dA-z]", file, re.I).groups()
                package_numbers.append(int(package_number[-1]))
            except (re.error, AttributeError) as e:
                # print(f"Doc Num Regex Error: {e}")
                pass
    if package_numbers:
        package_number_highest_str = str(max(package_numbers) + 1)
        if len(package_number_highest_str) < 2:
            package_number_highest_str = "0" + package_number_highest_str
    return package_number_highest_str
