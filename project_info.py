import json


# Exception rule to break out of multi-level for loops when trying to identify project numbers
class ProjectFound(Exception):
    pass


mode = ""
data_store = []
json_projects = []


def json_setup(state):
    global data_store
    global json_projects
    global mode

    mode = state
    # if self.testBox.currentText() != "Test":
    #     json_filename = r"C:\Users\gormbr\OneDrive - EnGlobe Corp\Desktop\sorter_data.json"
    # else:
    #     json_filename = r"C:\Users\gormbr\OneDrive - EnGlobe Corp\Desktop\sorter_test.json"
    # json_filename = r"C:\Users\gormbr\OneDrive - EnGlobe Corp\Desktop\sorter_data.json"
    json_filename = r"C:\Users\bgorm\Downloads\sorter_data.json"
    # Read JSON data into the data_store variable
    if json_filename:
        with open(json_filename, 'r') as f:
            data_store = json.load(f)
    for item in data_store:
        json_projects.append(item['project_number'])


# project info function
# By inputting the project number and detected variables, the function looks through the json data file, and returns
# the desired project info such as where to save files to, who to send e-mail too and what the project description is
def project_info(project_number, project_number_short, f, sheet_type, analyzed):
    # file path isn't really used for anything here anymore as far as i can tell
    file_path = f.replace(f.split("/").pop(), "")
    if file_path == "":
        file_path = f.replace(f.split("\\").pop(), "")
    # set default values in case project number is not in the JSON data file
    project_description = "SomeProjectDescription"
    email_recipient_to = ""
    email_recipient_cc = ""
    email_recipient_subject = ""
    default_email_to = "brandon.gorman@englobecorp.com; bgorman@live.ca"
    default_email_cc = "bgorman@live.com"
    # default_directory = r"C:\\Users\\gormbr\\OneDrive - EnGlobe Corp\\Desktop\\reports"
    default_directory = r"C:\Users\bgorm\Downloads\Reports"

    try:
        # There are two ways to compare project numbers here. The first attempt tries to exactly match the entire
        # project number. This will deliver the absolute correct returns for project description and save location,
        # but because it has to detect more characters, there a higher chance it won't work properly, due to a 4 getting
        # recognized as a 1, then the project number won't be in the JSON data file. To increase the odds of proper
        # detection, this first option compares the short project numbers, and if they match, then looks at the last
        # integer of the long project number, if those match as well, then the long project number is assumed to be
        # correct.
        for temp_count in [1, 2, 3]:
            if temp_count == 1:
                for project_data in data_store:
                    if project_number.replace(".", "") == project_data["project_number"].replace(".", "") or \
                            project_number.replace("-", "") == project_data["project_number"].replace("-", ""):
                        # If sheet_type == 5 then its a compaction sheet so use the compaction directory. Or if the
                        # sheet_type == 7 then use the asphalt directory
                        if (sheet_type == "5" and project_data["contract_number"] == "NOTNSTIR-Gravels") or \
                                (sheet_type == "7" and project_data["contract_number"] == "NOTNSTIR-Asphalt"):
                            project_description = project_data["project_description"]
                            if mode != "Test":
                                file_path = project_data["project_directory"]
                                email_recipient_to = project_data["project_email_to"]
                                email_recipient_cc = project_data["project_email_cc"]
                            else:
                                file_path = default_directory
                                email_recipient_to = default_email_to
                                email_recipient_cc = default_email_cc
                            email_recipient_subject = project_data["project_email_subject"]
                            project_number = project_data["project_number"]
                            project_number_short = project_data["project_number_short"]
                            raise ProjectFound
                        # If the sheet_type is not a single compaction or asphalt sheet then use the
                        elif sheet_type != "5" and sheet_type != "7":
                            project_description = project_data["project_description"]
                            if mode != "Test":
                                file_path = project_data["project_directory"]
                                email_recipient_to = project_data["project_email_to"]
                                email_recipient_cc = project_data["project_email_cc"]
                            else:
                                file_path = default_directory
                                email_recipient_to = default_email_to
                                email_recipient_cc = default_email_cc
                            email_recipient_subject = project_data["project_email_subject"]
                            project_number = project_data["project_number"]
                            project_number_short = project_data["project_number_short"]
                            raise ProjectFound
            if temp_count == 2:
                for project_data in data_store:
                    if ((project_number_short.replace(".", "") in project_data["project_number"].replace(".", "") or
                         project_number_short.replace("-", "") in project_data["project_number"].replace("-", "")) and
                            project_number[-1] == project_data["project_number"][-1]):
                        # If sheet_type == 5 then its a compaction sheet so use the compaction directory. Or if the
                        # sheet_type == 7 then use the asphalt directory
                        if (sheet_type == "5" and project_data["contract_number"] == "NOTNSTIR-Gravels") or \
                                (sheet_type == "7" and project_data["contract_number"] == "NOTNSTIR-Asphalt"):
                            project_description = project_data["project_description"]
                            if mode != "Test":
                                file_path = project_data["project_directory"]
                                email_recipient_to = project_data["project_email_to"]
                                email_recipient_cc = project_data["project_email_cc"]
                            else:
                                file_path = default_directory
                                email_recipient_to = default_email_to
                                email_recipient_cc = default_email_cc
                            email_recipient_subject = project_data["project_email_subject"]
                            project_number = project_data["project_number"]
                            project_number_short = project_data["project_number_short"]
                            raise ProjectFound
                        # If the sheet_type is not a single compaction or asphalt sheet then use the
                        elif sheet_type != "5" and sheet_type != "7":
                            project_description = project_data["project_description"]
                            if mode != "Test":
                                file_path = project_data["project_directory"]
                                email_recipient_to = project_data["project_email_to"]
                                email_recipient_cc = project_data["project_email_cc"]
                            else:
                                file_path = default_directory
                                email_recipient_to = default_email_to
                                email_recipient_cc = default_email_cc
                            email_recipient_subject = project_data["project_email_subject"]
                            project_number = project_data["project_number"]
                            project_number_short = project_data["project_number_short"]
                            raise ProjectFound
            if temp_count == 3:
                for project_data in data_store:
                    if (project_number_short.replace(".", "") in project_data["project_number"].replace(".", "") or
                            project_number_short.replace("-", "") in project_data["project_number"].replace("-", "")):
                        if (sheet_type == "5" and project_data["contract_number"] == "NOTNSTIR-Gravels") or \
                                (sheet_type == "7" and project_data["contract_number"] == "NOTNSTIR-Asphalt"):
                            project_description = project_data["project_description"]
                            if mode != "Test":
                                file_path = project_data["project_directory"]
                                email_recipient_to = project_data["project_email_to"]
                                email_recipient_cc = project_data["project_email_cc"]
                            else:
                                file_path = default_directory
                                email_recipient_to = default_email_to
                                email_recipient_cc = default_email_cc
                            email_recipient_subject = project_data["project_email_subject"]
                            project_number = project_data["project_number"]
                            project_number_short = project_data["project_number_short"]
                            raise ProjectFound
                        elif sheet_type != "5" and sheet_type != "7":
                            project_description = project_data["project_description"]
                            if mode != "Test":
                                file_path = project_data["project_directory"]
                                email_recipient_to = project_data["project_email_to"]
                                email_recipient_cc = project_data["project_email_cc"]
                            else:
                                file_path = default_directory
                                email_recipient_to = default_email_to
                                email_recipient_cc = default_email_cc
                            email_recipient_subject = project_data["project_email_subject"]
                            project_number = project_data["project_number"]
                            project_number_short = project_data["project_number_short"]
                            raise ProjectFound
    except ProjectFound:
        pass

    if analyzed:
        return project_number, project_number_short, email_recipient_to, email_recipient_cc, \
               email_recipient_subject
    else:
        return project_number, project_number_short, project_description, file_path
