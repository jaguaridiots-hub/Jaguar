class GannAngles:

    @staticmethod
    def calculate(price, support, resistance):

        up = price - support
        down = resistance - price

        if up < down:
            angle = "1x1 BULLISH"

        elif down < up:
            angle = "1x1 BEARISH"

        else:
            angle = "BALANCED"

        return {
            "angle": angle,
            "support": support,
            "resistance": resistance
        }
