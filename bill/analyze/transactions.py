from __future__ import annotations
from typing import TypedDict

from ..utility.date import Date
from ..utility import helpers


class Transactions:
    class Transaction(TypedDict):
        date: Date
        amount: float
        vendor: str
        category: str

    def __init__(self, transactions: list = []):
        self.transactions = []

        for transaction in transactions:
            self.add_transaction(*transaction)

    def add_transaction(self, date: str, amount: str, vendor: str, category: str):
        transaction: Transactions.Transaction = {
            "date": Date(date),
            "amount": helpers.to_float(amount),
            "vendor": vendor,
            "category": category,
        }

        self.transactions.append(transaction)

    def sort(self):
        self.transactions.sort(key=lambda t: t["date"].to_int())

    def by_category(self) -> dict[str, Transactions]:
        transactions: dict[str, Transactions] = {}

        for transaction in self.transactions:
            date = str(transaction["date"])
            amount = str(transaction["amount"])
            vendor = transaction["vendor"]
            category = transaction["category"]

            sub_cats = category.split(".")
            while len(sub_cats) > 0:
                sub_category = ".".join(sub_cats)
                sub_cats = sub_cats[:-1]

                if sub_category not in transactions:
                    transactions[sub_category] = Transactions()

                transactions[sub_category].add_transaction(
                    date, amount, vendor, category
                )

        return transactions

    def by_day(self) -> dict[Date, Transactions]:
        transactions: dict[Date, Transactions] = {}

        date_ind: Date = self.transactions[0]["date"]

        for transaction in self.transactions:
            date = transaction["date"]
            amount = str(transaction["amount"])
            vendor = transaction["vendor"]
            category = transaction["category"]

            while date != date_ind:
                transactions[date_ind] = Transactions()
                date_ind = date_ind.next_day()

            transactions[date].add_transaction(str(date), amount, vendor, category)

        return transactions

    def by_week(self) -> dict[Date, Transactions]:
        transactions: dict[Date, Transactions] = {}

        date_ind: Date = self.transactions[0]["date"].to_week()

        for transaction in self.transactions:
            date = transaction["date"]
            amount = str(transaction["amount"])
            vendor = transaction["vendor"]
            category = transaction["category"]

            if date.to_week() not in transactions:
                transactions[date.to_week()] = Transactions()
            while date.to_week() != date_ind:
                if date_ind not in transactions:
                    transactions[date_ind] = Transactions()
                date_ind = date_ind.next_week()

            transactions[date.to_week()].add_transaction(
                str(date), amount, vendor, category
            )

        return transactions

    def by_month(self) -> dict[str, Transactions]:
        transactions: dict[str, Transactions] = {}

        month_ind = self.transactions[0]["date"].month
        year_ind = self.transactions[0]["date"].year

        for transaction in self.transactions:
            date = transaction["date"]
            amount = str(transaction["amount"])
            vendor = transaction["vendor"]
            category = transaction["category"]

            month, year = date.month, date.year
            key = f"{month:0>2}/{year:0>4}"
            if key not in transactions:
                transactions[key] = Transactions()
            while month != month_ind and year != year_ind:
                key = f"{month_ind:0>2}/{year_ind:0>4}"
                if key not in transactions:
                    transactions[key] = Transactions()
                month_ind += 1
                if month_ind > 12:
                    month_ind = 1
                    year_ind += 1

            transactions[f"{month:0>2}/{year:0>4}"].add_transaction(
                str(date), amount, vendor, category
            )

        return transactions

    def by_year(self) -> dict[str, Transactions]:
        transactions: dict[str, Transactions] = {}

        year_ind = self.transactions[0]["date"].year

        for transaction in self.transactions:
            date = transaction["date"]
            amount = str(transaction["amount"])
            vendor = transaction["vendor"]
            category = transaction["category"]

            year = date.year

            while year != year_ind:
                transactions[f"{year_ind:0>4}"] = Transactions()
                year_ind += 1

            transactions[f"{year:0>4}"].add_transaction(
                str(date), amount, vendor, category
            )

        return transactions

    def __iter__(self):
        self._iter_i = 0
        return self

    def __next__(self):
        if self._iter_i < len(self.transactions):
            transaction = self.transactions[self._iter_i]
            self._iter_i += 1
            return transaction
        raise StopIteration
