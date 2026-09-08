# core/timeframe_indicator_engine.py
from indicators.indicator_engine import (
    IndicatorEngine,
    update_market_state,
)


class TimeframeIndicatorEngineRunner:

    def run(self, state, bus):
        bus.publish("MTF_INDICATORS_ANALYSIS")

        state.mtf_indicators = {}

        # ---- Get timeframe list (handles both dict and list) ----
        timeframes = getattr(state, "timeframes", {}) or {}
        if isinstance(timeframes, dict):
            tf_list = list(timeframes.keys())
            # tf_data is the dict itself (each tf maps to its data)
            # but we'll read from state.market anyway for safety
            tf_data = {tf: state.market.get(tf, {}) for tf in tf_list}
        elif isinstance(timeframes, list):
            tf_list = timeframes
            tf_data = {tf: state.market.get(tf, {}) for tf in tf_list}
        else:
            tf_list = []
            tf_data = {}

        print("\n========== TIMEFRAME INDICATOR ENGINE ==========")
        print("Available Timeframes:", tf_list)

        if not tf_list:
            print("WARNING: state.timeframes is EMPTY")
            bus.publish("MTF_INDICATORS_READY")
            return state

        for tf in tf_list:
            print(f"\n----- {tf} -----")
            data = tf_data.get(tf)
            if not data:
                print(f"{tf}: no data")
                continue
            candles = data.get("candles", [])
            if not candles:
                print(f"{tf}: no candles")
                continue

            print("Candles:", len(candles))
            indicators = IndicatorEngine.calculate(candles)
            print("Indicator Keys:", list(indicators.keys()))
            state.mtf_indicators[tf] = indicators
            # Publish the current timeframe as the canonical
            # single-timeframe indicator snapshot.
            current_interval = getattr(state, "interval", None) or "15m"

            state.indicators = state.mtf_indicators.get(
                current_interval,
                {},
         )


        # Canonical scalar-state bridge for the active timeframe.
        # Reuse the normalized candles already loaded by MarketEngine.
        current_interval = getattr(state, "interval", None) or "15m"
        active_data = state.market.get(current_interval, {})
        active_candles = (
            active_data.get("candles", [])
            if isinstance(active_data, dict)
            else []
        )

        if active_candles:
            state = update_market_state(
                state,
                active_candles,
            )

        print("\nMTF Indicator Timeframes:", list(state.mtf_indicators.keys()))
        print("===============================================\n")

        bus.publish("MTF_INDICATORS_READY")
        return state
