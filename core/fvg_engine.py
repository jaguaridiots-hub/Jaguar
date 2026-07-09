from strategy.fvg_engine import FVGEngine


class FVGEngineRunner:

    def run(self, state, bus):

        bus.publish("FVG_ANALYSIS")

        candles = state.market["candles"]

        state.fvg = FVGEngine.analyze(candles)

        bus.publish("FVG_READY")

        return state
