from core.engine import Engine
from strategy.equal_levels_engine import EqualLevelsEngine


class EqualLevelsEngineRunner(Engine):

    name = "Equal Levels Engine"

    def run(self, state, bus):

        bus.publish("EQUAL_LEVELS_ANALYSIS")

        candles = state.market_current["candles"]

        state.equal_levels = EqualLevelsEngine.analyze(candles)

        bus.publish("EQUAL_LEVELS_READY")

        return state
