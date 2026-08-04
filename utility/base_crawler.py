import json
from abc import ABC, abstractmethod
from model.news_item import NewsItem
from datetime import datetime
from pathlib import Path

class BaseCrawler(ABC):
    
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(self):
        self.saved_ids: set[str] = set()
        
    @abstractmethod
    def extract_links(self, url: str) -> list[NewsItem]:
        pass
    
    @abstractmethod
    def scrape_page(self, news_item:NewsItem) -> NewsItem:        
        pass

    def append_json_file(self, news_list: list[NewsItem]):
        today = f"{datetime.now():%Y%m%d}"
        for item in news_list:
            if item.id not in self.saved_ids:

                filename = (
                    f"news/{item.source}/{today}_{item.category}.json"
                )

                Path(filename).parent.mkdir(parents=True, exist_ok=True)

                with open(filename, "a", encoding="utf-8") as f:
                    json.dump(item.model_dump(mode="json"), f, ensure_ascii=False)
                    json.dump(item.model_dump(), f, ensure_ascii=False)
                    f.write("\n")
                    self.saved_ids.add(item.id)
            else:
                print(item.id + "----" + item.title + " IS DUPLICATED")

    def crawl(self, url: str) -> list[NewsItem]:
        newslinks = self.extract_links(url)
        news_list: list[NewsItem] = []
        for link in newslinks:
            try:
                news = self.scrape_page(link)
                news_list.append(news)
            except Exception as ex:
                print(ex)
        return news_list