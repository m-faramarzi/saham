from __future__ import annotations

import re
import unicodedata

from .models import TweetItem


HASHTAG_PATTERN = re.compile(r"#([\w\u0600-\u06ff\u200c]+)", re.UNICODE)


class HashtagExtractor:
    """Extracts every hashtag without applying a stock-symbol allow-list."""

    @staticmethod
    def extract_text(text: str | None) -> set[str]:
        if not text:
            return set()
        return {
            unicodedata.normalize("NFC", value).replace("\u200e", "").replace("\u200f", "")
            for value in HASHTAG_PATTERN.findall(text)
            if value
        }

    def extract_tweet(self, tweet: TweetItem) -> set[str]:
        hashtags = self.extract_text(tweet.content)
        hashtags.update(self.extract_text(tweet.parent_content))
        return hashtags

    def extract_many(self, tweets: list[TweetItem]) -> set[str]:
        result: set[str] = set()
        for tweet in tweets:
            result.update(self.extract_tweet(tweet))
        return result
