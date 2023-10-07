import datetime


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
