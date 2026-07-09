from strategy.equal_levels_engine import EqualLevelsEngine


class EqualLevelsEngineRunner:

    def run(self, state, bus):

        bus.publish("EQUAL_LEVELS_ANALYSIS")

        candles = state.market["candles"]

        state.equal_levels = EqualLevelsEngine.analyze(candles)

        bus.publish("EQUAL_LEVELS_READY")

        return state
