from . import create_doc

if __name__ == "__main__":
    CSV = "Z:\\bill_tracker\\bill_output\\all_transactions.csv"
    FILE = "Z:/bill_tracker/bill_output/bills.xlsx"

    create_doc.create_xlsx(CSV, FILE)
