from core.engine import Engine
from ai.probability_engine import ProbabilityEngine


class ProbabilityEngineRunner(Engine):

    name = "Probability Engine"

    def run(self, state, bus):

        bus.publish("PROBABILITY_ANALYSIS")

        state.probability = ProbabilityEngine.calculate(state)

        bus.publish("PROBABILITY_READY")

        return state
