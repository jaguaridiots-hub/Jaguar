from core.engine import Engine
from strategy.gann_engine import GannEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class GannEngineRunner(Engine):

    name = "Gann Engine"

    def run(self, state, bus):

        bus.publish("GANN_ANALYSIS")

        engine = GannEngine()
        state = engine.run(state, bus)   # Gann's run already assigns state.gann

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.gann.get("score", 0)
        nearest = state.gann.get("nearest_level", 0)
        raw_conf = abs(score) / 20.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Gann",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Nearest Level", f"Price near {nearest}", raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("GANN_READY")

        return state
