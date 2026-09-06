class JaguarBrain:

    @staticmethod
    def decide(
        technical,
        smc,
        gann,
        mtf,
        grade,
        atr
    ):

        total = technical + smc + gann

        if (
            grade == "A+"
            and mtf["signal"] == "STRONG BUY"
            and atr["volatility"] != "LOW"
        ):
            return {
                "signal": "STRONG BUY",
                "probability": 95,
                "decision": "EXECUTE"
            }

        if (
            grade in ["A+", "A"]
            and mtf["signal"] == "BUY"
        ):
            return {
                "signal": "BUY",
                "probability": 85,
                "decision": "BUY"
            }

        if (
            grade == "B"
            or atr["volatility"] == "LOW"
        ):
            return {
                "signal": "WATCH",
                "probability": 60,
                "decision": "WAIT"
            }

        return {
            "signal": "NO TRADE",
            "probability": 20,
            "decision": "IGNORE"
        }
