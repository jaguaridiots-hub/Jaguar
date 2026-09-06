"""
DecisionResult
Institutional decision output.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class DecisionResult:
    # Final decision
    action: str = "WAIT"      # ENTER_LONG / ENTER_SHORT / WAIT / AVOID
    confidence: float = 0.0

    # Decision quality
    approved: bool = False

    # Diagnostics
    reasons: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)

    # Statistics
    agreement_ratio: float = 0.0
    conflict_count: int = 0

    # Evidence summary
    supporting_engines: List[str] = field(default_factory=list)
    opposing_engines: List[str] = field(default_factory=list)
