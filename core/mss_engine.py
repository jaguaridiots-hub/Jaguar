from core.engine import Engine
from strategy.mss_engine import MSSEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class MSSEngineRunner(Engine):

    name = "MSS Engine"

    def run(self, state, bus):

        bus.publish("MSS_ANALYSIS")

        candles = state.market_current["candles"]

        state.mss = MSSEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.mss.get("score", 0)
        sig = state.mss.get("signal", "NONE")
        raw_conf = abs(score) / 40.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="MSS",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("MSS Signal", sig, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("MSS_READY")

        return state
