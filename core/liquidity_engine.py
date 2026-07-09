from strategy.liquidity_engine import LiquidityEngine


class LiquidityEngineRunner:

    def run(self, state, bus):

        bus.publish("LIQUIDITY_ANALYSIS")

        candles = state.market["candles"]

        state.liquidity = LiquidityEngine.analyze(candles)

        bus.publish("LIQUIDITY_READY")

        return state
