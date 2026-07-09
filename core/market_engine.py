from core.engine import Engine
from core.trading_kernel import TradingKernel


class MarketEngine(Engine):

    name = "Market Engine"

    TIMEFRAMES = [
        "15m",
        "1h",
        "4h",
        "1d"
    ]

    def run(self, state, bus):

        bus.publish("MARKET_LOADING")

        kernel = TradingKernel(state.symbol)

        markets = {}

        for tf in self.TIMEFRAMES:
            markets[tf] = kernel.load(tf)

        state.market = markets

        # Backward compatibility
        state.market_current = markets[state.interval]

        bus.publish("MARKET_READY")

        return state
