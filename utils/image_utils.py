import os
import regex as re
from PySide6 import QtCore, QtWidgets
from pdf2image import convert_from_path
import fitz
from utils.path_utils import resource_path
import io
import random
import shutil
import pytesseract
from view_models import main_view_model
import regex as re
import debugpy
from utils import text_utils


def detect_package_number(file_path: str, project_file_path: str = None) -> str:
    """Checks project_file_path directory for all pdf files to determine the current document number. If unable it'll resort to checking file_path.

    Args:
        file_path (str): Path to original files directory
        project_file_path (str): Path to project files directory

    Returns:
        str: Document number for current file being analyzed
    """
    try:
        only_files = [
            f_local[0:6]
            for f_local in os.listdir(project_file_path)
            if "pdf" in f_local[-4:].lower()
        ]
    except:
        only_files = [
            f_local[0:6]
            for f_local in os.listdir(file_path)
            if "pdf" in f_local[-4:].lower()
        ]
        pass

    package_number_highest_str = "01"
    package_numbers = []
    if only_files:
        for file in only_files:
            try:
                package_number = re.search(r"(\d+)[-.][\dA-z]", file, re.I).groups()
                package_numbers.append(int(package_number[-1]))
            except (re.error, AttributeError) as e:
                # print(f"Doc Num Regex Error: {e}")
                pass
    if package_numbers:
        package_number_highest_str = str(max(package_numbers) + 1)
        if len(package_number_highest_str) < 2:
            package_number_highest_str = "0" + package_number_highest_str
    return package_number_highest_str


# hard coded tesseract and poppler path from current working directory
tesseract_path = resource_path(os.path.join("Tesseract", "tesseract.exe"))
poppler_path = resource_path(os.path.join("poppler", "bin"))
# poppler_path = str(os.path.abspath(os.path.join(os.getcwd(), r"poppler/bin")))
# poppler_path = f"{os.path.abspath('/usr/bin')}"


class AnalysisSignals(QtCore.QObject):
    analysis_result = QtCore.Signal(list)
    analysis_progress = QtCore.Signal(int)


