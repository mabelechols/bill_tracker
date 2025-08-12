from Levenshtein import distance
import numpy as np
import os

try:
    from . import helpers
except:
    import helpers
import csv
import re


class CategorySelector:
    """
    A class to store categories and allow arbitrary selection using shorthand
    """

    def __init__(self, categories=[]):
        self.structure = {}

        for category in categories:
            if category is not None:
                self.add_category(category)

    def add_category(self, category):
        """
        Add a new category to the CategorySelector

        Args:
            category (str): New category string
        """

        def _insert_category(structure, category):
            cat_split = category.split(".")

            main = cat_split[0]
            tail = cat_split[1:]

            if main not in structure:
                structure[main] = {}
            if len(tail) > 0:
                _insert_category(structure[main], ".".join(tail))

        _insert_category(self.structure, category)

    def __str__(self):
        def str_helper(structure, level=1, level_str=""):
            out = ""
            for i, key in enumerate(structure):
                out += f"{'\t'*level}[{level_str}{i + 1}] {key}\n"
                out += str_helper(structure[key], level + 1, f"{level_str}{i + 1}.")
            return out

        return str_helper(self.structure)

    def select(self):
        def select_helper(structure, category):
            cat_split = category.split(".")

            main = cat_split[0]
            tail = cat_split[1:]

            try:
                main = int(main)
            except:
                main = main

            if isinstance(main, int):
                for i, key in enumerate(structure):
                    if i == main - 1:
                        return f"{key}.{select_helper(structure[key], ".".join(tail))}"
                raise IndexError(f"Index {main} is out of range")

            if main in structure:
                return f"{main}.{select_helper(structure[main], ".".join(tail))}"
            else:
                if len(tail) == 0:
                    return f"{main}"

                return f"{main}.{select_helper({}, ".".join(tail))}"

        print("Pick a category or enter a new one:")
        print(self)
        sym_cat = input("Category: ")
        cat = select_helper(self.structure, sym_cat).rstrip(".")
        print(cat)
        self.add_category(cat)

        return cat


def categorize(transactions, cat_file, write=False):
    uncat_ti: set = set(
        [i for i in range(len(transactions))]
    )  # Uncategorized transactions as indicies for transactions
    uncat_ui: set  # Uncategorized transactions as indicies for uncat_vendors
    categorized: list = [None] * len(
        transactions
    )  # List of categories by transaction in transactions (this is the output)
    uncat_vendors: list = (
        []
    )  # List of all vendors which did not get categorized by cat_file
    sel: CategorySelector  # Primary category selector instance
    dist_mat: np.ndarray  # Pairwise distance matrix for uncat_vendors
    ui_ti: dict = (
        {}
    )  # Dictionary to convert inds of uncat_vendors to inds of transactions

    # Check the category file and remove transactions which are already categorized
    file_cats = read_categories(cat_file)

    for i, transaction in enumerate(transactions):
        cat = trans_categorize(transaction["vendor"], file_cats)
        if cat != "~":
            uncat_ti.remove(i)
            categorized[i] = cat
        else:
            if transaction["vendor"] not in uncat_vendors:
                uncat_vendors.append(transaction["vendor"])
                ui_ti[len(uncat_vendors) - 1] = []
            ui_ti[len(uncat_vendors) - 1].append(i)

    uncat_ui = set([i for i in range(len(uncat_vendors))])
    used = []

    # Create selector
    sel = CategorySelector(categorized)
    for c in file_cats:
        sel.add_category(".".join(c[1:]))

    # Calculate distances for all pairs
    dist_mat = distance_matrix(uncat_vendors)

    N = 5  # How many matches to show per round
    if len(uncat_vendors) > 0:
        VEND_WIDTH = len(max(uncat_vendors, key=len))
    else:
        VEND_WIDTH = 0

    while len(uncat_ui) > 0:
        vi = uncat_ui.pop()
        vendor = uncat_vendors[vi]

        vendors = [vi]
        prev_l = 1

        while True:
            matches = closest_match(vendors, dist_mat, vendors + used)

            nn = min(N, len(uncat_ui))
            if len(vendors) == 1:
                print(f"Vendor:\n\t{vendor}")
            else:
                print(f"Vendors:")
                for i in vendors:
                    print(f"\t{uncat_vendors[i]}")

            print(
                f"The closest {nn} matches are ({len(uncat_ui) - len(vendors)} total remaining):"
            )
            for i in range(nn):
                mi = int(matches[1, i])
                mdist = matches[0, i]

                print(
                    f"\t[{i+1}] {uncat_vendors[mi]:<{VEND_WIDTH}} {helpers.percent_bar(1 - mdist)}"
                )

            selection = input("Matches: ")
            inds = helpers.parse_num_selection(selection)

            for i in inds:
                i = i - 1
                if i < nn and i >= 0:
                    vendors.append(int(matches[1, i]))
                else:
                    raise IndexError(f"{i+1} out of range for selection of length {nn}")

            if len(vendors) == prev_l:
                break

            prev_l = len(vendors)

        cat = sel.select()
        print("")
        for ui in vendors:
            tis = ui_ti[ui]
            for ti in tis:
                categorized[ti] = cat
            used.append(ui)
            try:
                uncat_ui.remove(ui)
            except:
                pass

        # write to file

        if write:
            with open(cat_file, "a+", newline="") as f_stream:
                writer = csv.writer(f_stream)
                for ui in vendors:
                    vend = uncat_vendors[ui]
                    writer.writerow([vend, *cat.split(".")])

    # Cleanup

    categories = {}
    for i, trans in enumerate(transactions):
        cat = categorized[i]

        if cat is not None:
            categories[trans["vendor"]] = cat

    for i, trans in enumerate(transactions):
        cat = categorized[i]

        if cat is None and trans["vendor"] in categories:
            categorized[i] = categories[trans]

    return categorized


