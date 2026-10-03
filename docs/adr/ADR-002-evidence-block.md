# ADR-002 – EvidenceBlock

**Status:** Accepted  
**Date:** 2026-08-01  

## Purpose
Define the canonical data format for structured engine outputs.

## Schema
- `engine` (str)
- `signal` (str, one of BULLISH/BEARISH/NEUTRAL)
- `confidence_raw` (float 0‑1)
- `confidence_calibrated` (float 0‑1) – initially equal to raw
- `sub_evidence` (list of dicts with type/signal/confidence)
- `lifecycle_state` (str)

## Backward Compatibility
Engines continue to write the legacy `score` dictionary to `state.<engine_name>`.
The new block is stored in `state.blackboard`.
