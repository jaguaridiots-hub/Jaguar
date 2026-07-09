from core.engine import Engine
from strategy.regime_engine import RegimeEngine


class RegimeEngineRunner(Engine):

    name = "Regime"

    def run(self, state, bus):
        return RegimeEngine().run(state, bus)
