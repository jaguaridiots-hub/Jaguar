from strategy.mtf_engine import MTFEngine
from core.timeframe_loader import TimeframeLoader


class MTFEngineRunner:

    def run(self, state, bus):

        bus.publish("MTF_ANALYSIS")

        state.timeframes = TimeframeLoader.load(state)

        state.mtf = MTFEngine.analyze(state)

        bus.publish("MTF_READY")

        return state
