from core.engine import Engine
from strategy.gann_engine import GannEngine


class GannEngineRunner(Engine):

    name = "Gann Engine"

    def run(self, state, bus):

        engine = GannEngine()

        return engine.run(state, bus)
