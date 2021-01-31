import regex as re

# months dictionary used to correct mis-detected months (ex. its used to transform detected Jen to Jan)
months = {"Jan": 0, "Feb": 1, "Mar": 2, "Apr": 3, "May": 4, "Jun": 5, "Jul": 6, "Aug": 7, "Sep": 8, "Oct": 9,
          "Nov": 10, "Dec": 11}


def month_value(month):
    return months[month]


def month_closest(found_month):
    # If detected month is not found in the months dictionary, it is obviously a bad detected letter
    # To ease file renaming (not perfect), find month closest in similarity and assume that was the one detected.
    closest_month = found_month
    if found_month not in months:
        similarity_highest = 999
        for month in months:
            similarity = hamming_distance(found_month, month)
            if similarity < similarity_highest:
                closest_month = month
                similarity_highest = similarity
    return closest_month


def hamming_distance(found_value, file_value):
    return sum(c1 != c2 for c1, c2 in zip(found_value, file_value))


def date_formatter(date_array):
    if date_array:
        date_day = []
        date_month = []
        date_year = []
        # Iterate through the dates and store the day value, and the month value.
        # these should be the same length so indexing will be identical between both
        for temp_date in date_array:
            if temp_date is not None:
                if re.search(r"(\d+)[\s-]+", temp_date, re.I) is not None:
                    date_day_search = re.search(r"(\d+)[\s-]+", temp_date, re.I).groups()
                    date_day.append(date_day_search[-1])
                else:
                    date_day.append("NA")
                if re.search(r"\d+[\s-]+(\w+)[\s-]+", temp_date, re.I) is not None:
                    date_month_search = re.search(r"\d+[\s-]+(\w+)[\s-]+", temp_date, re.I).groups()
                    date_month.append(date_month_search[-1])
                else:
                    date_month.append("NA")
                if re.search(r"\d+[\s-]+\w+[\s-]+(\d+)", temp_date, re.I) is not None:
                    date_year_search = re.search(r"\d+[\s-]+\w+[\s-]+(\d+)", temp_date, re.I).groups()
                    date_year.append(date_year_search[-1])
                else:
                    date_year.append("NA")
            else:
                date_day.append("NA")
                date_month.append("NA")
                date_year.append("NA")

        # Iterate through the stored months to find how many are unique
        month_unique = []
        for z, month in enumerate(date_month):
            closest_month = month_closest(month)
            date_month[z] = closest_month
            if closest_month not in month_unique:
                month_unique.append(closest_month)

        for i in range(0, len(date_year)):
            if len(date_year[i]) <= 2:
                date_year[i] = "20" + date_year[i]
            # To reduce misdetected years, if month is Feb to Nov assume year is current year.
            # if months[date_month[i]] != 0 or months[date_month[i]] != 11:
            #     now = datetime.datetime.now()
            #     date_year[i] = str(now.year)

        # Iterate through the stored years to find how many are unique (99% will be 1 year)
        year_unique = []
        for year in date_year:
            if year not in year_unique:
                year_unique.append(year)
        try:
            year_unique.sort(key=int)
        except ValueError:
            pass
        month_unique.sort(key=month_value)
        date_string = ""
        # For each unique year and month find how many day values there are for each
        for i, year in enumerate(year_unique):
            for k, month in enumerate(month_unique):
                date_day_string = ""
                day_unique = []
                # For each month-year combo, find number of unique days
                # This just gets rid of duplicate dates in the filename.
                for j in range(0, len(date_month)):
                    if date_year[j] == year and date_month[j] == month:
                        if date_day[j] not in day_unique:
                            day_unique.append(date_day[j])
                if day_unique:
                    try:
                        day_unique.sort(key=int)
                    except ValueError:
                        pass
                # Using the stored unique days for month-year combo, format into filename
                for j in range(0, len(day_unique)):
                    if j == 0:
                        date_day_string = day_unique[j]
                    else:
                        if int(day_unique[j]) == int(day_unique[j - 1]) + 1:
                            replace_string = "-" + day_unique[j - 1]
                            date_day_string = date_day_string.replace(replace_string, "") + "-" + day_unique[j]
                        else:
                            date_day_string = date_day_string + "," + day_unique[j]
                if k == 0:
                    date_string = date_day_string + "-" + month + "-" + year
                else:
                    date_string = date_string + "&" + date_day_string + "-" + month + "-" + year
        return date_string
    else:
        return "NO_DATES"
