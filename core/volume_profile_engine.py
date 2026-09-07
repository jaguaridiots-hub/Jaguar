from core.engine import Engine
from strategy.volume_profile_engine import VolumeProfileEngine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class VolumeProfileEngineRunner(Engine):

    name = "Volume Profile Engine"

    def run(self, state, bus):

        bus.publish("VOLUME_PROFILE_ANALYSIS")

        candles = state.market_current["candles"]

        state.volume_profile = VolumeProfileEngine.analyze(candles)

        # ---- Brain V5 EvidenceBlock (backward compatible) ----
        score = state.volume_profile.get("score", 0)
        sig = state.volume_profile.get("signal", "NONE")
        raw_conf = abs(score) / 52.5 if score != 0 else 0.1
        block = EvidenceBlock(
            engine="Volume Profile",
            signal="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
            confidence_raw=min(raw_conf, 1.0),
            sub_evidence=[
                SubEvidence("Volume Signal", sig, raw_conf)
            ],
        )
        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("VOLUME_PROFILE_READY")

        return state
