from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse


SYMBOL_ALIASES: dict[str, tuple[str, ...]] = {
    "BTCUSDT": ("bitcoin", "btc", "btc-usd"),
    "ETHUSDT": ("ethereum", "eth", "eth-usd"),
    "SOLUSDT": ("solana", "sol", "sol-usd"),
    "BNBUSDT": ("bnb", "binance coin"),
    "XRPUSDT": ("xrp", "ripple"),
    "RELIANCE.NS": ("reliance", "reliance industries"),
    "TCS.NS": ("tcs", "tata consultancy services"),
    "HDFCBANK.NS": ("hdfc bank", "hdfcbank"),
    "^NSEI": ("nifty", "nifty 50", "nse"),
    "GOLD": ("gold", "gc=f", "gold futures"),
    "SILVER": ("silver", "si=f", "silver futures"),
    "AAPL": ("apple", "aapl"),
    "MSFT": ("microsoft", "msft"),
    "NVDA": ("nvidia", "nvda"),
    "SPY": ("s&p 500", "sp 500", "spy"),
    "QQQ": ("nasdaq", "nasdaq 100", "qqq"),
}


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "MACRO": (
        "federal reserve",
        "fed",
        "interest rate",
        "inflation",
        "cpi",
        "ppi",
        "jobs",
        "employment",
        "gdp",
        "central bank",
        "treasury yield",
        "economic",
    ),
    "CRYPTO": (
        "bitcoin",
        "ethereum",
        "crypto",
        "cryptocurrency",
        "solana",
        "ripple",
        "xrp",
        "blockchain",
    ),
    "NSE": (
        "nifty",
        "sensex",
        "nse",
        "bse",
        "india stocks",
        "indian market",
    ),
    "MCX": (
        "gold",
        "silver",
        "mcx",
        "commodities",
        "crude oil",
    ),
    "US": (
        "s&p 500",
        "sp 500",
        "nasdaq",
        "dow",
        "wall street",
        "us stocks",
        "nyse",
        "nyse:",
        "nasdaq:",
    ),
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = re.sub(r"<[^>]+>", " ", str(value))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(value: Any) -> str:
    url = str(value or "").strip()

    if not url:
        return ""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    return url


def parse_timestamp(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(
                float(value),
                tz=timezone.utc,
            ).isoformat()
        except (OverflowError, OSError, ValueError):
            return None

    raw = str(value).strip()
    if not raw:
        return None

    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        pass

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def valid_item(
    *,
    title: Any,
    url: Any,
    published_at: Any,
) -> tuple[str, str, str] | None:
    clean_title = clean_text(title)
    clean_url = normalize_url(url)
    clean_time = parse_timestamp(published_at)

    if len(clean_title) < 4:
        return None

    if not clean_url:
        return None

    if clean_time is None:
        return None

    return clean_title, clean_url, clean_time


def make_item_id(title: str, url: str) -> str:
    digest = hashlib.sha256(
        f"{url}|{title}".encode("utf-8")
    ).hexdigest()

    return digest[:24]


def aliases_for(symbol: str | None) -> tuple[str, ...]:
    if not symbol:
        return ()

    return SYMBOL_ALIASES.get(
        symbol.upper().strip(),
        (symbol.lower().strip(),),
    )


def matches_symbol(title: str, symbol: str | None) -> bool:
    aliases = aliases_for(symbol)

    if not aliases:
        return True

    haystack = title.lower()

    return any(alias.lower() in haystack for alias in aliases)


def infer_category(title: str, requested: str) -> str:
    requested = str(requested or "MARKET").upper().strip()

    if requested != "MARKET":
        return requested

    haystack = title.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    return "MARKET"
