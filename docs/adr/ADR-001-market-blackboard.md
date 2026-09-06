# ADR-001 – MarketBlackboard

**Status:** Accepted  
**Date:** 2026-08-01  

## Purpose
Provide a shared evidence store that all engines read from and write to during a single analysis cycle.

## Responsibilities
- Accept `EvidenceBlock` objects from any engine.
- Expose all collected blocks to readers (Fusion Engine, Meta‑Reasoning).
- Maintain an immutable lifecycle log.

## Design Decisions
- Implemented as a plain Python dictionary attached to the state for simplicity.
- No thread safety needed in the current single‑threaded pipeline.
- Resets at the start of each `JaguarOrchestrator.analyze()` call.

## Known Limitations
- Not distributed – only lives for one analysis cycle.
- Future: may add TTL for evidence staleness.
