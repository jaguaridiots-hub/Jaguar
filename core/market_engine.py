from core.engine import Engine
from core.trading_kernel import TradingKernel


class MarketEngine(Engine):

    name = "Market Engine"

    def run(self, state, bus):

        bus.publish("MARKET_LOADING")

        kernel = TradingKernel(state.symbol)

        state.market = kernel.load(state.interval)

        bus.publish("MARKET_READY")

        return state
