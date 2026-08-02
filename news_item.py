class NewsItem(BaseModel):

    source: str

    news_id: str

    title: str

    category: str

    type: str

    publish_datetime_jalali: str
    publish_datetime_gregorian: datetime

    author: str | None

    tags: list[str]

    short_url: str

    news_url: str

    body: str
