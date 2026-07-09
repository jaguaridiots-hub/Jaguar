from core.engine import Engine
from strategy.probability_engine_v2 import ProbabilityEngineV2


class ProbabilityEngineV2Runner(Engine):

    name = "ProbabilityV2"

    def run(self, state, bus):

        return ProbabilityEngineV2().run(state, bus)

