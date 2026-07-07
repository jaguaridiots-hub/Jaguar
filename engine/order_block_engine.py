from core.engine_result import EngineResult
from data.market_data import candles


def analyze(state):

    if len(candles) < 20:
        return EngineResult(
            name="Order Block",
            signal="NEUTRAL",
            score=0,
            confidence=0,
            weight=1.20,
            reasons=["Not enough candles"]
        ).to_dict()

    last = candles[-1]

    signal = "NEUTRAL"
    score = 0
    reasons = []

    for i in range(len(candles) - 6, len(candles) - 1):

        candle = candles[i]

        # Bullish Order Block
        if (
            candle["close"] < candle["open"]
            and candles[i + 1]["close"] > candle["high"]
        ):

            if last["close"] >= candle["low"]:

                signal = "BULLISH"
                score = 5
                reasons.append("Bullish Order Block")

                break

        # Bearish Order Block
        if (
            candle["close"] > candle["open"]
            and candles[i + 1]["close"] < candle["low"]
        ):

            if last["close"] <= candle["high"]:

                signal = "BEARISH"
                score = -5
                reasons.append("Bearish Order Block")

                break

    confidence = min(1.0, abs(score) / 6)

    return EngineResult(
        name="Order Block",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.20,
        reasons=reasons,
        metadata={
            "last_close": last["close"]
        }
    ).to_dict()
