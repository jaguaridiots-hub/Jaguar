from core.engine import Engine
from strategy.orderflow_engine import OrderFlowEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class OrderFlowEngineRunner(Engine):

    name = "Order Flow Engine"

    def run(self, state, bus):

        bus.publish("ORDERFLOW_ANALYSIS")

        engine = OrderFlowEngine()
        state = engine.run(state, bus)   # the engine's run already assigns state.orderflow

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.orderflow.get("score", 0)
        delta = state.orderflow.get("delta", 0)
        sig = state.orderflow.get("signal", "NONE")
        raw_conf = abs(score) / 70.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Order Flow",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Delta", f"Delta={delta}", raw_conf),
                SubEvidence("Order Flow Signal", sig, raw_conf),
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("ORDERFLOW_READY")

        return state
