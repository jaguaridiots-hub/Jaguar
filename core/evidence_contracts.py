"""
Legacy compatibility layer – re‑exports the canonical EvidenceBlock.
All new code should import directly from core.evidence.
"""
from core.evidence import EvidenceBlock, SubEvidence, ADR002_SCHEMA

# Expose the same names for backward compatibility
__all__ = ["EvidenceBlock", "SubEvidence", "ADR002_SCHEMA"]
