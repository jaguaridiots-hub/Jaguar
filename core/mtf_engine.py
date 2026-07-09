from strategy.mtf_engine import MTFEngine


class MTFEngineRunner:

    def run(self, state, bus):

        bus.publish("MTF_ANALYSIS")

        state.mtf = MTFEngine.analyze(state)

        bus.publish("MTF_READY")

        return state
