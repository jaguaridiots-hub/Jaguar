from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Any

from scanner.models import ScannerCandidate, ScannerEvidence


_REQUIRED = (
    "open",
    "high",
    "low",
    "close",
    "volume",
)

_DIRECTIONAL_MAX = 70
_CANDIDATE_THRESHOLD = 18


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)

    if not math.isfinite(result):
        return float(default)

    return result


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalize_candles(
    candles: Sequence[Mapping[str, Any]],
) -> list[dict[str, float | int]]:
    if not isinstance(candles, Sequence) or isinstance(candles, (str, bytes)):
        raise ValueError("candles must be a sequence")

    normalized: list[dict[str, float | int]] = []

    for index, candle in enumerate(candles):
        if not isinstance(candle, Mapping):
            raise ValueError(f"candle[{index}] must be a mapping")

        missing = [
            key for key in _REQUIRED
            if key not in candle
        ]

        if missing:
            raise ValueError(
                f"candle[{index}] missing required fields: {','.join(missing)}"
            )

        normalized.append(
            {
                "open": _number(candle["open"]),
                "high": _number(candle["high"]),
                "low": _number(candle["low"]),
                "close": _number(candle["close"]),
                "volume": _number(candle["volume"]),
                "timestamp": int(
                    _number(
                        candle.get("timestamp", 0),
                    )
                ),
                "close_time": int(
                    _number(
                        candle.get("close_time", 0),
                    )
                ),
            }
        )

    return normalized


def _ema(values: Sequence[float], period: int) -> float | None:
    if len(values) < period:
        return None

    result = sum(values[:period]) / period
    multiplier = 2.0 / (period + 1.0)

    for value in values[period:]:
        result = value * multiplier + result * (1.0 - multiplier)

    return result


