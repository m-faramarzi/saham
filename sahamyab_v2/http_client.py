from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from requests import Response, Session
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
    def __init__(
        self,
        *,
        timeout: float = 30,
        pool_size: int = 10,
        retry_count: int = 5,
        backoff_factor: float = 1.0,
    ) -> None:
        self.timeout = timeout
        retry = Retry(
            total=retry_count,
            connect=retry_count,
            read=retry_count,
            status=retry_count,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(("GET", "POST")),
            raise_on_status=False,
            respect_retry_after_header=True,
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

    def post_json(self, url: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        response: Response = self.session.post(
            url,
            json=dict(payload),
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Sahamyab response must be a JSON object")
        return data

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
