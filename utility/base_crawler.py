import json
from abc import ABC, abstractmethod
from model.news_item import NewsItem
from datetime import datetime
from pathlib import Path


class BaseCrawler(ABC):
    saved_ids: set[str]

    def __init__(self):
        self.news_list: list[NewsItem] = []
        # self.saved_ids= set()

    @abstractmethod
    def extract_links(self, url: str) -> list[str]:
        pass

    def append_json_file(self, news_list: list[NewsItem]):
        for item in news_list:
            if item.id not in self.saved_ids:

                filename = (
                    f"news/{item.source}/{datetime.now():%Y%m%d}_{item.category}.json"
                )

                Path(filename).parent.mkdir(parents=True, exist_ok=True)

                with open(filename, "a", encoding="utf-8") as f:
                    json.dump(item, f, ensure_ascii=False)
                    f.write("\n")
                    self.saved_ids.add(item.id)
            else:
                print(item.id + "----" + item.title + " IS DUPLICATED")

    def crawl(self, url: str) -> list[NewsItem]:
        links = self.extract_links(url)

        for link in links:
            news = self.scrape_page(link)
            self.news_list.append(news)
        return self.news_list

    @abstractmethod
    def scrape_page(self, page_url: str) -> NewsItem:
        """
        Extract one news page and return NewsItem
        """
        pass