def _rsi(values: Sequence[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None

    gains: list[float] = []
    losses: list[float] = []

    for previous, current in zip(values[:-1], values[1:]):
        change = current - previous
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period

    if avg_loss == 0.0:
        return 100.0

    relative_strength = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _atr(candles: Sequence[Mapping[str, float | int]], period: int = 14) -> float | None:
    if len(candles) <= period:
        return None

    ranges: list[float] = []

    for index in range(1, len(candles)):
        current = candles[index]
        previous = candles[index - 1]

        high = float(current["high"])
        low = float(current["low"])
        previous_close = float(previous["close"])

        ranges.append(
            max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
        )

    return sum(ranges[-period:]) / period


def _vwap(
    candles: Sequence[Mapping[str, float | int]],
    period: int = 60,
) -> float | None:
    window = candles[-period:]

    total_price_volume = 0.0
    total_volume = 0.0

    for candle in window:
        typical = (
            float(candle["high"])
            + float(candle["low"])
            + float(candle["close"])
        ) / 3.0

        volume = max(float(candle["volume"]), 0.0)
        total_price_volume += typical * volume
        total_volume += volume

    if total_volume <= 0.0:
        return None

    return total_price_volume / total_volume


def _volume_ratio(
    candles: Sequence[Mapping[str, float | int]],
    period: int = 20,
) -> float | None:
    if len(candles) <= period:
        return None

    baseline = [
        max(float(candle["volume"]), 0.0)
        for candle in candles[-period - 1:-1]
    ]

    current = max(float(candles[-1]["volume"]), 0.0)
    average = sum(baseline) / len(baseline)

    if average <= 0.0:
        return None

    return current / average


def _pivot_indices(
    values: Sequence[float],
    side: str,
    radius: int = 2,
) -> list[int]:
    pivots: list[int] = []

    start = radius
    end = len(values) - radius

    for index in range(start, end):
        current = values[index]

        if side == "high":
            left = values[index - radius:index]
            right = values[index + 1:index + radius + 1]

            if current > max(left) and current >= max(right):
                pivots.append(index)

        else:
            left = values[index - radius:index]
            right = values[index + 1:index + radius + 1]

            if current < min(left) and current <= min(right):
                pivots.append(index)

    return pivots


def _structure(
    candles: Sequence[Mapping[str, float | int]],
) -> dict[str, Any]:
    highs = [float(item["high"]) for item in candles]
    lows = [float(item["low"]) for item in candles]
    close = float(candles[-1]["close"])

    high_pivots = _pivot_indices(highs, "high")
    low_pivots = _pivot_indices(lows, "low")

    structure_trend = "NEUTRAL"

    if len(high_pivots) >= 2 and len(low_pivots) >= 2:
        previous_high = highs[high_pivots[-2]]
        latest_high = highs[high_pivots[-1]]
        previous_low = lows[low_pivots[-2]]
        latest_low = lows[low_pivots[-1]]

        if latest_high > previous_high and latest_low > previous_low:
            structure_trend = "BULLISH"
        elif latest_high < previous_high and latest_low < previous_low:
            structure_trend = "BEARISH"

    latest_swing_high = (
        highs[high_pivots[-1]]
        if high_pivots
        else None
    )

    latest_swing_low = (
        lows[low_pivots[-1]]
        if low_pivots
        else None
    )

    bos = "NEUTRAL"
    choch = "NEUTRAL"

    if latest_swing_high is not None and close > latest_swing_high:
        bos = "BULLISH_BOS"
    elif latest_swing_low is not None and close < latest_swing_low:
        bos = "BEARISH_BOS"

    if bos == "BULLISH_BOS" and structure_trend == "BEARISH":
        choch = "BULLISH_CHOCH"
    elif bos == "BEARISH_BOS" and structure_trend == "BULLISH":
        choch = "BEARISH_CHOCH"

    return {
        "trend": structure_trend,
        "bos": bos,
        "choch": choch,
        "swing_high_count": len(high_pivots),
        "swing_low_count": len(low_pivots),
        "latest_swing_high": latest_swing_high,
        "latest_swing_low": latest_swing_low,
    }


def _fvg_signal(
    candles: Sequence[Mapping[str, float | int]],
) -> str:
    start = max(2, len(candles) - 20)

    signal = "NEUTRAL"

    for index in range(start, len(candles)):
        first = candles[index - 2]
        current = candles[index]

        if float(current["low"]) > float(first["high"]):
            signal = "BULLISH_FVG"

        elif float(current["high"]) < float(first["low"]):
            signal = "BEARISH_FVG"

    return signal


def _liquidity_signal(
    candles: Sequence[Mapping[str, float | int]],
    structure: Mapping[str, Any],
) -> str:
    latest = candles[-1]

    swing_high = structure.get("latest_swing_high")
    swing_low = structure.get("latest_swing_low")

    latest_high = float(latest["high"])
    latest_low = float(latest["low"])
    latest_close = float(latest["close"])

    if swing_high is not None:
        level = float(swing_high)

        if latest_high > level and latest_close < level:
            return "BEARISH_LIQUIDITY_SWEEP"

    if swing_low is not None:
        level = float(swing_low)

        if latest_low < level and latest_close > level:
            return "BULLISH_LIQUIDITY_SWEEP"

    return "NEUTRAL"


def _fibonacci_signal(
    candles: Sequence[Mapping[str, float | int]],
    trend: str,
) -> tuple[str, float]:
    window = candles[-50:]

    high = max(float(item["high"]) for item in window)
    low = min(float(item["low"]) for item in window)
    close = float(candles[-1]["close"])

    if high <= low:
        return "UNAVAILABLE", 0.5

    position = _clamp(
        (close - low) / (high - low),
        0.0,
        1.0,
    )

    if trend == "BULLISH":
        if position <= 0.5:
            return "DISCOUNT", position
        return "PREMIUM", position

    if trend == "BEARISH":
        if position >= 0.5:
            return "PREMIUM", position
        return "DISCOUNT", position

    return "MID_RANGE", position


def _interval_millis(interval: str) -> int:
    value = str(interval).strip().lower()

    try:
        if value.endswith("m"):
            return int(value[:-1]) * 60 * 1000
        if value.endswith("h"):
            return int(value[:-1]) * 60 * 60 * 1000
        if value.endswith("d"):
            return int(value[:-1]) * 24 * 60 * 60 * 1000
    except ValueError:
        pass

    return 15 * 60 * 1000


def _freshness(
    candles: Sequence[Mapping[str, float | int]],
    interval: str,
    now_ms: int,
) -> tuple[bool, int | None]:
    close_time = int(candles[-1].get("close_time", 0) or 0)

    if close_time <= 0:
        return False, None

    max_age = max(
        _interval_millis(interval) * 3,
        2 * 60 * 60 * 1000,
    )

    age = max(0, int(now_ms) - close_time)

    return age <= max_age, age


def _trend_signal(candles: Sequence[Mapping[str, float | int]]) -> str:
    closes = [
        float(item["close"])
        for item in candles
    ]

    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    ema200 = _ema(closes, 200)

    if ema20 is None or ema50 is None or ema200 is None:
        return "NEUTRAL"

    if ema20 > ema50 > ema200:
        return "BULLISH"

    if ema20 < ema50 < ema200:
        return "BEARISH"

    return "NEUTRAL"


def _momentum_signal(
    candles: Sequence[Mapping[str, float | int]],
) -> tuple[str, str]:
    closes = [
        float(item["close"])
        for item in candles
    ]

    rsi_value = _rsi(closes)

    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)

    if rsi_value is None or ema12 is None or ema26 is None:
        return "NEUTRAL", "Momentum data incomplete"

    macd = ema12 - ema26

    bullish = rsi_value >= 55.0 and macd > 0.0
    bearish = rsi_value <= 45.0 and macd < 0.0

    if bullish:
        return "BULLISH", f"RSI={rsi_value:.1f} MACD={macd:.4f}"

    if bearish:
        return "BEARISH", f"RSI={rsi_value:.1f} MACD={macd:.4f}"

    return "NEUTRAL", f"RSI={rsi_value:.1f} MACD={macd:.4f}"


def _mtf_signal(
    trend_map: Mapping[str, str],
    primary_trend: str,
) -> tuple[str, str, int]:
    if not primary_trend:
        return "NEUTRAL", "Primary trend unavailable", 0

    higher = [
        value
        for key, value in trend_map.items()
        if key != "primary"
        and value in {"BULLISH", "BEARISH"}
    ]

    if not higher:
        return "NEUTRAL", "No higher-timeframe trend available", 0

    aligned = sum(1 for value in higher if value == primary_trend)
    opposed = sum(1 for value in higher if value != primary_trend)

    if aligned > opposed:
        score = round(12.0 * aligned / len(higher))
        return (
            primary_trend,
            f"{aligned}/{len(higher)} higher timeframes aligned",
            score,
        )

    if opposed > aligned:
        score = round(12.0 * opposed / len(higher))
        opposite = "BEARISH" if primary_trend == "BULLISH" else "BULLISH"
        return (
            opposite,
            f"{opposed}/{len(higher)} higher timeframes oppose primary trend",
            -score,
        )

    return "NEUTRAL", f"{aligned}/{len(higher)} higher timeframes aligned", 0


class ScannerEngine:
    """
    Deterministic market candidate discovery.

    The engine reads candle data and returns a candidate object.
    It never mutates Jaguar state and does not authorize market actions.
    """

    def scan(
        self,
        symbol: str,
        timeframe: str,
        candles_by_timeframe: Mapping[str, Sequence[Mapping[str, Any]]],
        now_ms: int | None = None,
    ) -> ScannerCandidate:
        normalized_symbol = str(symbol).strip().upper()
        normalized_timeframe = str(timeframe).strip()

        if not normalized_symbol:
            raise ValueError("symbol is required")

        if not normalized_timeframe:
            raise ValueError("timeframe is required")

        if normalized_timeframe not in candles_by_timeframe:
            raise ValueError(
                f"primary timeframe {normalized_timeframe!r} is unavailable"
            )

        now = int(now_ms or (time.time() * 1000))

        primary = _normalize_candles(
            candles_by_timeframe[normalized_timeframe]
        )

        closes = [
            float(item["close"])
            for item in primary
        ]

        structure = _structure(primary)
        primary_trend = _trend_signal(primary)

        ema20 = _ema(closes, 20)
        ema50 = _ema(closes, 50)
        ema200 = _ema(closes, 200)

        momentum, momentum_detail = _momentum_signal(primary)

        vwap = _vwap(primary)
        latest_close = float(primary[-1]["close"])

        volume_ratio = _volume_ratio(primary)

        atr_value = _atr(primary)
        atr_ratio = (
            atr_value / latest_close
            if atr_value is not None and latest_close > 0
            else None
        )

        fib_signal, fib_position = _fibonacci_signal(
            primary,
            primary_trend,
        )

        fvg_signal = _fvg_signal(primary)
        liquidity_signal = _liquidity_signal(
            primary,
            structure,
        )

        trend_map = {"primary": primary_trend}

        for interval, candles in candles_by_timeframe.items():
            if interval == normalized_timeframe:
                continue

            try:
                tf_candles = _normalize_candles(candles)
                trend_map[interval] = _trend_signal(tf_candles)
            except ValueError:
                trend_map[interval] = "NEUTRAL"

        evidence: list[ScannerEvidence] = []
        raw_score = 0

        if primary_trend == "BULLISH":
            score = 10
            raw_score += score
            evidence.append(
                ScannerEvidence(
                    "TREND_ALIGNMENT",
                    "BULLISH",
                    score,
                    "EMA20 > EMA50 > EMA200",
                    normalized_timeframe,
                )
            )
        elif primary_trend == "BEARISH":
            score = -10
            raw_score += score
            evidence.append(
                ScannerEvidence(
                    "TREND_ALIGNMENT",
                    "BEARISH",
                    score,
                    "EMA20 < EMA50 < EMA200",
                    normalized_timeframe,
                )
            )
        else:
            evidence.append(
                ScannerEvidence(
                    "TREND_ALIGNMENT",
                    "NEUTRAL",
                    0,
                    "EMA structure is not directionally aligned",
                    normalized_timeframe,
                )
            )

        structure_score = 0

        if structure["bos"] == "BULLISH_BOS":
            structure_score = 14
        elif structure["bos"] == "BEARISH_BOS":
            structure_score = -14
        elif structure["trend"] == "BULLISH":
            structure_score = 8
        elif structure["trend"] == "BEARISH":
            structure_score = -8

        raw_score += structure_score

        structure_signal = "NEUTRAL"
        if structure_score > 0:
            structure_signal = "BULLISH"
        elif structure_score < 0:
            structure_signal = "BEARISH"

        evidence.append(
            ScannerEvidence(
                "STRUCTURE",
                structure_signal,
                structure_score,
                (
                    f"trend={structure['trend']} "
                    f"bos={structure['bos']} "
                    f"choch={structure['choch']}"
                ),
                normalized_timeframe,
            )
        )

        momentum_score = 0
        if momentum == "BULLISH":
            momentum_score = 8
        elif momentum == "BEARISH":
            momentum_score = -8

        raw_score += momentum_score

        evidence.append(
            ScannerEvidence(
                "MOMENTUM",
                momentum,
                momentum_score,
                momentum_detail,
                normalized_timeframe,
            )
        )

        vwap_score = 0

        if vwap is not None:
            if latest_close > vwap:
                vwap_signal = "BULLISH"
            elif latest_close < vwap:
                vwap_signal = "BEARISH"
            else:
                vwap_signal = "NEUTRAL"

            if vwap_signal == primary_trend and primary_trend in {
                "BULLISH",
                "BEARISH",
            }:
                vwap_score = 8 if primary_trend == "BULLISH" else -8

            evidence.append(
                ScannerEvidence(
                    "VWAP",
                    vwap_signal,
                    vwap_score,
                    f"close={latest_close:.6f} vwap={vwap:.6f}",
                    normalized_timeframe,
                )
            )
        else:
            evidence.append(
                ScannerEvidence(
                    "VWAP",
                    "UNAVAILABLE",
                    0,
                    "VWAP unavailable",
                    normalized_timeframe,
                )
            )

        raw_score += vwap_score

        volume_score = 0

        if volume_ratio is not None:
            candle_direction = (
                "BULLISH"
                if float(primary[-1]["close"]) > float(primary[-1]["open"])
                else "BEARISH"
            )

            if volume_ratio >= 1.20 and candle_direction == primary_trend:
                volume_score = 6 if primary_trend == "BULLISH" else -6
                volume_signal = candle_direction
            else:
                volume_signal = "NEUTRAL"

            evidence.append(
                ScannerEvidence(
                    "VOLUME",
                    volume_signal,
                    volume_score,
                    f"current_vs_20={volume_ratio:.2f}x",
                    normalized_timeframe,
                )
            )
        else:
            evidence.append(
                ScannerEvidence(
                    "VOLUME",
                    "UNAVAILABLE",
                    0,
                    "Volume baseline unavailable",
                    normalized_timeframe,
                )
            )

        raw_score += volume_score

        fib_score = 0

        if primary_trend == "BULLISH" and fib_signal == "DISCOUNT":
            fib_score = 6
        elif primary_trend == "BEARISH" and fib_signal == "PREMIUM":
            fib_score = -6

        evidence.append(
            ScannerEvidence(
                "FIBONACCI",
                fib_signal,
                fib_score,
                f"range_position={fib_position:.3f}",
                normalized_timeframe,
            )
        )

        raw_score += fib_score

        fvg_score = 0

        if fvg_signal == "BULLISH_FVG" and primary_trend == "BULLISH":
            fvg_score = 6
        elif fvg_signal == "BEARISH_FVG" and primary_trend == "BEARISH":
            fvg_score = -6

        evidence.append(
            ScannerEvidence(
                "FVG",
                fvg_signal,
                fvg_score,
                "latest detected fair-value-gap condition",
                normalized_timeframe,
            )
        )

        raw_score += fvg_score

        liquidity_score = 0

        if (
            liquidity_signal == "BULLISH_LIQUIDITY_SWEEP"
            and primary_trend == "BULLISH"
        ):
            liquidity_score = 6
        elif (
            liquidity_signal == "BEARISH_LIQUIDITY_SWEEP"
            and primary_trend == "BEARISH"
        ):
            liquidity_score = -6

        evidence.append(
            ScannerEvidence(
                "LIQUIDITY",
                liquidity_signal,
                liquidity_score,
                "recent swing liquidity interaction",
                normalized_timeframe,
            )
        )

        raw_score += liquidity_score

        mtf_signal, mtf_detail, mtf_score = _mtf_signal(
            trend_map,
            primary_trend,
        )

        evidence.append(
            ScannerEvidence(
                "MTF",
                mtf_signal,
                mtf_score,
                mtf_detail,
                normalized_timeframe,
            )
        )

        raw_score += mtf_score

        freshness_ok, freshness_age = _freshness(
            primary,
            normalized_timeframe,
            now,
        )

        quality = 100
        quality_reasons: list[str] = []

        if len(primary) < 220:
            quality -= 20
            quality_reasons.append("less_than_220_candles")

        if not freshness_ok:
            quality -= 20
            quality_reasons.append("stale_or_missing_close_time")

        if volume_ratio is None:
            quality -= 10
            quality_reasons.append("volume_baseline_unavailable")

        if atr_ratio is None:
            quality -= 10
            quality_reasons.append("atr_unavailable")

        if atr_ratio is not None:
            if atr_ratio < 0.001:
                quality -= 10
                quality_reasons.append("very_low_volatility")
            elif atr_ratio > 0.08:
                quality -= 10
                quality_reasons.append("extreme_volatility")

        quality = int(_clamp(quality, 0, 100))

        volatility_signal = "HEALTHY"

        if atr_ratio is None:
            volatility_signal = "UNAVAILABLE"
        elif atr_ratio < 0.001:
            volatility_signal = "LOW"
        elif atr_ratio > 0.08:
            volatility_signal = "EXTREME"

        evidence.append(
            ScannerEvidence(
                "VOLATILITY",
                volatility_signal,
                0,
                (
                    f"atr_ratio={atr_ratio:.5f}"
                    if atr_ratio is not None
                    else "ATR unavailable"
                ),
                normalized_timeframe,
            )
        )

        evidence.append(
            ScannerEvidence(
                "DATA_QUALITY",
                "HEALTHY" if quality >= 80 else "DEGRADED",
                0,
                (
                    f"quality={quality} "
                    f"freshness_age_ms={freshness_age}"
                ),
                normalized_timeframe,
            )
        )

        directional_score = int(
            _clamp(
                round(
                    50.0
                    + (
                        raw_score
                        / _DIRECTIONAL_MAX
                    ) * 50.0
                ),
                0,
                100,
            )
        )

        if abs(raw_score) >= _CANDIDATE_THRESHOLD:
            if raw_score > 0:
                direction = "LONG"
            else:
                direction = "SHORT"
        else:
            direction = "NEUTRAL"

        confidence = int(
            _clamp(
                round(
                    (
                        50.0
                        + (
                            abs(raw_score)
                            / _DIRECTIONAL_MAX
                        ) * 45.0
                    )
                    * (quality / 100.0)
                ),
                0,
                95,
            )
        )

        is_candidate = (
            direction in {"LONG", "SHORT"}
            and quality >= 70
            and len(primary) >= 220
        )

        return ScannerCandidate(
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            direction=direction,
            score=directional_score,
            confidence=confidence,
            is_candidate=is_candidate,
            structure=structure,
            data_quality={
                "quality": quality,
                "freshness_ok": freshness_ok,
                "freshness_age_ms": freshness_age,
                "candle_count": len(primary),
                "reasons": quality_reasons,
                "mtf": dict(trend_map),
                "ema20": ema20,
                "ema50": ema50,
                "ema200": ema200,
                "atr": atr_value,
                "atr_ratio": atr_ratio,
                "vwap": vwap,
                "volume_ratio": volume_ratio,
            },
            evidence=tuple(evidence),
        )
