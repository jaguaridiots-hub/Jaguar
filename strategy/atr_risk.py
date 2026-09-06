class ATRRisk:

    @staticmethod
    def calculate(candles, entry):

        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        closes = [c["close"] for c in candles]

        trs = []

        for i in range(1, len(candles)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            trs.append(tr)

        if len(trs) < 14:
            atr = sum(trs) / len(trs)
        else:
            atr = sum(trs[-14:]) / 14

        sl_buy = round(entry - atr * 2, 2)
        sl_sell = round(entry + atr * 2, 2)

        tp1_buy = round(entry + atr * 2, 2)
        tp2_buy = round(entry + atr * 4, 2)
        tp3_buy = round(entry + atr * 6, 2)

        tp1_sell = round(entry - atr * 2, 2)
        tp2_sell = round(entry - atr * 4, 2)
        tp3_sell = round(entry - atr * 6, 2)

        if atr < entry * 0.003:
            volatility = "LOW"
        elif atr < entry * 0.008:
            volatility = "MEDIUM"
        else:
            volatility = "HIGH"

        return {
            "atr": round(atr, 2),
            "volatility": volatility,
            "buy": {
                "sl": sl_buy,
                "tp1": tp1_buy,
                "tp2": tp2_buy,
                "tp3": tp3_buy
            },
            "sell": {
                "sl": sl_sell,
                "tp1": tp1_sell,
                "tp2": tp2_sell,
                "tp3": tp3_sell
            }
        }
