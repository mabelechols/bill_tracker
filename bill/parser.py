from pypdf import PdfReader
import re
from . import helpers
import csv


def parse(statement_path):
    """
    Returns transactions from a file

        Parameters:
            file_path (str): The file to extract transactions from

        Returns:
            list: Transactions from the file
    """

    info = helpers.document_info(statement_path)
    bank, year, month = info["bank"], info["year"], info["month"]

    transactions = []
    if bank == "PNC":
        transactions = pnc_parse(statement_path)
    elif bank == "Chase":
        transactions = chase_parse(statement_path)
    elif bank == "FNB":
        transactions = fnb_parse(statement_path)
    elif bank == "Discover":
        transactions = discover_parse(statement_path)

    for i, trans in enumerate(transactions):
        local_year = year
        if month == 1:
            local_month = int(trans["date"].split("/")[0])
            if local_month == 12:
                local_year = year - 1

        transactions[i]["date"] = f"{trans["date"]}/{local_year}"

    return transactions


def chase_parse(statement_path):
    reader = PdfReader(statement_path)

    transactions = []

    def visitor(text, cm, tm, font_dict, font_size):
        groups = re.search("(\\d{2}[\\/]\\d{2})\\s+(.+)\\s+([+-]?\\d+\\.\\d{2})", text)

        if groups is None:
            return

        transactions.append(
            {
                "date": groups.group(1),
                "vendor": groups.group(2),
                "amount": float(groups.group(3)),
            }
        )

    for page in reader.pages:
        page.extract_text(visitor_text=visitor)

    return transactions


def pnc_parse(statement_path):
    reader = PdfReader(statement_path)

    transactions = []

    curr_transaction = {
        "date": None,
        "vendor": None,
        "amount": None,
    }
    blank_count = [0]

    def visitor(text, cm, tm, font_dict, font_size):
        # Ignore header and footer
        HEADER_PHRASES = [
            "Member FDIC",
            "Equal Housing Lender",
            "Virtual Wallet Spend Statement",
            "Page",
        ]

        for phrase in HEADER_PHRASES:
            if phrase in text:
                return

        # Text Parsing
        date = re.search("^\\d{2}\\/\\d{2}$", text)
        amount = re.search("^[+-]?[\\d,]+\\.\\d{2}$", text)

        if text.strip() == "":
            blank_count[0] += 1

            if blank_count[0] > 2:
                for key in curr_transaction:
                    curr_transaction[key] = None

            return
        else:
            blank_count[0] = 0

        if date is not None:
            for key in curr_transaction:
                curr_transaction[key] = None

            curr_transaction["date"] = date.string
        elif amount is not None:
            if curr_transaction["date"] is not None:
                curr_transaction["amount"] = helpers.to_float(amount.string)
            else:
                for key in curr_transaction:
                    curr_transaction[key] = None
        else:
            if (
                curr_transaction["date"] is not None
                and curr_transaction["amount"] is not None
            ):
                if curr_transaction["vendor"] is None:
                    curr_transaction["vendor"] = ""

                curr_transaction["vendor"] += text

                if text[-1] != "\n":
                    curr_transaction["vendor"] = curr_transaction["vendor"].replace(
                        "\n", " "
                    )
                    transactions.append(curr_transaction.copy())
                    for key in curr_transaction:
                        curr_transaction[key] = None

            else:
                for key in curr_transaction:
                    curr_transaction[key] = None

    for page in reader.pages:
        page.extract_text(visitor_text=visitor)

    return transactions


def fnb_parse(statement_path):
    reader = PdfReader(statement_path)

    below_header = [False]
    transactions = []
    curr_transaction = {"date": None, "vendor": None, "amount": None}
    prev_balance = [None]

    def visitor(text, cm, tm, font_dict, font_size):
        header = re.search(
            "Post\\s+Date\\s+Description\\s+Debits\\s+Credits\\s+Balance", text
        )

        if header is not None:
            below_header[0] = True

        if text.strip() == "":
            below_header[0] = False

        if below_header[0]:
            date = re.search("(\\d{2}\\/\\d{2})\\/\\d{4}\\s+([^\\$\\n]+)", text)
            price = re.search("\\$([\\d,]+\\.\\d{2})\\s+\\$([\\d,]+\\.\\d{2})", text)

            if date is not None:
                for key in curr_transaction:
                    curr_transaction[key] = None
                curr_transaction["date"] = date.group(1)
                curr_transaction["vendor"] = date.group(2)
            if price is not None:
                amount = helpers.to_float(price.group(1))
                balance = helpers.to_float(price.group(2))

                neg = False
                if prev_balance[0] is not None:
                    neg = balance > prev_balance[0]
                prev_balance[0] = balance

                curr_transaction["amount"] = (-1 if neg else 1) * amount
                curr_transaction["vendor"] = curr_transaction["vendor"].replace(
                    "\n", " "
                )
                transactions.append(curr_transaction.copy())
            if price is None and date is None:
                curr_transaction["vendor"] = curr_transaction["vendor"] + text

    for page in reader.pages:
        page.extract_text(visitor_text=visitor)

    return transactions


def discover_parse(statement_path):
    transactions = []
    with open(statement_path, "r") as f_stream:
        reader = csv.reader(f_stream)
        for i, line in enumerate(reader):
            if i != 0:
                transactions.append(
                    {"date": line[0][:-5], "amount": line[3], "vendor": line[2]}
                )

    return transactions


def _parse(reader: PdfReader):
    """
    Template parser

        Parameters:
            reader (PdfReader): pypdf.PdfReader for statement
        Returns:
            list: transactions found in reader
    """

    def visitor(text, cm, tm, font_dict, font_size):
        print(repr(text))

    for page in reader.pages:
        page.extract_text(visitor_text=visitor)

    return []
