class GannTime:

    CYCLES = [30, 45, 60, 90, 120, 144, 180, 270, 360]

    @staticmethod
    def calculate(candle_count):

        nearest = min(
            GannTime.CYCLES,
            key=lambda x: abs(x - candle_count)
        )

        if candle_count == nearest:
            signal = "MAJOR TURN"

        elif abs(candle_count - nearest) <= 3:
            signal = "WATCH"

        else:
            signal = "NORMAL"

        return {
            "current": candle_count,
            "nearest_cycle": nearest,
            "signal": signal
        }
