from core.engine import Engine
from ai.score_engine import ScoreEngine as ScoreCalculator


class ScoreEngine(Engine):

    name = "Score Engine"

    def run(self, state, bus):

        state.ai = ScoreCalculator.calculate(
            state.indicators
        )

        bus.publish("SCORE_READY")

        return state
