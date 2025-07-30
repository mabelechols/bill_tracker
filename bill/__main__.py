import argparse
import os
from . import tracker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python -m bill",
        description="Utility to read and distill purchase information from bank statements. Currently supports: PNC Bank, Chase, FNB, Discover",
    )

    parser.add_argument(
        "statement_dir", type=str, help="Directory containing bank statements"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=str,
        help="Directory to output all_transactions.csv and uncategorized.txt into. Defalts to ./bill_output",
        default="./bill_output",
    )
    parser.add_argument(
        "category_file",
        nargs="?",
        type=str,
        help="Directory of categories.csv to use for categorization. Defalts to ./categories.csv",
        default="./categories.csv",
    )

    args = parser.parse_args()

    tracker.track(
        os.path.abspath(args.statement_dir),
        os.path.abspath(args.output_dir),
        os.path.abspath(args.category_file),
    )
