import re
from typing import TypedDict
import os

# from .date import Date


def to_float(amount: str):
    """
    Returns a float given a price string

        Parameters:
            amount (str): The amount to convert

        Returns:
            float: amount as numeric
    """

    return float("".join(amount.split(",")))


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
        for i, m in enumerate(Date.MONTHS):
            if m[:3] == mo_str:
                return i + 1

        raise ValueError(f"{mo_str} is not a valid month")

    NAME_CONVENTIONS = {
        "PNC": "Statement_([a-zA-Z]+)_\\d+_(\\d+).pdf",
        "Chase": "(\\d{4})(\\d{2})\\d{2}-statements-\\d{4}-.pdf",
        "FNB": "Statement_(\\d{4})-(\\d{2})-\\d{2}.pdf",
        "Discover": "Discover-Statement-(\\d{4})(\\d{2})\\d{2}.csv",
    }

    class Info(TypedDict):
        name: str | None
        bank: str | None
        month: int | None
        year: int | None

    info: Info = {
        "name": None,
        "bank": None,
        "month": None,
        "year": None,
    }

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
    if groups is None:
        raise ValueError(f"Unrecognized file name {f_name}")

    info["bank"] = bank
    info["name"] = f_name

    if bank == "PNC":
        info["month"], info["year"] = month_convert(groups.group(1)), int(
            groups.group(2)
        )
    elif bank in ["Chase", "FNB", "Discover"]:
        info["year"], info["month"] = int(groups.group(1)), int(groups.group(2))

    return info


def parse_num_selection(choice: str):
    raw_ranges = choice.split(",")
    stripped_ranges = []

    for raw in raw_ranges:
        stripped_ranges.append(raw.strip())

    output: list = []
    for rng in stripped_ranges:
        if rng == "":
            continue
        try:
            output.append(int(rng))
        except:
            try:
                s = rng.split("-")
                si = int(s[0])
                ei = int(s[1])
                output.extend(range(si, ei + 1))
            except:
                raise ValueError(f"Unrecognized value {rng}")

    return output


def percent_bar(p, w=10):
    FILL = "▓"
    UNFILL = "▒"

    bar = ""
    f = 0

    for _ in range(w):
        if p > f:
            bar += FILL
        else:
            bar += UNFILL

        f += 1 / w

    return f"{bar}"
