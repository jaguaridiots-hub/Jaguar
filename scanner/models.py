from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScannerEvidence:
    name: str
    signal: str
    score: int
    detail: str
    timeframe: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "signal": self.signal,
            "score": self.score,
            "detail": self.detail,
            "timeframe": self.timeframe,
        }


@dataclass(frozen=True)
class ScannerCandidate:
    symbol: str
    timeframe: str
    direction: str
    score: int
    confidence: int
    is_candidate: bool
    structure: dict[str, Any]
    data_quality: dict[str, Any]
    evidence: tuple[ScannerEvidence, ...] = field(default_factory=tuple)
    authority: str = "SCANNER_CANDIDATE_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "score": self.score,
            "confidence": self.confidence,
            "is_candidate": self.is_candidate,
            "structure": dict(self.structure),
            "data_quality": dict(self.data_quality),
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "authority": self.authority,
        }


@dataclass(frozen=True)
class ScannerSnapshot:
    status: str
    generated_at: int
    scanned_symbols: int
    candidate_count: int
    candidates: tuple[ScannerCandidate, ...] = field(default_factory=tuple)
    errors: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "scanned_symbols": self.scanned_symbols,
            "candidate_count": self.candidate_count,
            "candidates": [
                candidate.to_dict()
                for candidate in self.candidates
            ],
            "errors": [dict(item) for item in self.errors],
        }
