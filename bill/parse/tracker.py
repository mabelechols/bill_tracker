import os
from . import parser
import csv
from ..utility import helpers
import shutil
from . import categorize
from ..utility.date import Date


def track(in_dir, out_dir, cat_file):
    print(f"Reading statements from {in_dir}")

    # Read categories if the file exists
    categories = []
    if os.path.isfile(cat_file):
        if helpers.file_extension(cat_file) != "csv":
            raise TypeError("Categories file must be a .csv!")

        with open(cat_file, "r") as f_stream:
            reader = csv.reader(f_stream)
            for i, line in enumerate(reader):
                if len(line) == 0:
                    continue
                elif len(line) == 1:
                    raise ValueError(f"Malformed category in {cat_file} on line {i}")

                reg_ex, category = line[0], ".".join(line[1:])
                categories.append((reg_ex, *category.split(".")))

    # Clear/create output directory
    if os.path.exists(out_dir):
        if os.path.isdir(out_dir):
            choice = input(f"Preparing to delete {out_dir} Deletion ok? (Y/n) ")
            if choice != "Y":
                print(f"Cannot output to {out_dir}. Exiting")
                return

            shutil.rmtree(out_dir)
        else:
            raise TypeError("Output directory must not be a file.")

    os.mkdir(out_dir)

    # Read Transactions
    all_trans = []
    all_trans_dict = []

    if os.path.exists(in_dir):
        if not os.path.isdir(in_dir):
            raise TypeError("Input directory must not be a file.")

        for statement in os.listdir(in_dir):
            trans = parser.parse(os.path.join(in_dir, statement))

            for t in trans:
                vendor, date, amount = t["vendor"], Date(t["date"]), t["amount"]
                all_trans_dict.append(
                    {"vendor": vendor, "date": date, "amount": amount}
                )
                all_trans.append((date, amount, vendor))

        all_trans.sort(key=lambda t: t[0].to_int())
        all_trans_dict.sort(key=lambda t: t[0].to_int())

    # categorize
    print("Transactions read.")
    choice = input("Save categorizations to cat_file? (Y/n): ")
    write = choice == "Y"
    cats = categorize.categorize(all_trans_dict, cat_file, write)

    for i in range(len(all_trans)):
        trans = (*all_trans[i], cats[i])
        all_trans[i] = trans

    if len(all_trans) > 0:
        print(f"{len(all_trans)} transactions found. Writing to {out_dir}")
    else:
        print("0 transactions found. Exiting")
        return

    # Write to output file
    with open(
        os.path.join(out_dir, "all_transactions.csv"), "w", newline=""
    ) as f_stream:
        writer = csv.writer(f_stream)
        writer.writerows(all_trans)

    # Check for uncategorized vendors
    uncat = dict()
    for trans in all_trans:
        date, amount, vendor, cat = trans
        main_cat = cat.split(".")[0]

        if main_cat == "~":
            if vendor not in uncat:
                uncat[vendor] = []
            uncat[vendor].append((date, amount))

    for vendor in uncat:
        uncat[vendor] = sorted(uncat[vendor], key=lambda t: t[0].to_int())

    # Write uncategorized vendors to file
    out_txt = ""

    if len(uncat) > 0:
        print(f"Warning: {len(uncat)} uncategorized vendors found:")
        for vendor in sorted(uncat):
            out_txt += f"{vendor}:\n"
            for trans in uncat[vendor]:
                date, amount = trans
                out_txt += f"\t{date} | {amount}\n"
        out_txt = out_txt[:-1]

        print(out_txt)

        with open(os.path.join(out_dir, "uncategorized.txt"), "w") as f_stream:
            f_stream.write(out_txt)

        print(
            f"Uncategorized vendors written to {os.path.join(out_dir, 'uncategorized.txt')}"
        )
