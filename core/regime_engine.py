from core.engine import Engine
from strategy.regime_engine import RegimeEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class RegimeEngineRunner(Engine):

    name = "Regime Engine"

    def run(self, state, bus):

        bus.publish("REGIME_ANALYSIS")

        # The RegimeEngine.run() already assigns state.regime directly,
        # so we just call it and then publish the EvidenceBlock.
        engine = RegimeEngine()
        state = engine.run(state, bus)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.regime.get("score", 0)
        regime_label = state.regime.get("regime", "UNKNOWN")
        raw_conf = abs(score) / 20.0 if score != 0 else 0.1
        sub_conf = min(raw_conf, 1.0)

        block = EvidenceBlock(
            engine="Regime",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=sub_conf,
            sub_evidence=[
                SubEvidence("Regime Type", regime_label, sub_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("REGIME_READY")

        return state
