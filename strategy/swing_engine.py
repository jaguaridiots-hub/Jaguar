"""
Jaguar Quant X Enterprise
Institutional Swing Engine
Phase 1
"""


class SwingEngine:
    """
    Institutional Swing Detection Engine

    Responsibilities:
    - Detect Swing Highs
    - Detect Swing Lows
    - Classify HH / HL / LH / LL
    - Detect Trend
    - Calculate Strength
    - Calculate Confidence

    NOTE:
    This engine DOES NOT generate
    BOS, CHoCH, MSS or trading signals.
    """
    @staticmethod
    def _find_pivot_highs(candles, left=5, right=5):
        pivots = []

        for i in range(left, len(candles) - right):

            current = candles[i]["high"]

            if all(current > candles[j]["high"] for j in range(i-left, i)) and \
               all(current > candles[j]["high"] for j in range(i+1, i+right+1)):

                pivots.append({
                    "index": i,
                    "price": current,
                    "time": candles[i]["time"],
                })

        return pivots

    @staticmethod
    def _find_pivot_lows(candles, left=5, right=5):
        pivots = []

        for i in range(left, len(candles) - right):

            current = candles[i]["low"]

            if all(current < candles[j]["low"] for j in range(i-left, i)) and \
               all(current < candles[j]["low"] for j in range(i+1, i+right+1)):

                pivots.append({
                    "index": i,
                    "price": current,
                    "time": candles[i]["time"],
                })

        return pivots

    @staticmethod
    def classify_swings(pivots):
        """
        Clean pivot sequence and classify market structure.

        Ensures:
        HIGH → LOW → HIGH → LOW ...

        Consecutive HIGHs:
            keep only the higher one.

        Consecutive LOWs:
            keep only the lower one.
        """

        if not pivots:
            return []

        pivots = sorted(pivots, key=lambda x: x["index"])

        cleaned = [dict(pivots[0])]

        for pivot in pivots[1:]:

            last = cleaned[-1]

            # Same pivot type
            if pivot["type"] == last["type"]:

                # HIGH → keep higher high
                if pivot["type"] == "HIGH":
                    if pivot["price"] > last["price"]:
                        cleaned[-1] = dict(pivot)

                # LOW → keep lower low
                else:
                    if pivot["price"] < last["price"]:
                        cleaned[-1] = dict(pivot)

            else:
                cleaned.append(dict(pivot))

        swings = []

        previous_high = None
        previous_low = None

        for pivot in cleaned:

            if pivot["type"] == "HIGH":

                if previous_high is None:
                    label = "HH"
                elif pivot["price"] > previous_high:
                    label = "HH"
                else:
                    label = "LH"

                previous_high = pivot["price"]

            else:

                if previous_low is None:
                    label = "HL"
                elif pivot["price"] > previous_low:
                    label = "HL"
                else:
                    label = "LL"

                previous_low = pivot["price"]

            swings.append({
                **pivot,
                "label": label
            })

        return swings

    @staticmethod
    def detect_trend(swings):

        highs = [s for s in swings if s["type"] == "HIGH"]
        lows = [s for s in swings if s["type"] == "LOW"]

        if len(highs) < 2 or len(lows) < 2:
            return "UNKNOWN"

        if highs[-1]["label"] == "HH" and lows[-1]["label"] == "HL":
            return "UPTREND"

        if highs[-1]["label"] == "LH" and lows[-1]["label"] == "LL":
            return "DOWNTREND"

        return "RANGE"

    @staticmethod
    def analyze(candles):
        """
        Main analysis entry point.
        """

        highs = SwingEngine._find_pivot_highs(candles)
        lows = SwingEngine._find_pivot_lows(candles)

        pivots = []

        for h in highs:
            h["type"] = "HIGH"
            pivots.append(h)

        for l in lows:
            l["type"] = "LOW"
            pivots.append(l)

        pivots.sort(key=lambda x: x["index"])

        swings = SwingEngine.classify_swings(pivots)
        print("\n========== SWING DEBUG ==========")
        print("Raw Highs   :", len(highs))
        print("Raw Lows    :", len(lows))
        print("Raw Pivots  :", len(pivots))
        print("Clean Swings:", len(swings))

        print("\nLast 10 Swings")
        for s in swings[-10:]:
            print(
                s["type"],
                s["label"],
                round(s["price"], 2),
                s["index"]
            )

        previous_swing_high = None
        previous_swing_low = None

        for i in range(len(swings) - 1, -1, -1):

            if (
                swings[i]["type"] == "LOW"
                and i > 0
                and swings[i - 1]["type"] == "HIGH"
            ):
                previous_swing_high = swings[i - 1]
                previous_swing_low = swings[i]
                break

            if (
                swings[i]["type"] == "HIGH"
                and i > 0
                and swings[i - 1]["type"] == "LOW"
            ):
                previous_swing_low = swings[i - 1]
                previous_swing_high = swings[i]
                break

        trend = SwingEngine.detect_trend(swings)

        return {
            "trend": trend,

            "pivots": pivots,
            "swings": swings,

            "swing_high": highs[-1] if highs else None,
            "swing_low": lows[-1] if lows else None,

            "previous_swing_high": previous_swing_high,
            "previous_swing_low": previous_swing_low,

            "strength": 0,
            "confidence": 0,
            "reasons": [],
        }
