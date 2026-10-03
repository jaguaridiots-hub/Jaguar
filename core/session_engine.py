from core.engine import Engine
from strategy.session_engine import SessionEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class SessionEngineRunner(Engine):

    name = "Session Engine"

    def run(self, state, bus):

        bus.publish("SESSION_ANALYSIS")

        # The SessionEngine.run() already assigns state.session directly,
        # so we just call it and then publish the EvidenceBlock.
        engine = SessionEngine()
        state = engine.run(state, bus)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.session.get("score", 0)
        session_name = state.session.get("session", "UNKNOWN")
        raw_conf = abs(score) / 25.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Session",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Session", session_name, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("SESSION_READY")

        return state
