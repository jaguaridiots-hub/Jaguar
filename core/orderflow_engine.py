from core.engine import Engine
from strategy.orderflow_engine import OrderFlowEngine


class OrderFlowEngineRunner(Engine):

    name = "OrderFlow"

    def run(self, state, bus):
        return OrderFlowEngine().run(state, bus)
