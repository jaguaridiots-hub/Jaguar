from core.engine import Engine
from strategy.mss_engine import MSSEngine


class MSSEngineRunner(Engine):

    name = "MSS Engine"

    def run(self, state, bus):

        bus.publish("MSS_ANALYSIS")

        candles = state.market_current["candles"]

        state.mss = MSSEngine.analyze(candles)

        bus.publish("MSS_READY")

        return state
