import regex as re


def detect_project_number(text):
    # Regex expressions for job numbers
    # B numbers: ^(B[\.-\s]\d+[\.-\s]+\d{1})
    # P numbers: ^(P[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d{3})
    # 1900: ^(1\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d{3})
    # 0200: ^([0-2]\d+[\.-\s]+\d+[\.-\s]\d+[\.-\s]+\d{4})
    # r = StringIO(text)
    # text = text.replace(" ", "")
    # test = re.search(r"(B[\.-\s]\d+[\.-\s]+\d{1})", text, re.M)
    expressions = [
        r"(B[\.-\s]\d+[\.-\s]+\d{1})",
        r"(P[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d{3})",
        r"(P[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+)",
        r"(1\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d)",
        r"(1\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+)",
        r"([0-2]\d+[\.-\s]+\d+[\.-\s]\d+[\.-\s]+\d+)",
        r"([0-2]\d+[\.-\s]+\d+[\.-\s]\d+)"
    ]
    expressions_short = [
        "",
        r"(P[\.-\s]+\d+[\.-\s]+\d+[\.-\s]+\d+)",
        "",
        r"(1\d+[\.-\s]+\d+)",
        r"(1\d+[\.-\s]+\d+)",
        r"([0-2]\d+[\.-\s]+\d+)",
        r"([0-2]\d+[\.-\s]+\d+)"
    ]
    project_number = "NA"
    project_number_short = "NA"
    for i in range(6):
        if i == 0:
            if re.search(expressions[i], text, re.M) is not None:
                try:
                    project_number = re.search(expressions[i], text, re.M).groups()
                except AttributeError as e:
                    print(e)
                    project_number = str(re.search(expressions[i], text, re.M))
                project_number = project_number[-1]
                project_number = project_number.replace(" ", "")
                project_number_short = project_number
                break
        elif i in [1, 3, 4, 5, 6]:
            if re.search(expressions[i], text, re.M) is not None:
                project_number = re.search(expressions[i], text, re.M).groups()
                project_number = project_number[-1]
                project_number = project_number.replace(" ", "")
                if re.search(expressions_short[i], project_number, re.M) is not None:
                    project_number_short = re.search(expressions_short[i], project_number, re.M).groups()
                    project_number_short = project_number_short[-1]
                else:
                    project_number_short = project_number
                break
        elif i == 2:
            if re.search(expressions[i], text, re.M) is not None:
                project_number = re.search(expressions[i], text, re.M).groups()
                project_number = project_number[-1]
                project_number = project_number.replace(" ", "")
                project_number_short = project_number
                break
    project_number_short = project_number_short.replace(" ", "")
    if project_number_short[0] == "0":
        project_number_short = project_number_short[1:]
    if project_number[0] == "0":
        project_number = project_number[1:]
    return project_number, project_number_short
