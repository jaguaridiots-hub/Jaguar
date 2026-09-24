from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from scanner.models import ScannerCandidate, ScannerEvidence


def _interval_ms(interval: str) -> int:
    value = str(interval).strip().lower()

    if value.endswith("m"):
        return int(value[:-1]) * 60 * 1000

    if value.endswith("h"):
        return int(value[:-1]) * 60 * 60 * 1000

    if value.endswith("d"):
        return int(value[:-1]) * 24 * 60 * 60 * 1000

    raise ValueError(f"unsupported interval: {interval}")


def _signal_direction(signal: str) -> int:
    value = str(signal or "").upper()

    if (
        "BULLISH" in value
        or "LONG" in value
    ):
        return 1

    if (
        "BEARISH" in value
        or "SHORT" in value
    ):
        return -1

    return 0


def _setup_name(
    evidence: tuple[ScannerEvidence, ...],
    direction: str,
) -> str:
    direction_sign = 1 if direction == "LONG" else -1

    signals = {
        item.name: _signal_direction(item.signal)
        for item in evidence
    }

    structure = (
        signals.get("STRUCTURE") == direction_sign
    )

    trend = (
        signals.get("TREND_ALIGNMENT") == direction_sign
    )

    mtf = (
        signals.get("MTF") == direction_sign
    )

    liquidity = (
        signals.get("LIQUIDITY") == direction_sign
    )

    fvg = (
        signals.get("FVG") == direction_sign
    )

    fibonacci = (
        signals.get("FIBONACCI") == direction_sign
    )

    if structure:
        return "STRUCTURE_BREAK"

    if liquidity and fvg:
        return "LIQUIDITY_SWEEP_REACTION"

    if fvg and fibonacci:
        return "FVG_VALUE_ALIGNMENT"

    if trend and mtf:
        return "TREND_CONTINUATION"

    return "MULTI_FACTOR_CONFLUENCE"


def _evidence_signature(
    candidate: ScannerCandidate,
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "name": item.name,
            "signal": item.signal,
            "score": int(item.score),
        }
        for item in candidate.evidence
    )


def _fingerprint(
    candidate: ScannerCandidate,
    setup: str,
) -> str:
    payload = {
        "symbol": candidate.symbol,
        "timeframe": candidate.timeframe,
        "direction": candidate.direction,
        "candidate": bool(candidate.is_candidate),
        "setup": setup,
        "evidence": _evidence_signature(candidate),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _lifecycle(
    candidate: ScannerCandidate,
) -> str:
    if not candidate.is_candidate:
        return "EXPIRED"

    quality = candidate.data_quality or {}
    freshness_ok = quality.get("freshness_ok")

    raw_age = quality.get("freshness_age_ms")
    try:
        age_ms = int(raw_age) if raw_age is not None else None
    except (TypeError, ValueError):
        age_ms = None

    try:
        interval = _interval_ms(candidate.timeframe)
    except (TypeError, ValueError):
        interval = 15 * 60 * 1000

    if freshness_ok is False:
        if age_ms is not None and age_ms > interval * 3:
            return "EXPIRED"
        return "STALE"

    if age_ms is None:
        return "ACTIVE"

    if age_ms <= interval // 2:
        return "NEW"

    return "ACTIVE"


def _priority(
    candidate: ScannerCandidate,
    conflict_count: int,
) -> str:
    quality = int(
        candidate.data_quality.get("quality", 0)
        or 0
    )

    confidence = int(candidate.confidence)

    if (
        confidence >= 90
        and quality >= 90
        and conflict_count == 0
    ):
        return "CRITICAL"

    if (
        confidence >= 80
        and quality >= 80
        and conflict_count <= 1
    ):
        return "HIGH"

    if confidence >= 65 and quality >= 60:
        return "MEDIUM"

    return "LOW"


@dataclass(frozen=True)
class ScannerAlert:
    alert_id: str
    fingerprint: str
    symbol: str
    timeframe: str
    direction: str
    setup: str
    priority: str
    state: str
    confidence: int
    candidate_score: int
    confluence_score: int
    evidence_balance: dict[str, int]
    conflict_count: int
    dominant_factors: tuple[str, ...]
    explanation: str
    authority: str = "SCANNER_ALERT_CONTEXT_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "fingerprint": self.fingerprint,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "setup": self.setup,
            "priority": self.priority,
            "state": self.state,
            "confidence": self.confidence,
            "candidate_score": self.candidate_score,
            "confluence_score": self.confluence_score,
            "evidence_balance": dict(self.evidence_balance),
            "conflict_count": self.conflict_count,
            "dominant_factors": list(self.dominant_factors),
            "explanation": self.explanation,
            "authority": self.authority,
        }


class ScannerIntelligence:
    """
    Pure scanner-context enrichment.

    Converts an existing ScannerCandidate into a deterministic,
    explainable ScannerAlert. It does not mutate the candidate,
    persist state, place orders, or invoke trading authorities.
    """

    def enrich(
        self,
        candidate: ScannerCandidate,
    ) -> ScannerAlert:
        if not isinstance(candidate, ScannerCandidate):
            raise TypeError("candidate must be ScannerCandidate")

        direction = str(candidate.direction).upper()

        if direction not in {"LONG", "SHORT"}:
            raise ValueError(
                "scanner intelligence requires LONG or SHORT candidate"
            )

        evidence = tuple(candidate.evidence)
        direction_sign = 1 if direction == "LONG" else -1

        bullish_weight = 0
        bearish_weight = 0
        aligned_weight = 0
        conflict_count = 0

        aligned: list[ScannerEvidence] = []

        for item in evidence:
            score = int(item.score)
            signal_sign = _signal_direction(item.signal)

            if score > 0:
                bullish_weight += abs(score)
            elif score < 0:
                bearish_weight += abs(score)

            if signal_sign == direction_sign:
                aligned.append(item)
                aligned_weight += abs(score)

            elif signal_sign == -direction_sign:
                conflict_count += 1

        aligned.sort(
            key=lambda item: (
                abs(int(item.score)),
                item.name,
            ),
            reverse=True,
        )

        dominant_factors = tuple(
            item.name
            for item in aligned[:3]
            if int(item.score) != 0
        )

        setup = _setup_name(evidence, direction)
        fingerprint = _fingerprint(candidate, setup)

        state = _lifecycle(candidate)
        priority = _priority(candidate, conflict_count)

        quality = int(
            candidate.data_quality.get("quality", 0)
            or 0
        )

        if dominant_factors:
            factor_text = ", ".join(dominant_factors)
        else:
            factor_text = "no non-zero directional factors"

        explanation = (
            f"{direction} scanner candidate classified as {setup}; "
            f"dominant factors: {factor_text}; "
            f"aligned evidence weight={aligned_weight}; "
            f"conflicts={conflict_count}; "
            f"quality={quality}/100; "
            f"state={state}."
        )

        alert_id = f"SCN-{fingerprint[:16].upper()}"

        return ScannerAlert(
            alert_id=alert_id,
            fingerprint=fingerprint,
            symbol=candidate.symbol,
            timeframe=candidate.timeframe,
            direction=direction,
            setup=setup,
            priority=priority,
            state=state,
            confidence=int(candidate.confidence),
            candidate_score=int(candidate.score),
            confluence_score=int(aligned_weight),
            evidence_balance={
                "bullish": int(bullish_weight),
                "bearish": int(bearish_weight),
            },
            conflict_count=int(conflict_count),
            dominant_factors=dominant_factors,
            explanation=explanation,
        )
