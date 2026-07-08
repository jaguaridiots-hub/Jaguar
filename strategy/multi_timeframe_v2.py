class MultiTimeframeV2:

    @staticmethod
    def analyze(tf):

        buy = 0
        sell = 0
        hold = 0

        for t in ["5m", "15m", "1h", "4h", "1d"]:

            signal = tf.get(t, {}).get("signal", "HOLD")

            if signal in ("BUY", "STRONG BUY"):
                buy += 1

            elif signal in ("SELL", "STRONG SELL"):
                sell += 1

            else:
                hold += 1

        total = buy + sell + hold

        confidence = round(max(buy, sell) / total * 100, 2)

        if buy > sell:
            trend = "BULLISH"

        elif sell > buy:
            trend = "BEARISH"

        else:
            trend = "SIDEWAYS"

        return {
            "trend": trend,
            "buy": buy,
            "sell": sell,
            "hold": hold,
            "confidence": confidence
        }
