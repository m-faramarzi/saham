from __future__ import annotations

import logging
from typing import Optional

from client import HttpClient
from state import SymbolState
from storage import TweetWriter

URL = "https://www.sahamyab.com/guest/twiter/list?v=0.1"


class SahamyabCrawler:

    def __init__(
        self,
        client: HttpClient,
        state: SymbolState,
    ):

        self.client = client
        self.state = state
        self.logger = logging.getLogger("SahamyabCrawler")

    def crawl_symbol(self, symbol: str, today: str) -> int:
        """
        Returns
        -------
        number of new tweets
        """

        previous_last_id = self.state.last_id(symbol)

        newest_id: Optional[int] = None
        page = 0
        next_id = None
        new_count = 0
        stop = False

        with TweetWriter(symbol) as writer:

            while True:

                payload = {
                    "page": page,
                    "tag": symbol,
                }

                if next_id is not None:
                    payload["id"] = next_id

                data = self.client.post_json(
                    URL,
                    payload,
                )

                items = data.get("items", [])

                if not items:
                    break

                for tweet in items:

                    tweet_id = tweet["id"]

                    #
                    # duplicate
                    #
                    if previous_last_id is not None and tweet_id == previous_last_id:
                        stop = True
                        break

                    if newest_id is None:
                        newest_id = tweet_id

                    writer.append(tweet)

                    new_count += 1

                if stop:
                    break

                if not data.get("hasMore", False):
                    break

                next_id = items[-1]["id"]

                page += 1

        #
        # update state
        #

        if newest_id is not None:

            self.state.update(
                symbol,
                last_seen=today,
                last_id=newest_id,
            )

        else:

            self.state.update(
                symbol,
                last_seen=today,
            )

        return new_count
