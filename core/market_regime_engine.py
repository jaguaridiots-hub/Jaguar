from core.engine import Engine
from strategy.market_regime_engine import MarketRegimeEngine


class MarketRegimeEngineRunner(Engine):

    name = "Market Regime Engine"

    def run(self, state, bus):

        bus.publish("MARKET_REGIME_ANALYSIS")

        candles = state.market_current["candles"]

        state.market_regime = MarketRegimeEngine.analyze(candles)

        bus.publish("MARKET_REGIME_READY")

        return state
