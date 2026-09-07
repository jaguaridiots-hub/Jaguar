from core.engine import Engine
from strategy.wyckoff_engine import WyckoffEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class WyckoffEngineRunner(Engine):

    name = "Wyckoff Engine"

    def run(self, state, bus):

        bus.publish("WYCKOFF_ANALYSIS")

        candles = state.market_current["candles"]

        state.wyckoff = WyckoffEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        signal_name = state.wyckoff.get("signal", "NONE")
        score = state.wyckoff.get("score", 0)
        raw_conf = abs(score) / 30.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Wyckoff",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Wyckoff Phase", signal_name, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("WYCKOFF_READY")

        return state
