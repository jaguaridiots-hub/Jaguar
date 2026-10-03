from core.engine import Engine
from strategy.trade_planner_engine import TradePlannerEngine


class TradePlannerEngineRunner(Engine):

    name = "Trade Planner"

    def run(self, state, bus):

        engine = TradePlannerEngine()

        return engine.run(state, bus)
