class OrderFlowEngine:

    def run(self, state, bus):

        bus.publish("ORDERFLOW_ANALYSIS")

        candles = state.market_current["candles"]

        last = candles[-1]

        buy_pressure = 0
        sell_pressure = 0

        # Candle Body
        if last["close"] > last["open"]:
            buy_pressure += 20
        else:
            sell_pressure += 20

        # Average Volume
        avg_volume = sum(c["volume"] for c in candles[-20:]) / 20

        if last["volume"] > avg_volume:
            if last["close"] > last["open"]:
                buy_pressure += 30
            else:
                sell_pressure += 30

        # Wick Analysis
        upper = last["high"] - max(last["open"], last["close"])
        lower = min(last["open"], last["close"]) - last["low"]

        if lower > upper:
            buy_pressure += 20
        elif upper > lower:
            sell_pressure += 20

        delta = buy_pressure - sell_pressure

        if delta > 25:
            signal = "BUY"
        elif delta < -25:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        state.orderflow = {
            "signal": signal,
            "buy_pressure": buy_pressure,
            "sell_pressure": sell_pressure,
            "delta": delta,
            "score": delta,
            "reasons": [
                f"Buy Pressure {buy_pressure}",
                f"Sell Pressure {sell_pressure}"
            ]
        }

        bus.publish("ORDERFLOW_READY")

        return state
