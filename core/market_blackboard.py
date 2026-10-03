"""
MarketBlackboard – stores EvidenceBlocks produced by engines.
"""
from typing import List
from core.evidence import EvidenceBlock

class MarketBlackboard:
    def __init__(self):
        self.evidence_blocks: List[EvidenceBlock] = []

    def publish(self, block: EvidenceBlock):
        """Add an EvidenceBlock to the blackboard."""
        self.evidence_blocks.append(block)

    def clear(self):
        """Remove all evidence blocks."""
        self.evidence_blocks.clear()

    def get_all(self) -> List[EvidenceBlock]:
        """Return a copy of all evidence blocks."""
        return self.evidence_blocks.copy()