class WorkerAnalyzeThread(QtCore.QRunnable):
    def __init__(self, file_name: str, main_view_model: main_view_model.MainViewModel , template: bool = False):
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
            self.file, fmt="jpeg", poppler_path=poppler_path, single_file=True
        )
        image = images_jpeg[0]
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="jpeg")
        img_byte_arr = img_byte_arr.getvalue()

        # doc = fitz.open(self.file)
        # page = doc.load_page(0)  # Load the first page (index 0)
        # image = page.get_pixmap()
        # doc.close()
        # img_byte_arr = io.BytesIO(image.pil_tobytes("png"))
        # # image.save(img_byte_arr, format="jpeg")
        # img_byte_arr = img_byte_arr.getvalue()

        # For each image, connect to database and select all rows in profiles
        # Checking each unique id area for the unique identifier text
        # If identifier text found, the sheet is that type (return profile_id)
        file_type = self.find_file_profile(pdf_image=image)

        if self.template:
            self.signals.analysis_progress.emit(100)
            self.signals.analysis_result.emit([file_type])
            return

        if file_type == 0:
            file_title = self.file.replace(self.file_dir_path, "").replace(".pdf", "")
            print_string = f"No profile found for: {file_title}.pdf"
            returns = [print_string, file_title, self.file, None, None, file_type]
            self.signals.analysis_progress.emit(90)
            self.signals.analysis_result.emit(returns)
            return

        self.main_view_model.update_profile_used_count_by_profile_id(
            profile_id=file_type
        )
        parameter_data = self.find_parameter_data(profile_id=file_type, pdf_image=image)

        project_number = parameter_data.get("project_number")
        # If project_number specified in database, try to get directory info
        if project_number is not None:
            rename_path_project_dir = (
                self.main_view_model.fetch_project_directory_by_project_number(
                    project_number=project_number
                )
            )
            if not rename_path_project_dir:
                project_numbers = self.main_view_model.fetch_all_project_numbers()
                project_directories = (
                    self.main_view_model.fetch_all_project_directories()
                )
                for project_dir, temp_project_number in zip(
                    project_directories, project_numbers
                ):
                    if (
                        project_number in temp_project_number
                        or temp_project_number in project_number
                    ):
                        rename_path_project_dir = project_dir
                        break
            project_description = self.main_view_model.fetch_project_description_by_project_number(
                project_number=project_number
            )
        else:
            rename_path_project_dir = ""
            project_description = ""

        file_pattern = (
            self.main_view_model.fetch_profile_file_name_pattern_by_profile_id(
                file_type
            )
        )

        # If no file pattern just add each parameter value separated by hyphen
        # else format according to supplied pattern
        if file_pattern is None:

            new_file_name = "-".join(map(str,[parameter_data[key] for key in parameter_data.keys()]))

        else:

            new_file_name = file_pattern

            if "{doc_num}" in new_file_name:
                doc_number = detect_package_number(self.file_dir_path, rename_path_project_dir)
                new_file_name = new_file_name.replace("{doc_num}", doc_number)

            if "{project_description}" in new_file_name:
                if project_number is None:
                    project_description = ""
                else:
                    project_description = self.main_view_model.fetch_project_description_by_project_number(
                        project_number=project_number
                    )
                    if project_description is None:
                        project_description = ""
                    new_file_name = new_file_name.replace(
                        "{project_description}", project_description
                    )

            for key in parameter_data.keys():
                new_file_name = new_file_name.replace(
                    "".join(["{", key, "}"]), parameter_data[key]
                )

        rename_path = os.path.abspath(
            os.path.join(self.file_dir_path, new_file_name + ".pdf")
        )
        rename_path = self.rename_file(self.file, rename_path)

        # if os.path.isfile(rename_path):
        #     # TODO: Implement proper event looping for the below

        #     # message_box = QtWidgets.QMessageBox()
        #     # message_box.setWindowTitle("File Already Exists")
        #     # message_box.setText(
        #     #     f"File {new_file_name} already exists in this directory. Would you like to overwrite it?"
        #     # )
        #     # message_box.setStandardButtons(
        #     #     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        #     # )
        #     # message_box.setDefaultButton(QtWidgets.QMessageBox.No)
        #     # message_box.setIcon(QtWidgets.QMessageBox.Warning)
            
        #     # if message_box.exec():
        #     #     self.file = self.rename_file(self.file, rename_path)
        
        rename_project_data_path = ""
        if rename_path_project_dir:
            try:
                shutil.copy(rename_path, rename_path_project_dir)
                rename_project_data_path = os.path.join(
                    rename_path_project_dir, new_file_name + ".pdf"
                )
            except FileNotFoundError as e:
                file_name = os.path.basename(rename_path)
                if rename_path_project_dir == "":
                    self.main_view_model.add_console_text(
                        f"No project directory found for {file_name}"
                    )
                else:
                    self.main_view_model.add_console_text(
                        f"Error copying {file_name} to project directory: {rename_path_project_dir}"
                    )
                self.main_view_model.add_console_alerts(1)
            except shutil.SameFileError as e:
                pass

        
        prev_file_name = os.path.basename(self.file)
        print_string = f"{prev_file_name} renamed to {new_file_name}"
        returns = [
            print_string,
            new_file_name,
            rename_path,
            rename_project_data_path,
            project_number,
            file_type,
        ]
        self.signals.analysis_progress.emit(90)
        self.signals.analysis_result.emit(returns)

    def generate_unique_filename(self, rename_path, extension=".pdf"):
        # Extract the base filename and directory from the absolute path
        dir_name = os.path.dirname(rename_path)
        base_name = os.path.splitext(os.path.basename(rename_path))[0]
        
        # Counter for appending to the file name
        counter = 1
        
        # Check if the path exists, and if so, increment counter and try again
        while os.path.isfile(rename_path):
            new_name = f"{base_name}({counter}){extension}"
            rename_path = os.path.join(dir_name, new_name)
            counter += 1

        return rename_path

    def rename_file(self, current_name: str, new_name: str, extension: str=".pdf") -> str:
        MAX_PATH_LENGTH = 253
        dir_name = os.path.dirname(new_name)
        base_name = os.path.splitext(os.path.basename(new_name))[0]
        
        if len(new_name) > MAX_PATH_LENGTH:
            cut_length = len(new_name) - (MAX_PATH_LENGTH - len("LONG") - len(extension) - 1)
            base_name = base_name[:-cut_length] + "LONG"
            new_name = os.path.abspath(
                os.path.join(dir_name, base_name + extension)
            )
        if os.path.isfile(new_name):
            new_name = self.generate_unique_filename(new_name, extension=extension)
        try:
            os.rename(current_name, new_name)
            return new_name
        except Exception as e:
            print(f"Error renaming file in original location: {e}")
            return current_name

    def find_file_profile(self, pdf_image: io.BytesIO) -> int:
        profiles = self.main_view_model.fetch_all_file_profiles(order_by="count")

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
            cropped_pdf_image = pdf_image.crop(
                (file_id_x1, file_id_y1, file_id_x2, file_id_y2)
            )

            # Using tesseract on cropped image, check if its equal to the unique_text
            text = self.analyze_image(cropped_pdf_image)
            if (self.compare_strings(file_identifier_text, text.replace("\n", " "))):
                file_type = file_profile[0]
                return file_type

        return 0

    def compare_strings(self, string_1: str, string_2: str) -> bool:
        if string_1 == string_2:
            return True
        if self.main_view_model.scrub(string_1) in self.main_view_model.scrub(string_2):
            return True
        else:
            return False

    def find_parameter_data(self, profile_id: int, pdf_image: io.BytesIO) -> dict:
        file_profile_parameters = (
            self.main_view_model.fetch_active_parameters_by_profile_id(
                profile_id=profile_id
            )
        )
        # Iterate through each location of each parameter
        data = {}
        for file_profile_parameter in file_profile_parameters[2:]:
            [
                x_1,
                x_2,
                y_1,
                y_2,
            ] = self.main_view_model.fetch_parameter_rectangle_by_name_and_profile_id(
                profile_id=profile_id, parameter_name=file_profile_parameter
            )
            parameter_regex = self.main_view_model.fetch_parameter_regex_by_parameter_name_and_profile_id(
                profile_id=profile_id, parameter_name=file_profile_parameter
            )
            advanced_option = self.main_view_model.fetch_advanced_option_by_parameter_name_and_profile_id(
                profile_id=profile_id, parameter_name=file_profile_parameter
            )
            for scale in [1.0, 1.01, 1.02, 1.03, 1.04, 1.05]:
                (scaled_x_1, scaled_x_2, scaled_y_1, scaled_y_2) = self.scaled_coordinates(
                    x_1, x_2, y_1, y_2, scale
                )

                # crop image to desired location
                cropped_image = pdf_image.crop(
                    (scaled_x_1, scaled_y_1, scaled_x_2, scaled_y_2)
                )

                result = self.analyze_image(cropped_image)
                
                project_number_found = False
                if "project_number" in file_profile_parameter:
                    result = text_utils.detect_englobe_project_number(result)
                    # check if project number is in database
                    project_data = self.main_view_model.fetch_project_data_by_project_number(
                        project_number=result
                    )
                    if project_data:
                        project_number_found = True
                        
                if advanced_option:
                    
                    parameter_id = self.main_view_model.fetch_parameter_id_by_name_and_profile_id(
                        profile_id=profile_id, parameter_name=file_profile_parameter
                    )
                    secondary_parameter_data = self.main_view_model.fetch_secondary_parameter_by_parameter_id(parameter_id=parameter_id)
                    if secondary_parameter_data:
                        (scaled_x_1, scaled_x_2, scaled_y_1, scaled_y_2) = self.scaled_coordinates(
                            secondary_parameter_data[0],
                            secondary_parameter_data[1],
                            secondary_parameter_data[2],
                            secondary_parameter_data[3],
                            scale
                        )
                        
                        secondary_cropped_image = pdf_image.crop(
                            (scaled_x_1, scaled_y_1, scaled_x_2, scaled_y_2)
                        )
                        secondary_advanced_option = secondary_parameter_data[4]
                        comparison_type = secondary_parameter_data[5]
                        secondary_result = self.analyze_image(secondary_cropped_image)
                    
                    potential_list = result.split("\n")

                    try:
                        primary_list = [line.strip() for line in potential_list]
                        if secondary_parameter_data:
                            secondary_list = [line.strip() for line in secondary_result.split("\n")]
                            processed_data = text_utils.process_list_comparison(primary_list, advanced_option, secondary_list, secondary_advanced_option, comparison_type)
                        else:
                            processed_data = text_utils.process_list_comparison(primary_list, advanced_option)
                    except ValueError:
                        # Some item in the potential list couldn't be converted to float
                        # Try to scale up and see if that fixes issue
                        continue
                else:

                    if parameter_regex:
                        data_point = re.search(rf"{parameter_regex}", result, re.M + re.I)
                        if data_point:
                            data_point = data_point.groups()
                            processed_data = self.main_view_model.scrub(data_point[-1].replace(" ", "-"))
                        else:
                            processed_data = None
                    else:
                        processed_data = self.main_view_model.scrub(str(result).replace(" ", "-"))
                
                if "project_number" in file_profile_parameter:
                    if project_number_found:
                        break
                    else:
                        continue
                else:              
                    break

            data[file_profile_parameter] = str(processed_data)
        return data
    
    def scaled_coordinates(self, x_1, x_2, y_1, y_2, scale):
        scaled_x_1 = int(x_1 / scale)
        scaled_x_2 = int(x_2 * scale)
        scaled_y_1 = int(y_1 / scale)
        scaled_y_2 = int(y_2 * scale)
        return scaled_x_1, scaled_x_2, scaled_y_1, scaled_y_2

    def analyze_image(self, img_path) -> str:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        config_str = "--psm " + str(6)
        return pytesseract.image_to_string(img_path, config=config_str).strip()
