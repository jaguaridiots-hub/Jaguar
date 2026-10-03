"""
EvidenceBlock – ADR-002 compliant evidence container (Brain V5 contract).
"""
from dataclasses import dataclass, field
from typing import List, Any, Optional
import time

@dataclass
class SubEvidence:
    """Strongly typed sub‑evidence item."""
    key: str
    value: Any
    confidence: float = 0.5

@dataclass
class EvidenceBlock:
    # ----- Canonical fields (Brain V5) -----
    engine: str                     # e.g., "SMC"
    signal: str                     # e.g., "BULLISH", "BEARISH", "NEUTRAL"
    confidence_raw: float           # 0..1
    confidence_calibrated: Optional[float] = None
    sub_evidence: List[SubEvidence] = field(default_factory=list)
    lifecycle_state: str = "DETECTED"
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """If calibrated confidence is not provided, default to raw."""
        if self.confidence_calibrated is None:
            self.confidence_calibrated = self.confidence_raw

    # ----- Backward compatibility properties (for audit & legacy) -----
    @property
    def engine_name(self) -> str:
        """Legacy alias for `engine`."""
        return self.engine

    @property
    def confidence(self) -> float:
        """Legacy alias for `confidence_raw`."""
        return self.confidence_raw

    @property
    def calibrated_confidence(self) -> float:
        """Legacy alias for `confidence_calibrated`."""
        return self.confidence_calibrated

# ADR-002 schema definition (canonical)
ADR002_SCHEMA = {
    "engine": str,
    "signal": str,
    "confidence_raw": float,
    "confidence_calibrated": float,
    "sub_evidence": list,          # list of SubEvidence
    "lifecycle_state": str,
    "timestamp": float,
}
