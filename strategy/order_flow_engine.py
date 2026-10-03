class OrderFlowEngine:

    def run(self, state, bus):

        bus.publish("ORDER_FLOW_ANALYSIS")

        candles = state.market_current["candles"]

        recent = candles[-20:]

        buy_pressure = 0
        sell_pressure = 0
        volume_buy = 0
        volume_sell = 0

        for c in recent:

            body = abs(c["close"] - c["open"])

            if c["close"] > c["open"]:
                buy_pressure += body
                volume_buy += c["volume"]

            elif c["close"] < c["open"]:
                sell_pressure += body
                volume_sell += c["volume"]

        score = 0
        signal = "NEUTRAL"
        reasons = []

        if buy_pressure > sell_pressure and volume_buy > volume_sell:
            signal = "BULLISH"
            score = 20
            reasons.append("Buyers dominate order flow")

        elif sell_pressure > buy_pressure and volume_sell > volume_buy:
            signal = "BEARISH"
            score = -20
            reasons.append("Sellers dominate order flow")

        else:
            reasons.append("Balanced order flow")

        state.order_flow = {
            "signal": signal,
            "score": score,
            "buy_pressure": round(buy_pressure, 2),
            "sell_pressure": round(sell_pressure, 2),
            "buy_volume": round(volume_buy, 2),
            "sell_volume": round(volume_sell, 2),
            "reasons": reasons,
        }

        bus.publish("ORDER_FLOW_READY")

        return state
