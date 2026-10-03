from core.engine import Engine
from strategy.structure_engine import StructureEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class StructureEngineRunner(Engine):

    name = "Structure Engine"

    def run(self, state, bus):

        bus.publish("STRUCTURE_ANALYSIS")

        candles = state.market_current["candles"]

        state.structure = StructureEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        bos_signal = state.structure.get("bos", {}).get("signal", "NEUTRAL")
        choch_signal = state.structure.get("choch", {}).get("signal", "NEUTRAL")
        score = state.structure.get("score", 0)
        sub_list = [
            SubEvidence("BOS", bos_signal, 0.7),
            SubEvidence("CHOCH", choch_signal, 0.6),
        ]
        raw_conf = abs(score) / 80.0 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Structure",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=sub_list,
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("STRUCTURE_READY")

        return state
