from core.engine import Engine
from core.trading_kernel import TradingKernel


class MarketEngine(Engine):

    name = "Market Engine"

    TIMEFRAMES = [
        "15m",
        "1h",
        "4h",
        "1d",
    ]

    def run(self, state, bus):

        bus.publish("MARKET_LOADING")

        kernel = TradingKernel(state.symbol)

        markets = {}

        for tf in self.TIMEFRAMES:

            data = kernel.load(tf)

            print(f"\n===== {tf} =====")
            print(type(data))
            print(data.keys() if isinstance(data, dict) else "NOT DICT")

            markets[tf] = data

        state.market = markets

        state.market_current = markets.get(state.interval)

        state.timeframes = {}

        for tf, data in markets.items():

            if not isinstance(data, dict):
                continue

            candles = data.get("candles", [])

            state.timeframes[tf] = {
                "symbol": data.get("symbol"),
                "interval": data.get("interval"),
                "candles": candles,
            }

            print(f"{tf}: {len(candles)} candles")

        print("Loaded Timeframes:", list(state.timeframes.keys()))

        bus.publish("MARKET_READY")

        return state
