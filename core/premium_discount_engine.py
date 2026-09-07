from core.engine import Engine
from strategy.premium_discount_engine import PremiumDiscountEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class PremiumDiscountEngineRunner(Engine):

    name = "Premium Discount Engine"

    def run(self, state, bus):

        bus.publish("PREMIUM_DISCOUNT_ANALYSIS")

        candles = state.market_current["candles"]

        state.premium_discount = PremiumDiscountEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.premium_discount.get("score", 0)
        zone = state.premium_discount.get("zone", "NONE")
        raw_conf = abs(score) / 15.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Premium/Discount",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Zone", zone, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("PREMIUM_DISCOUNT_READY")

        return state
