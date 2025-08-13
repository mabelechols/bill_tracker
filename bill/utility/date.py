from __future__ import annotations

from functools import total_ordering


@total_ordering
class Date:
    MONDAY_MOD = 3
    DAYS = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    MONTHS = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    def __init__(self, date_str: str):
        mo, da, yr = date_str.split("/")

        self.month = int(mo)
        self.day = int(da)
        self.year = int(yr)
        self.leap = Date.is_leap(self.year)

    def to_int(self) -> int:
        days = 0
        for i in range(1, self.month):
            days += Date.month_days(i, self.year)

        for i in range(self.year):
            days += 365 + Date.is_leap(i)

        return days + self.day

    def to_week(self) -> Date:
        mod = self.to_int() % 7
        week_rank = self.to_int() - mod + Date.MONDAY_MOD

        monday = Date.from_int(week_rank)

        return monday

    def next_day(self) -> Date:
        day = self.day + 1
        month = self.month
        year = self.year

        if day > Date.month_days(self.month, self.year):
            day = 1
            month += 1

        if month > 12:
            month = 1
            year += 1

        return Date(f"{month}/{day}/{year}")

    def next_week(self) -> Date:
        week = self

        for _ in range(7):
            week = week.next_day()

        return week

    def since_epoch(self) -> int:
        return self.to_int() - Date("01/01/1900").to_int() + 1

    def __repr__(self) -> str:
        return f"{self.month:0>2}/{self.day:0>2}/{self.year:0>4}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented

        return (
            self.month == other.month
            and self.day == other.day
            and self.year == other.year
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented

        return self.to_int() < other.to_int()

    def __hash__(self) -> int:
        return self.to_int()

    @staticmethod
    def is_leap(year: int) -> bool:
        if year % 4 == 0:
            if year % 100 == 0:
                if year % 400 == 0:
                    return True
                return False
            return True
        return False

    @staticmethod
    def month_days(month: int, year: int) -> int:
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month != 2:
            return 30
        else:
            return 28 + Date.is_leap(year)

    @staticmethod
    def from_int(rank: int) -> Date:
        year = 0
        while rank > 365 + Date.is_leap(year):
            rank -= 365 + Date.is_leap(year)
            year += 1

        month = 1
        while rank > Date.month_days(month, year):
            rank -= Date.month_days(month, year)
            month += 1

        return Date(f"{month}/{rank}/{year}")
