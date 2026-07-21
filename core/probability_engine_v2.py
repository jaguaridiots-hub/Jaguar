from core.engine import Engine
from strategy.probability_engine_v2 import ProbabilityEngineV2


class ProbabilityEngineV2Runner(Engine):

    name = "ProbabilityV2"

    def run(self, state, bus):

        bus.publish("PROBABILITY_V2_ANALYSIS")

        state = ProbabilityEngineV2.analyze(state)

        bus.publish("PROBABILITY_V2_READY")

        return state
