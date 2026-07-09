class SMCEngine:

    def run(self, state, bus):

        bus.publish("SMC_ANALYSIS")

        candles = state.market_current["candles"]

        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        closes = [c["close"] for c in candles]

        lookback = 30

        swing_high = max(highs[-lookback:])
        swing_low = min(lows[-lookback:])

        last = closes[-1]
        prev = closes[-2]

        trend = "SIDEWAYS"

        bos = False
        choch = False
        liquidity = False

        equal_high = abs(swing_high - highs[-2]) < 0.001 * swing_high
        equal_low = abs(swing_low - lows[-2]) < 0.001 * swing_low

        if last > swing_high:
            trend = "BULLISH"
            bos = True

        elif last < swing_low:
            trend = "BEARISH"
            bos = True

        elif prev < closes[-5] and last > closes[-5]:
            choch = True

        if highs[-1] > swing_high and last < swing_high:
            liquidity = True

        state.smc = {
            "trend": trend,
            "bos": bos,
            "choch": choch,
            "liquidity_sweep": liquidity,
            "equal_high": equal_high,
            "equal_low": equal_low,
            "swing_high": swing_high,
            "swing_low": swing_low
        }

        bus.publish("SMC_READY")

        return state
