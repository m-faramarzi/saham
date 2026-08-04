from __future__ import annotations

import logging
from typing import Any

import requests
from requests import Session, Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.sahamyab.com",
    "Referer": "https://www.sahamyab.com/",
}


class HttpClient:
    """
    Thread-safe HTTP client.

    Features
    --------
    * Session
    * Connection Pool
    * Automatic Retry
    * Timeout
    * JSON helpers
    """

    def __init__(
        self,
        timeout: int = 30,
        pool_size: int = 20,
        retry_count: int = 5,
        backoff_factor: float = 2.0,
    ):

        self.timeout = timeout

        retry = Retry(
            total=retry_count,
            connect=retry_count,
            read=retry_count,
            backoff_factor=backoff_factor,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=frozenset(
                [
                    "GET",
                    "POST",
                ]
            ),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=pool_size,
            pool_maxsize=pool_size,
        )

        self.session = Session()

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update(DEFAULT_HEADERS)

        self.logger = logging.getLogger("HttpClient")

    def get(
        self,
        url: str,
        **kwargs,
    ) -> Response:

        response = self.session.get(
            url,
            timeout=self.timeout,
            **kwargs,
        )

        response.raise_for_status()

        return response

    def post(
        self,
        url: str,
        json: dict | None = None,
        **kwargs,
    ) -> Response:

        response = self.session.post(
            url,
            json=json,
            timeout=self.timeout,
            **kwargs,
        )

        response.raise_for_status()

        return response

    def get_json(
        self,
        url: str,
        **kwargs,
    ) -> dict[str, Any]:

        return self.get(
            url,
            **kwargs,
        ).json()

    def post_json(
        self,
        url: str,
        payload: dict,
        **kwargs,
    ) -> dict[str, Any]:

        return self.post(
            url,
            json=payload,
            **kwargs,
        ).json()

    def close(self):

        self.session.close()

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc, tb):

        self.close()
