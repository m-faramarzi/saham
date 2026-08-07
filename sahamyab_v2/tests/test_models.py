from __future__ import annotations

import unittest

from sahamyab_v2.hashtags import HashtagExtractor
from sahamyab_v2.models import TweetItem


def tweet_payload(tweet_id: str = "101", like_count: str = "2") -> dict:
    return {
        "id": tweet_id,
        "sendTime": "2026-08-03T14:13:59Z",
        "sendTimePersian": "1405/05/12 17:43",
        "senderName": "کاربر",
        "senderUsername": "user",
        "senderProfileImage": "default",
        "content": "خبر #فولاد و #بازار_سرمایه",
        "parentContent": "متن قبلی #شاخص‌کل",
        "likeCount": like_count,
        "commentCount": "1",
        "type": "twit",
        "scoredPostDate": "1785766530511",
        "finalPullDatePersian": "",
        "aFutureApiField": {"preserved": True},
    }


class TweetItemTests(unittest.TestCase):
    def test_validates_counts_and_preserves_future_fields(self) -> None:
        tweet = TweetItem.model_validate(tweet_payload())

        self.assertEqual(tweet.id, "101")
        self.assertEqual(tweet.like_count, 2)
        dumped = tweet.model_dump(mode="json", by_alias=True)
        self.assertEqual(dumped["aFutureApiField"], {"preserved": True})

    def test_extracts_main_and_parent_hashtags(self) -> None:
        tweet = TweetItem.model_validate(tweet_payload())
        hashtags = HashtagExtractor().extract_tweet(tweet)

        self.assertEqual(hashtags, {"فولاد", "بازار_سرمایه", "شاخص‌کل"})


if __name__ == "__main__":
    unittest.main()
