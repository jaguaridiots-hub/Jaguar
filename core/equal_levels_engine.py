from core.engine import Engine
from strategy.equal_levels_engine import EqualLevelsEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class EqualLevelsEngineRunner(Engine):

    name = "Equal Levels Engine"

    def run(self, state, bus):

        bus.publish("EQUAL_LEVELS_ANALYSIS")

        candles = state.market_current["candles"]

        state.equal_levels = EqualLevelsEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.equal_levels.get("score", 0)
        sig = state.equal_levels.get("signal", "NONE")
        raw_conf = abs(score) / 15.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Equal Levels",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Equal Level Signal", sig, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("EQUAL_LEVELS_READY")

        return state
