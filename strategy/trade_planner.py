class TradePlanner:

    @staticmethod
    def plan(price, decision, atr):

        signal = decision["signal"]

        atr_value = atr["value"]

        if signal == "BUY":

            entry = price
            stop = round(entry - atr_value, 2)
            target1 = round(entry + atr_value, 2)
            target2 = round(entry + atr_value * 2, 2)

        elif signal == "SELL":

            entry = price
            stop = round(entry + atr_value, 2)
            target1 = round(entry - atr_value, 2)
            target2 = round(entry - atr_value * 2, 2)

        else:

            return {
                "signal": "NO TRADE"
            }

        rr = round(abs(target2-entry)/abs(entry-stop),2)

        return {
            "signal": signal,
            "entry": round(entry,2),
            "stop_loss": stop,
            "target1": target1,
            "target2": target2,
            "risk_reward": f"1:{rr}"
        }
