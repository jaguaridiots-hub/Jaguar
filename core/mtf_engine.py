"""
MTF Engine Runner
"""
from core.engine import Engine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from strategy.mtf_engine import MTFEngine


class MTFEngineRunner(Engine):
    engine_name = "MTF"

    def run(self, state, bus):
        # Publish ANALYSIS event
        bus.publish("MTF_ANALYSIS")

        # Execute MTF analysis
        state = MTFEngine.analyze(state)

        mtf_data = state.mtf

        score = mtf_data.get("score", 0)
        bias = mtf_data.get("bias", "NEUTRAL")
        alignment = mtf_data.get("alignment", 0)

        # Institutional MTF confidence

        raw_conf = max(
            abs(score) / 100.0,
            alignment / 4.0,
        )

        raw_conf = min(raw_conf, 1.0)

        block = EvidenceBlock(
            engine=self.engine_name,
            signal=bias,
            confidence_raw=raw_conf,
            confidence_calibrated=raw_conf,
            sub_evidence=[
                SubEvidence(
                    "Bias",
                    bias,
                    raw_conf,
                ),
                SubEvidence(
                    "Alignment",
                    str(alignment),
                    raw_conf,
                ),
            ],
            lifecycle_state="DETECTED",
        )

        if not hasattr(state, "blackboard"):
            from core.market_blackboard import MarketBlackboard
            state.blackboard = MarketBlackboard()

        state.blackboard.publish(block)

        # Publish READY event
        bus.publish("MTF_READY")

        return state
