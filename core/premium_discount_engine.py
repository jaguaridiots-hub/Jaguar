from strategy.premium_discount_engine import PremiumDiscountEngine

class PremiumDiscountEngineRunner:

    def run(self, state, bus):

        bus.publish("PREMIUM_DISCOUNT_ANALYSIS")

        candles = state.market["candles"]

        state.premium_discount = PremiumDiscountEngine.analyze(candles)

        bus.publish("PREMIUM_DISCOUNT_READY")

        return state
