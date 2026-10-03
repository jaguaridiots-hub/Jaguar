from core.engine import Engine
from strategy.order_flow_engine import OrderFlowEngine


class OrderFlowEngineRunner(Engine):

    name = "Order Flow Engine"

    def run(self, state, bus):

        engine = OrderFlowEngine()

        return engine.run(state, bus)
