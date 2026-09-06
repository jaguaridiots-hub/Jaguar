class MultiTimeframe:

    @staticmethod
    def analyze(timeframes):

        buy = 0
        sell = 0
        hold = 0

        reasons = []

        for tf, data in timeframes.items():

            signal = data.get("signal", "HOLD")

            if signal in ["BUY", "STRONG BUY"]:
                buy += 1
                reasons.append(f"{tf}: BUY")

            elif signal in ["SELL", "STRONG SELL"]:
                sell += 1
                reasons.append(f"{tf}: SELL")

            else:
                hold += 1
                reasons.append(f"{tf}: HOLD")

        total = len(timeframes)

        buy_percent = round((buy / total) * 100)
        sell_percent = round((sell / total) * 100)

        if buy >= 4:
            trend = "STRONG BULLISH"
            signal = "STRONG BUY"

        elif buy == 3:
            trend = "BULLISH"
            signal = "BUY"

        elif sell >= 4:
            trend = "STRONG BEARISH"
            signal = "STRONG SELL"

        elif sell == 3:
            trend = "BEARISH"
            signal = "SELL"

        else:
            trend = "SIDEWAYS"
            signal = "HOLD"

        confidence = max(buy_percent, sell_percent)

        return {
            "signal": signal,
            "trend": trend,
            "buy": buy,
            "sell": sell,
            "hold": hold,
            "buy_percent": buy_percent,
            "sell_percent": sell_percent,
            "confidence": confidence,
            "reasons": reasons
        }
