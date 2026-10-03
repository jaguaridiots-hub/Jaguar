from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from market.live_loader import load_market
from market.watchlist import WATCHLIST

from scanner.engine import ScannerEngine
from scanner.models import ScannerCandidate, ScannerSnapshot


MarketLoader = Callable[..., Sequence[Mapping[str, Any]]]


class ScannerService:
    """
    Watchlist discovery service.

    Market loading is injected so scanning can be tested without network access.
    """

    def __init__(
        self,
        *,
        loader: MarketLoader = load_market,
        watchlist: Iterable[str] = WATCHLIST,
        timeframes: Sequence[str] = ("15m", "1h", "4h", "1d"),
        limit: int = 300,
        engine: ScannerEngine | None = None,
    ):
        if limit < 220:
            raise ValueError("limit must be >= 220")

        normalized_watchlist = tuple(
            str(symbol).strip().upper()
            for symbol in watchlist
            if str(symbol).strip()
        )

        if not normalized_watchlist:
            raise ValueError("watchlist cannot be empty")

        normalized_timeframes = tuple(
            str(value).strip()
            for value in timeframes
            if str(value).strip()
        )

        if not normalized_timeframes:
            raise ValueError("timeframes cannot be empty")

        self.loader = loader
        self.watchlist = normalized_watchlist
        self.timeframes = normalized_timeframes
        self.limit = int(limit)
        self.engine = engine or ScannerEngine()

    def scan_watchlist(
        self,
        *,
        symbols: Iterable[str] | None = None,
        now_ms: int | None = None,
    ) -> ScannerSnapshot:
        selected = tuple(
            str(symbol).strip().upper()
            for symbol in (
                symbols
                if symbols is not None
                else self.watchlist
            )
            if str(symbol).strip()
        )

        generated_at = int(now_ms or (time.time() * 1000))

        candidates: list[ScannerCandidate] = []
        errors: list[dict[str, str]] = []
        degraded = False

        for symbol in selected:
            candles_by_timeframe: dict[
                str,
                Sequence[Mapping[str, Any]],
            ] = {}

            primary_interval = self.timeframes[0]
            primary_loaded = False

            for timeframe in self.timeframes:
                try:
                    candles = self.loader(
                        symbol,
                        interval=timeframe,
                        limit=self.limit,
                    )

                    candles_by_timeframe[timeframe] = candles

                    if timeframe == primary_interval:
                        primary_loaded = True

                except Exception as exc:
                    degraded = True
                    errors.append(
                        {
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "error": str(exc),
                        }
                    )

            if not primary_loaded:
                continue

            try:
                candidate = self.engine.scan(
                    symbol,
                    primary_interval,
                    candles_by_timeframe,
                    now_ms=generated_at,
                )
            except Exception as exc:
                degraded = True
                errors.append(
                    {
                        "symbol": symbol,
                        "timeframe": primary_interval,
                        "error": str(exc),
                    }
                )
                continue

            if candidate.is_candidate:
                candidates.append(candidate)

        candidates.sort(
            key=lambda item: (
                abs(item.score - 50),
                item.confidence,
            ),
            reverse=True,
        )

        if selected and not candidates and errors:
            status = "UNAVAILABLE"
        elif degraded:
            status = "DEGRADED"
        else:
            status = "CURRENT"

        return ScannerSnapshot(
            status=status,
            generated_at=generated_at,
            scanned_symbols=len(selected),
            candidate_count=len(candidates),
            candidates=tuple(candidates),
            errors=tuple(errors),
        )
