from core.engine import Engine
from strategy.wyckoff_engine import WyckoffEngine


class WyckoffEngineRunner(Engine):

    name = "Wyckoff Engine"

    def run(self, state, bus):

        bus.publish("WYCKOFF_ANALYSIS")

        candles = state.market_current["candles"]

        state.wyckoff = WyckoffEngine.analyze(candles)

        bus.publish("WYCKOFF_READY")

        return state
