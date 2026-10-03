from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Alert:
    alert_type: str
    severity: str
    message: str
    dedup_key: str
    symbol: str | None = None
    timestamp: str | None = None

    @property
    def execution_authority(self) -> str:
        return "NONE"

    @property
    def alert_id(self) -> str:
        return self.dedup_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "symbol": self.symbol,
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
            "message": self.message,
            "dedup_key": self.dedup_key,
            "execution_authority": self.execution_authority,
        }
