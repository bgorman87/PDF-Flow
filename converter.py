import json
import os
import csv


def parse_json_file(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in file {file_path}: {e}")
        return None


def json_to_csv(parsed_data, csv_file_path):
    # Define the CSV headers
    headers = [
        "project_number",
        "directory",
        "description",
        "email_to",
        "email_cc",
        "email_bcc",
        "email_subject",
        "email_profile_name",
    ]

    # Create and open the CSV file for writing
    with open(csv_file_path, "w", newline="") as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=headers)

        # Write the CSV header row
        csv_writer.writeheader()

        # Iterate through each JSON entry and write it to the CSV
        for entry in parsed_data:
            # Create a dictionary for each CSV row
            csv_row = {
                "project_number": entry.get("project_number", ""),
                "directory": entry.get("project_directory", ""),
                "description": entry.get("project_description", ""),
                "email_to": entry.get("project_email_to", ""),
                "email_cc": entry.get("project_email_cc", ""),
                "email_bcc": "",  # This field is not present in the JSON data
                "email_subject": entry.get("project_email_subject", ""),
                "email_profile_name": "",  # This field is not present in the JSON data
            }

            # Write the CSV row
            csv_writer.writerow(csv_row)


if __name__ == "__main__":
    file_path = os.path.abspath(os.path.join(os.getcwd(), "sorter_data.json"))

    output_file_path = os.path.abspath(os.path.join(os.getcwd(), "output.csv"))
    print(output_file_path)
    parsed_data = parse_json_file(file_path)

    if parsed_data is not None:
        print("Converting to CSV")
        json_to_csv(
            parsed_data,
            output_file_path
        )
    else:
        print("No JSON Data")
