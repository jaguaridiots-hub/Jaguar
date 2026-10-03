from core.engine_result import EngineResult


def analyze(state):

    score = 0
    reasons = []

    signal = "NEUTRAL"

    ema20 = state.ema20
    ema50 = state.ema50
    ema100 = state.ema100
    ema200 = state.ema200

    rsi = state.rsi

    # EMA Trend
    ema_ready = all(
        value is not None
        for value in (ema20, ema50, ema100, ema200)
    )

    if ema_ready:
        if ema20 > ema50 > ema100 > ema200:
            score += 4
            signal = "BULLISH"
            reasons.append("EMA Bullish")
        elif ema20 < ema50 < ema100 < ema200:
            score -= 4
            signal = "BEARISH"
            reasons.append("EMA Bearish")
    else:
        reasons.append("EMA Trend Unavailable")

    # RSI
    if rsi <= 30:
        score += 2
        reasons.append("RSI Oversold")

    elif rsi >= 70:
        score -= 2
        reasons.append("RSI Overbought")

    # Volume
    if state.volume > 0:
        score += 1
    else:
        score -= 1
        reasons.append("Low Volume")

    confidence = min(1.0, abs(score) / 10)

    return EngineResult(
        name="AI Brain",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.20,
        reasons=reasons,
        metadata={
            "EMA20": ema20,
            "EMA50": ema50,
            "EMA100": ema100,
            "EMA200": ema200,
            "RSI": rsi,
        },
    ).to_dict()
