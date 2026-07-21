from core.engine_result import EngineResult


def analyze(state):

    reasons = []

    ema20 = state.ema20
    ema50 = state.ema50
    ema100 = state.ema100
    ema200 = state.ema200

    print("\n========== REGIME ENGINE DEBUG ==========")
    print("EMA20 :", ema20)
    print("EMA50 :", ema50)
    print("EMA100:", ema100)
    print("EMA200:", ema200)
    print("Price :", state.price)
    print("ATR   :", state.atr)
    print("RSI   :", state.rsi)
    print("=========================================\n")

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
    # STRUCTURAL OVERRIDE
    # ======================================

    market = getattr(state, "market", {})

    bos = market.get("bos_result", {})
    choch = market.get("choch_result", {})

    bos_signal = bos.get("signal", "NEUTRAL")
    choch_signal = choch.get("signal", "NEUTRAL")

    if bos_signal == "BEARISH":
        signal = "BEARISH"
        score = min(score, -4)
        reasons.append("Confirmed Bearish BOS")

    elif bos_signal == "BULLISH":
        signal = "BULLISH"
        score = max(score, 4)
        reasons.append("Confirmed Bullish BOS")

    elif choch_signal == "BEARISH":
        signal = "BEARISH"
        score = min(score, -2)
        reasons.append("Bearish CHOCH")

    elif choch_signal == "BULLISH":
        signal = "BULLISH"
        score = max(score, 2)
        reasons.append("Bullish CHOCH")

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
