class VolumeProfileEngine:

    @staticmethod
    def analyze(candles):

        if len(candles) < 20:
            return {
                "signal": "NONE",
                "score": 0,
                "poc": None,
                "vah": None,
                "val": None,
                "hvn": None,
                "lvn": None,
                "reasons": ["Not enough candles"]
            }

        price_volume = {}

        for c in candles:

            high = c["high"]
            low = c["low"]
            close = c["close"]
            volume = c["volume"]

            price = round(close, 2)

            if price not in price_volume:
                price_volume[price] = 0

            price_volume[price] += volume

        sorted_nodes = sorted(
            price_volume.items(),
            key=lambda x: x[1],
            reverse=True
        )

        poc = sorted_nodes[0][0]

        hvn = sorted_nodes[0][0]

        lvn = sorted_nodes[-1][0]

        prices = sorted(price_volume.keys())

        vah = prices[int(len(prices) * 0.7)]

        val = prices[int(len(prices) * 0.3)]

        last_price = candles[-1]["close"]

        score = 0

        reasons = []

        signal = "NEUTRAL"

        if last_price > poc:

            signal = "BULLISH"

            score += 20

            reasons.append("Price above POC")

        else:

            signal = "BEARISH"

            score -= 20

            reasons.append("Price below POC")

        if last_price > vah:

            score += 10

            reasons.append("Acceptance above Value Area")

        elif last_price < val:

            score -= 10

            reasons.append("Acceptance below Value Area")

        if abs(last_price - hvn) < abs(last_price - lvn):

            score += 5

            reasons.append("Strong HVN Support")

        else:

            score -= 5

            reasons.append("Near LVN")

        return {

            "signal": signal,

            "score": score,

            "poc": poc,

            "vah": vah,

            "val": val,

            "hvn": hvn,

            "lvn": lvn,

            "reasons": reasons

        }
