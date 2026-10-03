from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from news.models import NewsSnapshot
from scanner.alerts import ScannerAlertService
from scanner.intelligence import ScannerAlert
from scanner.news_context import (
    ScannerAlertNewsContext,
    ScannerNewsContext,
)


@dataclass(frozen=True)
class ScannerAlertContextSnapshot:
    status: str
    generated_at: int
    scanned_symbols: int
    candidate_count: int
    alert_count: int
    context_count: int
    contexts: tuple[ScannerAlertNewsContext, ...] = field(
        default_factory=tuple
    )
    errors: tuple[dict[str, str], ...] = field(
        default_factory=tuple
    )
    authority: str = "SCANNER_ALERT_CONTEXT_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "scanned_symbols": self.scanned_symbols,
            "candidate_count": self.candidate_count,
            "alert_count": self.alert_count,
            "context_count": self.context_count,
            "contexts": [
                context.to_dict()
                for context in self.contexts
            ],
            "errors": [
                dict(item)
                for item in self.errors
            ],
            "authority": self.authority,
        }


class ScannerAlertContextService:
    """
    Read-only composition of ScannerAlert and NewsSnapshot.

    This layer provides contextual explainability only. It does not
    modify alerts or news, persist state, calculate trading authority,
    or invoke execution.
    """

    def __init__(
        self,
        *,
        alerts: ScannerAlertService | None = None,
        news: Any | None = None,
        context: ScannerNewsContext | None = None,
    ) -> None:
        if alerts is None:
            raise ValueError("alerts service is required")

        if news is None:
            raise ValueError("news service is required")

        self.alerts = alerts
        self.news = news
        self.context = context or ScannerNewsContext()

    def scan_watchlist(
        self,
        *,
        symbols: Iterable[str] | None = None,
        now_ms: int | None = None,
        refresh_news: bool = False,
    ) -> ScannerAlertContextSnapshot:
        alert_snapshot = self.alerts.scan_watchlist(
            symbols=symbols,
            now_ms=now_ms,
        )

        contexts: list[
            ScannerAlertNewsContext
        ] = []

        errors: list[dict[str, str]] = [
            dict(item)
            for item in alert_snapshot.errors
        ]

        news_by_symbol: dict[
            str,
            NewsSnapshot,
        ] = {}

        for alert in alert_snapshot.alerts:
            if not isinstance(
                alert,
                ScannerAlert,
            ):
                continue

            symbol = (
                str(alert.symbol)
                .strip()
                .upper()
            )

            if symbol not in news_by_symbol:
                try:
                    news_by_symbol[symbol] = (
                        self.news.get_news(
                            symbol=symbol,
                            category="MARKET",
                            limit=5,
                            refresh=refresh_news,
                        )
                    )

                except Exception as exc:
                    errors.append(
                        {
                            "symbol": symbol,
                            "error": str(exc),
                        }
                    )
                    continue

            try:
                contexts.append(
                    self.context.correlate(
                        alert,
                        news_by_symbol[symbol],
                        limit=5,
                    )
                )

            except Exception as exc:
                errors.append(
                    {
                        "symbol": symbol,
                        "error": str(exc),
                    }
                )

        return ScannerAlertContextSnapshot(
            status=str(
                alert_snapshot.status
            ).upper(),
            generated_at=int(
                alert_snapshot.generated_at
            ),
            scanned_symbols=int(
                alert_snapshot.scanned_symbols
            ),
            candidate_count=int(
                alert_snapshot.candidate_count
            ),
            alert_count=int(
                alert_snapshot.alert_count
            ),
            context_count=len(contexts),
            contexts=tuple(contexts),
            errors=tuple(errors),
        )
