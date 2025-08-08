import re
import os


def to_float(amount: str):
    """
    Returns a float given a price string

        Parameters:
            amount (str): The amount to convert

        Returns:
            float: amount as numeric
    """

    return float("".join(amount.split(",")))


def day_rank(date):
    """
    Returns an integer representing the number of days since 01/01/0000

        Parameters:
            date (str): The date string in the form mm/dd/yyyy

        Returns:
            int: The number of days since 01/01/0000
    """

    def is_leap(yr):
        if yr % 4 == 0:
            if yr % 100 == 0:
                if yr % 400 == 0:
                    return True
                return False
            return True
        return False

    def days_before(mo, yr):
        days = 0
        for i in range(1, mo):
            if i in [1, 3, 5, 7, 8, 10, 12]:
                days += 31
            elif i != 2:
                days += 30
            else:
                days += 28 + is_leap(yr)

        for i in range(yr):
            if is_leap(i):
                days += 366
            else:
                days += 365

        return days

    out = 0
    mo, da, yr = date.split("/")

    out += days_before(int(mo), int(yr))
    out += int(da)

    return out


def file_extension(file_path):
    """
    Returns the extension of a file if there is one

        Parameters:
            file_path (str): The file to return the extension of

        Returns:
            str: The extension
    """

    _, f_name = os.path.split(file_path)

    f_name_split = f_name.split(".")
    if len(f_name_split) > 1:
        return f_name_split[-1]
    return ""


def document_info(file_path):
    """
    Returns information on a bank statement

        Parameters:
            file_path (str): The file to query info of

        Returns:
            dict: Information on the bank statement
    """

    def month_convert(mo_str):
        MONTHS = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        for i, m in enumerate(MONTHS):
            if m == mo_str:
                return i + 1

        raise ValueError(f"{mo_str} is not a valid month")

    NAME_CONVENTIONS = {
        "PNC": "Statement_([a-zA-Z]+)_\\d+_(\\d+).pdf",
        "Chase": "(\\d{4})(\\d{2})\\d{2}-statements-\\d{4}-.pdf",
        "FNB": "Statement_(\\d{4})-(\\d{2})-\\d{2}.pdf",
        "Discover": "Discover-Statement-(\\d{4})(\\d{2})\\d{2}.csv",
    }

    info = {"name": None, "bank": None, "month": None, "year": None}

    _, f_name = os.path.split(file_path)

    banks = set()
    for bank in NAME_CONVENTIONS:
        reg = NAME_CONVENTIONS[bank]

        groups = re.search(reg, f_name)

        if groups != None:
            banks.add(bank)

    if len(banks) > 1:
        raise ValueError(f"{file_path} could be a document for multiple banks")
    elif len(banks) == 0:
        raise ValueError(f"{file_path} does not match any known bank")

    bank = banks.pop()
    groups = re.search(NAME_CONVENTIONS[bank], f_name)

    info["bank"] = bank
    info["name"] = f_name

    if bank == "PNC":
        info["month"], info["year"] = month_convert(groups.group(1)), int(
            groups.group(2)
        )
    elif bank in ["Chase", "FNB", "Discover"]:
        info["year"], info["month"] = int(groups.group(1)), int(groups.group(2))

    return info
