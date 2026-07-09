from core.engine import Engine
from strategy.premium_discount_engine import PremiumDiscountEngine


class PremiumDiscountEngineRunner(Engine):

    name = "Premium Discount Engine"

    def run(self, state, bus):

        bus.publish("PREMIUM_DISCOUNT_ANALYSIS")

        candles = state.market_current["candles"]

        state.premium_discount = PremiumDiscountEngine.analyze(candles)

        bus.publish("PREMIUM_DISCOUNT_READY")

        return state
