"""
FusionResult
Institutional evidence fusion output.
"""

from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class FusionResult:
    # Raw EvidenceBlocks collected from the blackboard
    evidence_blocks: List[Any] = field(default_factory=list)

    # Confidence statistics (Phase 2B.5)
    average_raw_confidence: float = 0.0
    average_calibrated_confidence: float = 0.0
    max_confidence: float = 0.0
    min_confidence: float = 0.0

    # Signal counts (Phase 2B.6)
    bullish_engines: int = 0
    bearish_engines: int = 0
    neutral_engines: int = 0

    # Conflict statistics (Phase 2B.8)
    conflict_count: int = 0
    agreement_ratio: float = 0.0

    # Scores (used in later phases)
    bullish_score: float = 0.0
    bearish_score: float = 0.0
    neutral_score: float = 0.0

    # Final decision (used later)
    consensus: str = "NEUTRAL"
    confidence: float = 0.0

    # Engine groups
    supporting_engines: List[str] = field(default_factory=list)
    opposing_engines: List[str] = field(default_factory=list)
    ignored_engines: List[str] = field(default_factory=list)

    # Engine contribution ranking (Phase 2B.12)
    engine_contributions: List[tuple] = field(default_factory=list)
    # Phase 2B.13 - Top contributors
    top_supporters: List[tuple] = field(default_factory=list)
    top_opponents: List[tuple] = field(default_factory=list)
    # Diagnostics
    conflicts: List[str] = field(default_factory=list)
    explanation: List[str] = field(default_factory=list)
