from core.engine_result import EngineResult


def analyze(state):

    reasons = []

    ema20 = state.ema20
    ema50 = state.ema50
    ema100 = state.ema100
    ema200 = state.ema200

    atr = state.atr
    price = state.price
    rsi = state.rsi

    score = 0
    signal = "NEUTRAL"

    # ======================================
    # MARKET REGIME
    # ======================================

    if ema20 > ema50 > ema100 > ema200:
        signal = "BULLISH"
        score += 3
        reasons.append("EMA Bull Trend")

    elif ema20 < ema50 < ema100 < ema200:
        signal = "BEARISH"
        score -= 3
        reasons.append("EMA Bear Trend")

    elif ema20 > ema50 and ema100 > ema200:
        signal = "BULLISH"
        score += 1
        reasons.append("Bull Transition")

    elif ema20 < ema50 and ema100 < ema200:
        signal = "BEARISH"
        score -= 1
        reasons.append("Bear Transition")

    else:
        signal = "SIDEWAYS"
        reasons.append("EMA Sideways")

    # ======================================
    # ATR VOLATILITY
    # ======================================

    atr_percent = (atr / price * 100) if price > 0 else 0

    if atr_percent >= 3:
        volatility = "HIGH"
        reasons.append("High Volatility")

    elif atr_percent >= 1:
        volatility = "NORMAL"

    else:
        volatility = "LOW"

    # ======================================
    # RSI
    # ======================================

    if rsi < 30:
        score += 1
        reasons.append("RSI Oversold")

    elif rsi > 70:
        score -= 1
        reasons.append("RSI Overbought")

    confidence = min(1.0, abs(score) / 8)

    return EngineResult(
        name="Market Regime",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.10,
        reasons=reasons,
        metadata={
            "volatility": volatility,
            "atr_percent": round(atr_percent, 2),
            "ema20": ema20,
            "ema50": ema50,
            "ema100": ema100,
            "ema200": ema200,
        },
    ).to_dict()
