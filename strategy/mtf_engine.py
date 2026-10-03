# strategy/mtf_engine.py
"""
Jaguar Quant X Enterprise
Phase 6.2
Institutional Multi-Timeframe Engine
"""

from config.institutional_config import (
    MTF_THRESHOLDS,
    MTF_WEIGHTS,
    TIMEFRAME_WEIGHTS,
)


class MTFEngine:

    TIMEFRAMES = ["15m", "1h", "4h", "1d"]

    @staticmethod
    def score_to_signal(score):

        if score >= MTF_THRESHOLDS["strong_buy"]:
            return "STRONG BUY"

        elif score >= MTF_THRESHOLDS["buy"]:
            return "BUY"

        elif score <= MTF_THRESHOLDS["strong_sell"]:
            return "STRONG SELL"

        elif score <= MTF_THRESHOLDS["sell"]:
            return "SELL"

        return "WAIT"

    @staticmethod
    def score_ema(ema):

        trend = ema.get("trend", "SIDEWAYS")

        if trend == "STRONG BULLISH":
            return 25

        elif trend == "BULLISH":
            return 15

        elif trend == "SIDEWAYS":
            return 0

        elif trend == "BEARISH":
            return -15

        elif trend == "STRONG BEARISH":
            return -25

        return 0

    @staticmethod
    def score_rsi(rsi):

        value = rsi.get("value", 50)

        if value >= 70:
            return 15

        elif value >= 60:
            return 10

        elif value >= 55:
            return 5

        elif value <= 30:
            return -15

        elif value <= 40:
            return -10

        elif value <= 45:
            return -5

        return 0

    @staticmethod
    def score_vwap(price, vwap):
        value = vwap.get("value")
        if value is None:
            return 0
        if price > value:
            return MTF_WEIGHTS["vwap"]
        return -MTF_WEIGHTS["vwap"]

    @staticmethod
    def score_macd(macd):
        signal = macd.get("signal", "NEUTRAL")
        if signal == "BUY":
            return MTF_WEIGHTS["macd"]
        if signal == "SELL":
            return -MTF_WEIGHTS["macd"]
        return 0

    @staticmethod
    def score_supertrend(supertrend):
        signal = supertrend.get("signal", "NEUTRAL")
        if signal == "BULLISH":
            return MTF_WEIGHTS["supertrend"]
        if signal == "BEARISH":
            return -MTF_WEIGHTS["supertrend"]
        return 0

    @staticmethod
    def score_adx(adx):
        strength = adx.get("strength", "WEAK")
        trend = adx.get("trend", "SIDEWAYS")
        if strength == "STRONG":
            if trend == "BULLISH":
                return MTF_WEIGHTS["adx"]
            if trend == "BEARISH":
                return -MTF_WEIGHTS["adx"]
        return 0

    @staticmethod
    def score_volume(volume):
        signal = volume.get("signal", "LOW VOLUME")
        if signal == "HIGH VOLUME":
            return MTF_WEIGHTS["volume"]
        return 0

    @staticmethod
    def analyze(state):
        frames = {}
        buy = 0
        sell = 0
        wait = 0

        reasons = []
        market = getattr(state, "market", {}) or {}
        mtf_indicators = getattr(state, "mtf_indicators", {}) or {}
        for tf in MTFEngine.TIMEFRAMES:
            score = 0
            tf_data = market.get(tf, {})
            candles = tf_data.get("candles", [])
            if len(candles) >= 50:
                ind = mtf_indicators.get(tf, {})

                print(f"\nTIMEFRAME: {tf}")
                print("EMA :", ind.get("ema"))
                print("RSI :", ind.get("rsi"))
                print("VWAP:", ind.get("vwap"))

                ema = ind.get("ema", {})
                rsi = ind.get("rsi", {})
                vwap = ind.get("vwap", {})
                macd = ind.get("macd", {})
                supertrend = ind.get("supertrend", {})
                adx = ind.get("adx", {})
                volume = ind.get("volume", {})

                price = candles[-1]["close"]

                score += MTFEngine.score_ema(ema)
                score += MTFEngine.score_rsi(rsi)
                score += MTFEngine.score_vwap(price, vwap)
                score += MTFEngine.score_macd(macd)
                score += MTFEngine.score_supertrend(supertrend)
                score += MTFEngine.score_adx(adx)
                score += MTFEngine.score_volume(volume)

                score = max(-100, min(100, score))

            signal = MTFEngine.score_to_signal(score)

            frames[tf] = {
                "score": score,
                "signal": signal,
            }

            if signal in ("BUY", "STRONG BUY"):
                buy += 1
            elif signal in ("SELL", "STRONG SELL"):
                sell += 1
            else:
                wait += 1

        # Institutional Alignment
        alignment_score = 0
        for frame in frames.values():
            signal = frame["signal"]
            if signal == "STRONG BUY":
                alignment_score += 3
            elif signal == "BUY":
                alignment_score += 2
            elif signal == "WAIT":
                alignment_score += 0
            elif signal == "SELL":
                alignment_score -= 2
            elif signal == "STRONG SELL":
                alignment_score -= 3

        bullish_frames = sum(
            1 for f in frames.values()
            if f["signal"] in ("BUY", "STRONG BUY")
        )

        bearish_frames = sum(
            1 for f in frames.values()
            if f["signal"] in ("SELL", "STRONG SELL")
        )

        confluence = max(bullish_frames, bearish_frames) / len(frames)

        alignment = max(buy, sell)

        # ==========================================================
        # Institutional Weighted MTF Bias
        # ==========================================================
        weighted_score = 0.0
        total_weight = 0.0

        for tf in MTFEngine.TIMEFRAMES:
            if tf not in frames:
                continue

            weight = TIMEFRAME_WEIGHTS.get(tf, 0) / 100.0
            weighted_score += frames[tf]["score"] * weight
            total_weight += weight

        top_level_score = (
            weighted_score / total_weight
            if total_weight > 0 else 0
        )

        weighted_signal = MTFEngine.score_to_signal(top_level_score)

        if weighted_signal == "STRONG BUY":
            bias = "STRONG BULLISH"
        elif weighted_signal == "BUY":
            bias = "BULLISH"
        elif weighted_signal == "STRONG SELL":
            bias = "STRONG BEARISH"
        elif weighted_signal == "SELL":
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        state.mtf = {
            "engine": "MultiTimeframe",
            "frames": frames,
            "buy": buy,
            "sell": sell,
            "wait": wait,
            "alignment": alignment,
            "alignment_score": alignment_score,
            "bias": bias,
            "strength": abs(alignment_score),
            "confidence": abs(alignment_score) * 10,
            "signal": bias,
            "score": top_level_score,
            "reasons": reasons,
        }

        # ---- FIX: return the dictionary so the runner can store it ----
        return state
