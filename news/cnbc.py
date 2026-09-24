from __future__ import annotations

import socket
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from news.models import NewsItem
from news.normalizer import (
    infer_category,
    make_item_id,
    matches_symbol,
    valid_item,
)
from news.provider import (
    NewsFailureKind,
    NewsProviderError,
    NewsQuery,
)


class CNBCNewsProvider:
    name = "CNBC"

    DEFAULT_FEED_URL = (
        "https://www.cnbc.com/id/100727362/device/rss/rss.html"
    )

    def __init__(
        self,
        feed_url: str | None = None,
        timeout: float = 8.0,
        opener=None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self.feed_url = feed_url or self.DEFAULT_FEED_URL
        self.timeout = float(timeout)
        self._opener = opener or urllib.request.urlopen

    def fetch(self, query: NewsQuery) -> list[NewsItem]:
        request = urllib.request.Request(
            self.feed_url,
            headers={
                "User-Agent": "JaguarQuantX/3.0 NewsProvider",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
            method="GET",
        )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                payload = response.read()
        except (TimeoutError, socket.timeout) as exc:
            raise NewsProviderError(
                "CNBC request timed out",
                provider=self.name,
                kind=NewsFailureKind.TIMEOUT,
            ) from exc
        except urllib.error.HTTPError as exc:
            raise NewsProviderError(
                f"CNBC HTTP {exc.code}",
                provider=self.name,
                kind=NewsFailureKind.HTTP,
            ) from exc
        except urllib.error.URLError as exc:
            raise NewsProviderError(
                "CNBC network failure",
                provider=self.name,
                kind=NewsFailureKind.NETWORK,
            ) from exc
        except OSError as exc:
            raise NewsProviderError(
                "CNBC operating-system/network failure",
                provider=self.name,
                kind=NewsFailureKind.NETWORK,
            ) from exc

        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise NewsProviderError(
                "CNBC returned invalid RSS",
                provider=self.name,
                kind=NewsFailureKind.INVALID_PAYLOAD,
            ) from exc

        items: list[NewsItem] = []
        seen: set[str] = set()

        for element in root.findall(".//item"):
            title = element.findtext("title")
            link = element.findtext("link")
            published = (
                element.findtext("pubDate")
                or element.findtext("published")
                or element.findtext("date")
            )

            valid = valid_item(
                title=title,
                url=link,
                published_at=published,
            )

            if valid is None:
                continue

            clean_title, clean_url, clean_time = valid

            if not matches_symbol(clean_title, query.symbol):
                continue

            item_id = make_item_id(clean_title, clean_url)

            if item_id in seen:
                continue

            seen.add(item_id)

            items.append(
                NewsItem(
                    item_id=item_id,
                    publisher="CNBC",
                    title=clean_title,
                    published_at=clean_time,
                    url=clean_url,
                    symbol=query.symbol,
                    category=infer_category(
                        clean_title,
                        query.category,
                    ),
                    source=self.name,
                )
            )

            if len(items) >= query.limit:
                break

        if not items:
            raise NewsProviderError(
                "CNBC returned no usable news items",
                provider=self.name,
                kind=NewsFailureKind.EMPTY,
            )

        return items
