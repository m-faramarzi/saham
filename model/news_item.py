from pydantic import BaseModel, Field
from datetime import datetime


class NewsItem(BaseModel):

    source: str = ""
    id: str = ""
    title: str = ""
    category: str = ""
    type: str = ""
    publish_date_j: str = ""
    publish_date_g: datetime | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    short_url: str = ""
    news_url: str = ""
    body: str = ""
