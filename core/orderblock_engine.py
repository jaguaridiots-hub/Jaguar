from strategy.orderblock_engine import OrderBlockEngine


class OrderBlockEngineRunner:

    def run(self, state, bus):

        engine = OrderBlockEngine()

        return engine.run(state, bus)
