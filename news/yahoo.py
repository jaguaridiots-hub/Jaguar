from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request

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


class YahooFinanceNewsProvider:
    name = "Yahoo Finance"

    DEFAULT_URL = (
        "https://query1.finance.yahoo.com/v1/finance/search"
    )

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 8.0,
        opener=None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self.base_url = (
            base_url
            or os.environ.get(
                "JAGUAR_YAHOO_NEWS_URL",
                self.DEFAULT_URL,
            )
        )
        self.timeout = float(timeout)
        self._opener = opener or urllib.request.urlopen

    @staticmethod
    def _search_term(query: NewsQuery) -> str:
        if query.symbol:
            aliases = {
                "BTCUSDT": "bitcoin",
                "ETHUSDT": "ethereum",
                "SOLUSDT": "solana",
                "BNBUSDT": "BNB",
                "XRPUSDT": "XRP",
                "RELIANCE.NS": "Reliance Industries",
                "TCS.NS": "TCS Tata Consultancy Services",
                "HDFCBANK.NS": "HDFC Bank",
                "^NSEI": "Nifty 50",
                "GOLD": "gold futures",
                "SILVER": "silver futures",
                "AAPL": "Apple",
                "MSFT": "Microsoft",
                "NVDA": "NVIDIA",
                "SPY": "S&P 500",
                "QQQ": "Nasdaq 100",
            }
            return aliases.get(
                query.symbol.upper(),
                query.symbol,
            )

        terms = {
            "CRYPTO": "cryptocurrency bitcoin ethereum",
            "NSE": "India Nifty NSE stocks",
            "MCX": "gold silver commodities futures",
            "US": "US stocks S&P 500 Nasdaq",
            "MACRO": "Federal Reserve inflation interest rates economy",
            "MARKET": "financial markets stocks",
        }

        return terms.get(
            query.category.upper(),
            "financial markets",
        )

    def fetch(self, query: NewsQuery) -> list[NewsItem]:
        params = urllib.parse.urlencode(
            {
                "q": self._search_term(query),
                "newsCount": min(max(query.limit, 1), 50),
                "quotesCount": 0,
            }
        )

        request = urllib.request.Request(
            f"{self.base_url}?{params}",
            headers={
                "User-Agent": "JaguarQuantX/3.0 NewsProvider",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                payload = response.read()
        except (TimeoutError, socket.timeout) as exc:
            raise NewsProviderError(
                "Yahoo Finance request timed out",
                provider=self.name,
                kind=NewsFailureKind.TIMEOUT,
            ) from exc
        except urllib.error.HTTPError as exc:
            raise NewsProviderError(
                f"Yahoo Finance HTTP {exc.code}",
                provider=self.name,
                kind=NewsFailureKind.HTTP,
            ) from exc
        except urllib.error.URLError as exc:
            raise NewsProviderError(
                "Yahoo Finance network failure",
                provider=self.name,
                kind=NewsFailureKind.NETWORK,
            ) from exc
        except OSError as exc:
            raise NewsProviderError(
                "Yahoo Finance operating-system/network failure",
                provider=self.name,
                kind=NewsFailureKind.NETWORK,
            ) from exc

        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NewsProviderError(
                "Yahoo Finance returned invalid JSON",
                provider=self.name,
                kind=NewsFailureKind.INVALID_PAYLOAD,
            ) from exc

        raw_items = data.get("news", [])

        if not isinstance(raw_items, list):
            raise NewsProviderError(
                "Yahoo Finance news payload is malformed",
                provider=self.name,
                kind=NewsFailureKind.INVALID_PAYLOAD,
            )

        items: list[NewsItem] = []
        seen: set[str] = set()

        for raw in raw_items:
            if not isinstance(raw, dict):
                continue

            title = raw.get("title")
            url = raw.get("link")
            published = raw.get("providerPublishTime")

            valid = valid_item(
                title=title,
                url=url,
                published_at=published,
            )

            if valid is None:
                continue

            clean_title, clean_url, clean_time = valid

            if query.symbol and not (
                matches_symbol(clean_title, query.symbol)
                or any(
                    str(ticker).upper() == query.symbol.upper()
                    for ticker in raw.get("relatedTickers", [])
                    if ticker is not None
                )
            ):
                continue

            item_id = str(
                raw.get("uuid")
                or make_item_id(clean_title, clean_url)
            )

            if item_id in seen:
                continue

            seen.add(item_id)

            items.append(
                NewsItem(
                    item_id=item_id,
                    publisher=str(
                        raw.get("publisher")
                        or "Yahoo Finance"
                    ).strip(),
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
                "Yahoo Finance returned no usable news items",
                provider=self.name,
                kind=NewsFailureKind.EMPTY,
            )

        return items
