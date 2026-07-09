from core.engine import Engine
from strategy.fvg_engine import FVGEngine


class FVGEngineRunner(Engine):

    name = "Fair Value Gap Engine"

    def run(self, state, bus):

        bus.publish("FVG_ANALYSIS")

        candles = state.market_current["candles"]

        state.fvg = FVGEngine.analyze(candles)

        bus.publish("FVG_READY")

        return state
