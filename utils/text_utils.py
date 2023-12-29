import datetime
import re
import os
from bs4 import BeautifulSoup
from lxml import html
import base64


def valid_date(date_string):
    try:
        datetime.datetime.strptime(date_string, "%d %b %Y")
        return True
    except (ValueError, TypeError):
        return False


def determine_precision(numbers):
    """Determines the maximum number of decimal places in a list of numbers. Useful when trying to display a float value to the user. Float value can remain consistent across all values in the list.

    Args:
        numbers (list[float]): List of floats

    Returns:
        int: Maximum number of decimal places
    """

    max_decimal_places = 0

    for num in numbers:
        # Split the number into its integer and decimal parts
        parts = str(num).split('.')

        # If the number has a decimal part, compare its length to the current max
        if len(parts) > 1:
            max_decimal_places = max(max_decimal_places, len(parts[1]))

    return max_decimal_places


def process_and_determine_type(values):
    """Processes a list of values to either a list of ints or a list of floats

    Args:
        values (list[any]): List of OCR scanned values

    Returns:
        tuple: (Processed list, type of list)
    """
    has_float = False
    processed_values = []

    for value in values:
        try:
            float_value = float(value)
            if float_value != int(float_value):
                has_float = True
            processed_values.append(float_value)
        except ValueError:
            # Ignore values that can't be converted to numbers
            pass

    if has_float:
        return processed_values, float
    else:
        return [int(val) for val in processed_values], int
    
def process_list_comparison(primary_list, primary_option, secondary_list=None, secondary_option=None, comparison_type=None):

    process_primary_list, primary_list_type = process_and_determine_type(primary_list)

    if primary_option != "index":
        primary_result = process_list(process_primary_list, primary_list_type, primary_option)
    
    if secondary_list is not None:
        process_secondary_list, secondary_list_type = process_and_determine_type(secondary_list)
        if secondary_option != "index":
            secondary_result = process_list(process_secondary_list, secondary_list_type, secondary_option)
    
    if primary_option == "index":
        try:
            result = primary_list[secondary_result]
            return result
        except IndexError:
            print("Index Error")
            return "NA"

    elif secondary_option == "index":
        try:
            result = secondary_list[primary_result]
            return result
        except IndexError:
            print("Index Error")
            return "NA"

    # Perform the comparison based on the selected operator
    if comparison_type == "equal":
        result = primary_result == secondary_result
    elif comparison_type == "min":
        result = min(primary_result, secondary_result)
    elif comparison_type == "max":
        result = max(primary_result, secondary_result)
    else:
        result = ""

    return result

def process_list(list_data, list_type, advanced_option):

    precision = None
    if list_type == float:
        precision = determine_precision(list_data)

    result = None
    
    if advanced_option == "max":
        result = max(list_data)
    elif advanced_option == "min":
        result = min(list_data)
    elif advanced_option == "mean":
        result = sum(list_data) / len(list_data)
        if precision:
            result = round(result, precision)
    elif advanced_option == "median":
        sorted_list = sorted(list_data)
        mid_idx = len(sorted_list) // 2
        if len(sorted_list) % 2 == 0:  # Even number of items
            result = (sorted_list[mid_idx - 1] + sorted_list[mid_idx]) / 2
            if precision:
                result = round(result, precision)
        else:  # Odd number of items
            result = sorted_list[mid_idx]
    elif advanced_option == "min_index":
        result = list_data.index(min(list_data))
    elif advanced_option == "max_index":
        result = list_data.index(max(list_data))
    elif advanced_option == "length":
        result = len(list_data)
    elif advanced_option == "sum":
        result = sum(list_data)
    elif advanced_option == "first_value":
        result = list_data[0]
    elif advanced_option == "last_value":
        result = list_data[-1]

    return result


def detect_englobe_project_number(text):
    # Regex expressions for job numbers
    # B numbers: ^(B[\.-\s]\d+[\.-\s]+\d{1})
    # P numbers: ^(P[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d{3})
    # 1900: ^(1\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d{3})
    # 0200: ^([0-2]\d+[\.-\s]+\d+[\.-\s]\d+[\.-\s]+\d{4})
    # r = StringIO(text)
    # text = text.replace(" ", "")
    # test = re.search(r"(B[\.-\s]\d+[\.-\s]+\d{1})", text, re.M)
    expressions = [
        r"(B[.\-\s]\d+[.\-\s]+\d{1})",
        r"(P[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d{3})",
        r"(P[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d+)",
        r"(1\d+[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d)",
        r"(1\d+[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d+[.\-\s]+\d+)",
        r"([0-2]\d+[.\-\s]+\d+[.\-\s]\d+[.\-\s]+\d+)",
        r"([0-2]\d+[.\-\s]+\d+[.\-\s]\d+)"
    ]

    project_number = "NA"

    for i in range(6):
        if re.search(expressions[i], text, re.M) is not None:
            try:
                project_number = re.search(expressions[i], text, re.M).groups()
            except AttributeError as e:
                print(e)
                project_number = str(re.search(expressions[i], text, re.M))
            project_number = project_number[-1]
            project_number = project_number.replace(" ", "")
            break

    return project_number

def format_external_html(folder_path: str, html: str) -> str:
        soup = BeautifulSoup(html, 'lxml')
        
        def update_path(tag, attribute):
            if tag.has_attr(attribute):
                rel_path = tag[attribute]
                # Check if the path is relative and not an external link
                if rel_path and not rel_path.startswith(('http:', 'https:', 'mailto:', '#')):
                    abs_path = os.path.join(folder_path, *rel_path.split("/"))
                    tag[attribute] = abs_path

        # Update src and href attributes
                    
        def custom_selector(tag):
            # Return tags with either a 'src' or 'href' attribute
            return (tag.name is not None) and (tag.has_attr('src') or tag.has_attr('href'))

        for tag in soup.find_all(custom_selector):
            update_path(tag, 'src')
            update_path(tag, 'href')

        return(str(soup))

def embed_images_as_base64(html_content: str) -> str:
    """Embeds images in html as base64

    Args:
        html_content (str): Body content for an HTML email

    Returns:
        str: html with images embedded as base64
    """
    root = html.fromstring(html_content)

    for img_tag in root.xpath("//img"):
        src = img_tag.get("src")
        if not src.startswith("data:image/"):
            # Read the image and encode it in base64
            with open(src, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

            # Get the image's format from its extension (e.g., .jpg -> jpeg)
            image_format = (
                os.path.splitext(src)[1].replace(".", "").replace("jpg", "jpeg")
            )

            # Replace the src with the base64 encoded version
            img_tag.set("src", f"data:image/{image_format};base64,{encoded_string}")

    return html.tostring(root, encoding="unicode")