def closest_match(
    i: int | list[int], distance_matrix: np.ndarray, exclude: list[int] = []
):
    """
    Return a sorted array of distances and transaction indices

    Args:
        i (int | list[int]): The index or indices of the transactions to include
        distance_matrix (np.ndarray): Pairwise distance matrix for all transactions
        exclude (list[int]): A list of indices to ignore when sorting

    Returns:
        ndarray: Sorted array of distances and transaction indices
    """

    if isinstance(i, int):
        dist_vect = distance_matrix[i, :]
    elif isinstance(i, list):
        dist_vect = distance_matrix[i[0], :]
        for ii in i[1:]:
            dist_vect = np.minimum(dist_vect, distance_matrix[ii, :])
    else:
        raise TypeError("i must be an int or list[int]")

    ind_vect = np.arange(dist_vect.size)

    sort = np.vstack((dist_vect, ind_vect))
    sort = np.delete(sort, exclude, axis=1)
    raw_matches = sort[:, sort[0, :].argsort()]

    return raw_matches


def distance_matrix(vendors: list):
    """
    Calculate a pairwise (Levenshtein) distance matrix for a list of vendors

    Args:
        vendors (list): A list of strings to calculate the distance between

    Returns:
        ndarray: A (len(vendors),len(vendors)) shaped np.ndarray with pairwise distances
    """
    dist_mat = np.zeros((len(vendors), len(vendors)))

    for i in range(len(vendors)):
        vend_1 = vendors[i]
        for j in range(i + 1, len(vendors)):
            vend_2 = vendors[j]
            dist = distance(vend_1, vend_2) / max(len(vend_1), len(vend_2))
            dist_mat[i, j] = dist
            dist_mat[j, i] = dist

    return dist_mat


def trans_categorize(vendor, categories):
    """
    Returns a string match to a given set of categories

        Parameters:
            vendor (str): The string to categorize
            categories (list): A list of categories in the form (reg_ex, category, subcategory, ...)

        Returns:
            str: The first matched category
    """

    for line in categories:
        if line[0].strip() == vendor.strip():
            return ".".join([line[n].strip() for n in range(1, len(line))])
    return "~"


def read_categories(cat_file):
    """
    Read category regex from cat_file and return a list of all categories found

        Parameters:
            cat_file (str): Path to the categories csv file

        Returns:
            list: All categories in the file
    """

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

                category = ""
                for l in line[1:]:
                    if l.strip() != "":
                        category += l
                        category += "."

                reg_ex = line[0]

                categories.append((reg_ex, *category[:-1].split(".")))

    return categories
