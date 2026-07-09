from strategy.mss_engine import MSSEngine


class MSSEngineRunner:

    def run(self, state, bus):

        bus.publish("MSS_ANALYSIS")

        candles = state.market["candles"]

        state.mss = MSSEngine.analyze(candles)

        bus.publish("MSS_READY")

        return state
