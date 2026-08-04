from jalali_date_parser import JalaliDateParser

if __name__ == "__main__":

    publish_date_j, publish_date_g = JalaliDateParser.parse(
        "۰۴ مرداد ۱۴۰۵ - ۲۳:۴۵ یکشنبه", "DD MONTH YYYY - HH24:MI WEEKDAY"
    )
    print(publish_date_j, publish_date_g)
