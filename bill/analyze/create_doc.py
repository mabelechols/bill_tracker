import csv
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell as cell_name
import os
import numpy as np

from ..utility import helpers
from ..utility.date import Date
from .transactions import Transactions


def add_category(struct: dict, category: str):
    head = category.split(".")[0]
    tail = ".".join(category.split(".")[1:])

    if head not in struct:
        struct[head] = {"*": []}

    if tail == "":
        return struct[head]

    return add_category(struct[head], tail)


def get_category(struct: dict, category: str):
    head = category.split(".")[0]
    tail = ".".join(category.split(".")[1:])

    if tail == "":
        return struct

    return get_category(struct[head], tail)


def header_section(struct: dict, level: int = 0):
    header = []
    for key in struct.keys():
        if key == "*":
            continue
        header.append([None] * level + [key])
        if len(struct[key].keys()) > 1:
            header.extend(header_section(struct[key], level + 1))
    return header


def padded_header_section(struct: dict) -> list[list[str | None]]:
    header = header_section(struct)

    max_len = 0
    for line in header:
        if len(line) > max_len:
            max_len = len(line)

    for i, line in enumerate(header):
        header[i] = line + [None] * (max_len - len(line))

    return header


def ordered_header(struct: dict):
    header = padded_header_section(struct)
    ordered = {}

    cat: list[str] = []

    for j, line in enumerate(header):
        sub_cat: str | None = None
        i = len(line) - 1

        while sub_cat is None:
            if i < 0:
                break

            sub_cat = line[i]
            i -= 1

        cat = cat[: i + 1]
        cat.append(sub_cat)

        ordered[".".join(cat)] = j

    return ordered


def week_data(transactions: Transactions, categories: dict):
    raw_data = transactions.by_week()
    n_weeks = len(raw_data.keys())

    data_header: list = [""] * n_weeks
    data = np.zeros((n_weeks, len(categories)), float)

    for i, week in enumerate(raw_data):
        data_header[i] = str(week)

        cat_ind = 0

        for transaction in raw_data[week]:
            amount, category = (
                transaction["amount"],
                transaction["category"],
            )

            sub_cats = category.split(".")
            while len(sub_cats) > 0:
                cat_ind = categories[".".join(sub_cats)]
                data[i, cat_ind] += amount
                sub_cats = sub_cats[:-1]

    return data_header, data


def month_data(transactions: Transactions, categories: dict):
    raw_data = transactions.by_month()
    n_months = len(raw_data.keys())

    data_header: list = [""] * n_months
    data = np.zeros((n_months, len(categories)), float)

    for i, month in enumerate(raw_data):
        data_header[i] = month

        cat_ind = 0

        for transaction in raw_data[month]:
            amount, category = (
                transaction["amount"],
                transaction["category"],
            )

            sub_cats = category.split(".")
            while len(sub_cats) > 0:
                cat_ind = categories[".".join(sub_cats)]
                data[i, cat_ind] += amount
                sub_cats = sub_cats[:-1]

    return data_header, data


def category_sheet(
    workbook: xlsxwriter.Workbook,
    category: str,
    category_transactions: dict[str, Transactions],
):
    date_format = workbook.add_format({"num_format": "mm/dd/yyyy;@"})
    sheet = workbook.add_worksheet(category)

    transactions = category_transactions[category]

    header = ["Date", "Amount", "Vendor"]
    header_keys = ["date", "amount", "vendor"]

    for i, data in enumerate(header):
        sheet.write(0, i, data)

    for i, transaction in enumerate(transactions):
        for j, key in enumerate(header_keys):
            if isinstance(transaction[key], Date):
                sheet.write(i + 1, j, transaction[key].since_epoch(), date_format)
            else:
                sheet.write(i + 1, j, transaction[key])

    sheet.autofit()


