from core.engine import Engine
from strategy.fvg_engine import FVGEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class FVGEngineRunner(Engine):

    name = "Fair Value Gap Engine"

    def run(self, state, bus):

        bus.publish("FVG_ANALYSIS")

        candles = state.market_current["candles"]

        state.fvg = FVGEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.fvg.get("score", 0)
        sig = state.fvg.get("signal", "NONE")
        raw_conf = abs(score) / 40.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="FVG",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("FVG Signal", sig, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("FVG_READY")

        return state
