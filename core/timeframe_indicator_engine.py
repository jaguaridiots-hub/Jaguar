from indicators.indicator_engine import IndicatorEngine


class TimeframeIndicatorEngineRunner:

    def run(self, state, bus):

        bus.publish("MTF_INDICATORS_ANALYSIS")

        state.mtf_indicators = {}

        timeframes = getattr(state, "timeframes", {}) or {}

        print("\n========== TIMEFRAME INDICATOR ENGINE ==========")
        print("Available Timeframes:", list(timeframes.keys()))

        if not timeframes:
            print("WARNING: state.timeframes is EMPTY")
            bus.publish("MTF_INDICATORS_READY")
            return state

        for tf, data in timeframes.items():

            print(f"\n----- {tf} -----")

            if not isinstance(data, dict):
                print("Invalid timeframe data")
                continue

            candles = data.get("candles", [])

            if not isinstance(candles, list):
                print(f"{tf}: candles is {type(candles).__name__}, expected list")
                continue

            print("Candles:", len(candles))

            if not candles:
                print("No candles found.")
                continue

            indicators = IndicatorEngine.calculate(candles)

            print("Indicator Keys:", list(indicators.keys()))

            state.mtf_indicators[tf] = indicators

        print("\nMTF Indicator Timeframes:", list(state.mtf_indicators.keys()))
        print("===============================================\n")

        bus.publish("MTF_INDICATORS_READY")

        return state
