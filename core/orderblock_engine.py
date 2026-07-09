from core.engine import Engine
from strategy.orderblock_engine import OrderBlockEngine


class OrderBlockEngineRunner(Engine):

    name = "Order Block Engine"

    def run(self, state, bus):

        engine = OrderBlockEngine()

        return engine.run(state, bus)
