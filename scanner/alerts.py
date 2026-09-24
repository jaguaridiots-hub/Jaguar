from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from scanner.intelligence import ScannerAlert, ScannerIntelligence
from scanner.models import ScannerCandidate
from scanner.service import ScannerService


@dataclass(frozen=True)
class ScannerAlertSnapshot:
    status: str
    generated_at: int
    scanned_symbols: int
    candidate_count: int
    alert_count: int
    alerts: tuple[ScannerAlert, ...] = field(default_factory=tuple)
    errors: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "scanned_symbols": self.scanned_symbols,
            "candidate_count": self.candidate_count,
            "alert_count": self.alert_count,
            "alerts": [
                alert.to_dict()
                for alert in self.alerts
            ],
            "errors": [
                dict(item)
                for item in self.errors
            ],
        }


class ScannerAlertService:
    """
    Read-only alert projection over the R19 ScannerService.

    This layer enriches scanner candidates into contextual alerts.
    It does not persist alerts or invoke any trading authority.
    """

    def __init__(
        self,
        *,
        scanner: ScannerService | None = None,
        intelligence: ScannerIntelligence | None = None,
    ) -> None:
        self.scanner = scanner or ScannerService()
        self.intelligence = (
            intelligence or ScannerIntelligence()
        )

    def scan_watchlist(
        self,
        *,
        symbols: Iterable[str] | None = None,
        now_ms: int | None = None,
    ) -> ScannerAlertSnapshot:
        snapshot = self.scanner.scan_watchlist(
            symbols=symbols,
            now_ms=now_ms,
        )

        alerts: list[ScannerAlert] = []

        for candidate in snapshot.candidates:
            if not isinstance(candidate, ScannerCandidate):
                continue

            alerts.append(
                self.intelligence.enrich(candidate)
            )

        return ScannerAlertSnapshot(
            status=snapshot.status,
            generated_at=snapshot.generated_at,
            scanned_symbols=snapshot.scanned_symbols,
            candidate_count=snapshot.candidate_count,
            alert_count=len(alerts),
            alerts=tuple(alerts),
            errors=tuple(snapshot.errors),
        )
