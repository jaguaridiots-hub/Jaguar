class OrderBlock:

    @staticmethod
    def detect(candles):

        if len(candles) < 20:
            return {
                "type": "NONE",
                "price": None
            }

        last20 = candles[-20:]

        bullish = max(last20, key=lambda x: x["volume"])
        bearish = min(last20, key=lambda x: x["volume"])

        if bullish["close"] > bullish["open"]:
            return {
                "type": "BULLISH",
                "price": bullish["low"]
            }

        if bearish["close"] < bearish["open"]:
            return {
                "type": "BEARISH",
                "price": bearish["high"]
            }

        return {
            "type": "NONE",
            "price": None
        }