def create_xlsx(csv_file: str, xlsx_file: str):
    categories = {}
    transactions = Transactions()

    with open(csv_file, "r") as f_stream:
        reader = csv.reader(f_stream)

        for line in reader:
            date, amount, vendor, category = line

            transactions.add_transaction(date, amount, vendor, category)

            struct = add_category(categories, category)
            struct["*"].append((date, amount))

    transactions.sort()

    category_header = padded_header_section(categories)
    category_order = ordered_header(categories)

    week_header, data_by_week = week_data(transactions, category_order)
    month_header, data_by_month = month_data(transactions, category_order)
    data_by_category = transactions.by_category()

    try:
        os.remove(xlsx_file)
    except:
        pass

    workbook = xlsxwriter.Workbook(xlsx_file)
    money_format = workbook.add_format(
        {"num_format": '_($* #,##0.00_);_($* (#,##0.00);_($* " - "??_);_(@_)'}
    )
    header_format = workbook.add_format(
        {"bold": True, "font_color": "#FFFFFF", "bg_color": "#303030"}
    )
    sheet_by_week = workbook.add_worksheet("Category Spending By Week")
    sheet_by_month = workbook.add_worksheet("Category Spending By Month")

    row_off, col_off = 1, len(category_header[0])

    # Category Header
    for ri, row in enumerate(category_header):
        ci = 0
        while row[ci] is None:
            ci += 1

        if len(row) - ci > 2:
            sheet_by_week.merge_range(
                ri + row_off, ci, ri + row_off, len(row) - 1, row[ci], header_format
            )
            sheet_by_month.merge_range(
                ri + row_off, ci, ri + row_off, len(row) - 1, row[ci], header_format
            )

        else:
            sheet_by_week.write(ri + row_off, ci, row[ci], header_format)
            sheet_by_month.write(ri + row_off, ci, row[ci], header_format)

    # Data Writing
    for ci, data in enumerate(week_header):
        sheet_by_week.write(0, ci + col_off, data)
    for ci, data in enumerate(month_header):
        sheet_by_month.write(0, ci + col_off, data)

    for i in range(data_by_week.shape[0]):
        for j in range(data_by_week.shape[1]):
            sheet_by_week.write(
                row_off + j, col_off + i, data_by_week[i, j], money_format
            )

    for i in range(data_by_month.shape[0]):
        for j in range(data_by_month.shape[1]):
            sheet_by_month.write(
                row_off + j, col_off + i, data_by_month[i, j], money_format
            )

    for category in category_order:
        category_sheet(workbook, category, data_by_category)

    # Write Formulas

    row_off, col_off = 1, len(category_header[0]) + data_by_month.shape[0] + 2

    formula_header = [
        "Average (From {month})",
        "Confidence Interval",
    ]
    formula_equations = [
        "=AVERAGE({start_cell}:{end_cell})",
        "=CONFIDENCE(0.05, STDEV({start_cell}:{end_cell}), COUNT({start_cell}:{end_cell}))",
    ]
    months = ["09/2022", "09/2023", "09/2024", "02/2025"]
    n_months, n_cats = data_by_month.shape

    for month in months:
        for k in range(len(formula_header)):
            sheet_by_month.write(
                0, col_off + k, formula_header[k].format(month=month), header_format
            )

        # Find data start
        start_col = 0

        for c, m in enumerate(month_header):
            if m == month:
                start_col = c
                break
        # End find data start

        for j in range(n_cats):

            for k, formula in enumerate(formula_equations):
                f_cell = (row_off + j, col_off + k)

                start_cell = cell_name(row_off + j, start_col + len(category_header[0]))
                end_cell = cell_name(
                    row_off + j, n_months + len(category_header[0]) - 1
                )

                sheet_by_month.write_formula(
                    *f_cell,
                    formula.format(start_cell=start_cell, end_cell=end_cell),
                    money_format
                )

        col_off += len(formula_header)

    sheet_by_month.freeze_panes(1, len(category_header[0]))
    sheet_by_week.freeze_panes(1, len(category_header[0]))
    sheet_by_month.autofit()
    workbook.close()
