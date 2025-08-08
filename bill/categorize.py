from Levenshtein import distance
import numpy as np
import matplotlib.pyplot as plt
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

            structure[main] = {}
            if len(tail) > 0:
                _insert_category(structure[main], ".".join(tail))

        _insert_category(self.structure, category)

    def __str__(self):
        def str_helper(structure, level=1, level_str=""):
            out = ""
            for i, key in enumerate(structure):
                out += f"{"\t"*level}[{level_str}{i + 1}] {key}\n"
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
                return f"{main}"

        print("Pick a category or enter a new one:")
        print(self)
        sym_cat = input("Category: ")
        cat = select_helper(self.structure, sym_cat).rstrip(".")
        self.add_category(cat)

        return cat


def categorize(transactions, cat_file):
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
    for i, transaction in enumerate(transactions):
        cat = trans_categorize(transaction["vendor"], read_categories(cat_file))
        if cat != "~":
            uncat_ti.remove(i)
            categorized[i] = cat
        else:
            if transaction["vendor"] not in uncat_vendors:
                uncat_vendors.append(transaction["vendor"])
            ui_ti[len(uncat_vendors) - 1] = i

    uncat_ui = set([i for i in range(len(uncat_vendors))])

    # Create selector
    sel = CategorySelector(categorized)

    # Calculate distances for all pairs
    dist_mat = distance_matrix(uncat_vendors)

    N = 5  # How many matches to show per round

    while len(uncat_ui) > 0:
        vi = uncat_ui.pop()
        vendor = uncat_vendors[vi]

        matches = closest_match(vi, dist_mat)

        nn = min(N, len(uncat_ui))
        print(f"{vendor}\nThe closest {nn} matches are:")
        for i in range(nn):
            mi = int(matches[1, i])
            mdist = matches[0, i]

            print(f"\t[{i+1}] {uncat_vendors[mi]}")

        input()


def closest_match(i: int | list[int], distance_matrix: np.ndarray):
    """
    Return a sorted array of distances and transaction indices

    Args:
        i (int | list[int]): The index or indices of the transactions to include
        distance_matrix (np.ndarray): Pairwise distance matrix for all transactions

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
    return sort[:, sort[0, :].argsort()]


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
        if re.search(line[0], vendor, re.IGNORECASE) is not None:
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

                reg_ex, category = line[0], ".".join(line[1:])
                categories.append((reg_ex, *category.split(".")))

    return categories


def match_level(dist: float):
    """
    Returns a string (for printing) of the confidence of a match

    Args:
        dist (float): Normalized [0,1] distance between words

    Returns:
        str: Human readable match confidence
    """
    MATCH_LEVELS = [0.15, 0.3, 0.5]
    MATCH_STRINGS = ["Very Good", "Good", "OK", "Bad"]

    for i in range(len(MATCH_LEVELS)):
        if dist < MATCH_LEVELS[i]:
            return MATCH_STRINGS[i]

    return MATCH_STRINGS[-1]


if __name__ == "__main__":
    TRANS_FILE = "C:\\Users\\aaech\\Documents\\Important\\Bill Tracking\\bill_output\\all_transactions.csv"
    CAT_FILE = "C:\\Users\\aaech\\Documents\\Important\\Bill Tracking\\_categories.csv"

    transactions = []

    with open(TRANS_FILE, "r") as f_stream:
        reader = csv.reader(f_stream)

        for line in reader:
            transaction = {"date": line[0], "amount": line[1], "vendor": line[2]}

            transactions.append(transaction)

    categorize(transactions, CAT_FILE)
