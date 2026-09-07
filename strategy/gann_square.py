from math import sqrt


class GannSquare:

    @staticmethod
    def calculate(price):

        root = sqrt(price)

        levels = []

        # Generate Square of 9 levels around current price
        for step in range(-8, 9):

            level = round((root + step * 0.125) ** 2, 2)

            levels.append(level)

        levels = sorted(set(levels))

        nearest = min(levels, key=lambda x: abs(x - price))

        lower = [x for x in levels if x < price]
        higher = [x for x in levels if x > price]

        support = lower[-1] if lower else levels[0]
        resistance = higher[0] if higher else levels[-1]

        distance_support = round(price - support, 2)
        distance_resistance = round(resistance - price, 2)

        if distance_support < distance_resistance:
            bias = "BULLISH"
        elif distance_resistance < distance_support:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        return {

            "price": round(price, 2),

            "nearest": nearest,

            "support": support,

            "resistance": resistance,

            "distance_support": distance_support,

            "distance_resistance": distance_resistance,

            "bias": bias,

            "levels": levels

        }
