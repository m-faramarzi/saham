import re
from datetime import datetime

import jdatetime


class JalaliDateParser:

    MONTHS = {
        "فروردین": 1,
        "اردیبهشت": 2,
        "خرداد": 3,
        "تیر": 4,
        "مرداد": 5,
        "شهریور": 6,
        "مهر": 7,
        "آبان": 8,
        "آذر": 9,
        "دی": 10,
        "بهمن": 11,
        "اسفند": 12,
    }

    @staticmethod
    def normalize(text: str) -> str:
        """
        یکسان‌سازی حروف فارسی و اعداد
        """

        if text is None:
            return ""

        table = str.maketrans("۰۱۲۳۴۵۶۷۸۹كيى", "0123456789کیی")

        text = text.translate(table)

        text = text.replace("‌", " ")  # نیم‌فاصله
        text = text.replace("ـ", "")
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def build_regex(format_string: str) -> str:
        """
        تبدیل فرمت Oracle مانند
        DD MONTH YYYY - HH24:MI
        به Regular Expression
        """

        regex = re.escape(format_string)

        regex = regex.replace("DD", r"(?P<day>\d{1,2})")
        regex = regex.replace("MONTH", r"(?P<month>[^\d]+?)")
        regex = regex.replace("YYYY", r"(?P<year>\d{4})")
        regex = regex.replace("HH24", r"(?P<hour>\d{1,2})")
        regex = regex.replace("MI", r"(?P<minute>\d{1,2})")
        regex = regex.replace("SS", r"(?P<second>\d{1,2})")
        regex = regex.replace("WEEKDAY", r"(?P<weekday>[^\d]+?)")

        return "^" + regex + "$"

    @staticmethod
    def parse(text: str, format_string: str):

        text = JalaliDateParser.normalize(text)

        pattern = JalaliDateParser.build_regex(format_string)

        match = re.match(pattern, text)

        if not match:
            raise ValueError(f"Date '{text}' does not match '{format_string}'")

        g = match.groupdict()

        day = int(g["day"])
        month = JalaliDateParser.MONTHS[g["month"].strip()]
        year = int(g["year"])

        hour = int(g.get("hour") or 0)
        minute = int(g.get("minute") or 0)
        second = int(g.get("second") or 0)

        jalali = (
            f"{year:04d}-{month:02d}-{day:02d} " f"{hour:02d}:{minute:02d}:{second:02d}"
        )

        gregorian = jdatetime.datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
        ).togregorian()

        return jalali, gregorian
