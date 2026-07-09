from core.engine import Engine
from strategy.risk_manager_engine import RiskManagerEngine


class RiskManagerEngineRunner(Engine):

    name = "Risk Manager"

    def run(self, state, bus):

        engine = RiskManagerEngine()

        return engine.run(state, bus)
