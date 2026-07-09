from strategy.wyckoff_engine import WyckoffEngine


class WyckoffEngineRunner:

    def run(self, state, bus):

        bus.publish("WYCKOFF_ANALYSIS")

        candles = state.market["candles"]

        state.wyckoff = WyckoffEngine.analyze(candles)

        bus.publish("WYCKOFF_READY")

        return state
