from utility.bourse_news_crawler import BourseNewsCrawler

if __name__ == "__main__":
    archives = [
        "https://www.boursenews.ir/fa/archive?service_id=1&sec_id=-1&cat_id=-1&rpp=100&from_date=1400/01/01&to_date=1405/06/31",
        "https://www.boursenews.ir/fa/archive?service_id=14&sec_id=-1&cat_id=-1&rpp=100&from_date=1400/01/01&to_date=1405/06/31",
        "https://www.boursenews.ir/fa/archive?service_id=3&sec_id=-1&cat_id=-1&rpp=100&from_date=1400/01/01&to_date=1405/06/31",
        "https://www.boursenews.ir/fa/archive?service_id=4&sec_id=-1&cat_id=-1&rpp=100&from_date=1400/01/01&to_date=1405/06/31",
    ]

    bourse_crawler = BourseNewsCrawler()
    for arch in archives:
        for page in range(100):
            url = f"{arch}" + f"&p={page+1}"
            news_list = bourse_crawler.crawl(url)
            bourse_crawler.append_json_file(news_list)
