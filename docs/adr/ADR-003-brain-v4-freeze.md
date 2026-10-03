# ADR-003 – Brain V4 Freeze

**Status:** Accepted  
**Date:** 2026-08-01  

## Decision
Brain V4 (additive score aggregation) is feature‑frozen.

## Rationale
- Weight‑sensitivity analysis shows only marginal, non‑transformative improvements.
- Multiple independent audits confirm the model cannot discriminate winners from losers.
- Logistic validation proves near‑zero cross‑market generalisation.
- The architecture itself is the limiting factor, not the parameter values.

## Consequences
- Brain V4 remains as a stable baseline for regression testing and research comparisons.
- No further engineering effort will be spent on improving its scoring logic.
- All new intelligence development targets the Brain V5 institutional reasoning architecture.
- Every future audit will compare V4 and V5 on identical datasets.
