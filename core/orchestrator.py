from core.state import JaguarState
from core.event_bus import EventBus
from core.logger import logger
from core.engine_registry import EngineRegistry
from core.filter_attribution import reset_attribution


class JaguarOrchestrator:

    def __init__(self):
        self.state = JaguarState()
        self.bus = EventBus()
        self.registry = EngineRegistry()

        from core.register_engines import register
        register(self.registry)

        print("\n========== REGISTERED ENGINES ==========")
        for i, engine in enumerate(self.registry.engines, 1):
            print(f"{i:02d}. {engine.__class__.__name__}")
        print("========================================\n")

    def publish(self, event, payload=None):
        logger.info(event)
        self.bus.publish(event, payload)

    def analyze(
        self,
        symbol="BTCUSDT",
        interval="15m",
        mode="SWING",
        debug_brain=False
    ):
        # ---- Reset attribution at start of each pipeline ----
        reset_attribution()

        self.state.symbol = symbol
        self.state.interval = interval
        self.state.mode = mode
        self.state.debug_brain = debug_brain

        print("\n" + "=" * 70)
        print(f"JAGUAR QUANT X ENTERPRISE | MODE: {mode}")
        print("=" * 70)

        self.publish("SYSTEM_START")

        self.registry.run(self.state, self.bus)

        from core.evidence_fusion import EvidenceFusionEngine
        from core.decision_engine import DecisionEngine

        # Phase 2B
        self.state.fusion = EvidenceFusionEngine().fuse(
            self.state.blackboard
        )

        # Phase 3
        self.state.decision = DecisionEngine().evaluate(
            self.state.fusion
        )

        self.state.master_decision = {
            "decision": self.state.decision.action,
            "confidence": self.state.decision.confidence,
            "approved": self.state.decision.approved,
            "reasons": self.state.decision.reasons,
            "reasoning": self.state.fusion.explanation,
            "score": round(self.state.fusion.confidence * 100),
            "components": {},
        }
        self.state.dashboard = {
            # Market
            "symbol": self.state.symbol,
            "timeframe": self.state.interval,
            "price": getattr(self.state, "price", 0),
            "session": getattr(self.state, "session", "UNKNOWN"),
            "market_regime": getattr(self.state, "market_regime", {}),

            # Decision
            "decision": self.state.decision.action,
            "decision_score": round(self.state.fusion.confidence * 100),
            "decision_confidence": round(self.state.decision.confidence * 100, 2),
            "trade_approved": self.state.decision.approved,
            "decision_reasons": self.state.decision.reasons,

            # Fusion diagnostics
            "fusion_consensus": self.state.fusion.consensus,
            "supporting_engines": self.state.fusion.supporting_engines,
            "opposing_engines": self.state.fusion.opposing_engines,

            # Engine outputs
            "smc": getattr(self.state, "smc", {}),
            "structure": getattr(self.state, "structure", {}),
            "liquidity": getattr(self.state, "liquidity", {}),
            "fvg": getattr(self.state, "fvg", {}),
            "orderflow": getattr(self.state, "orderflow", {}),
            "volume_profile": getattr(self.state, "volume_profile", {}),
            "gann": getattr(self.state, "gann", {}),
            "premium_discount": getattr(self.state, "premium_discount", {}),
            "wyckoff": getattr(self.state, "wyckoff", {}),
            "equal_levels": getattr(self.state, "equal_levels", {}),
            "mtf": getattr(self.state, "mtf", {}),
        }

        self.publish("SYSTEM_FINISHED")

        print("\n" + "=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)

        if hasattr(self.state, "engine_status"):
            for name, status in self.state.engine_status.items():
                t = self.state.engine_time.get(name, 0)
                print(f"{name:<40} {status:<10} {t:.4f}s")

        if getattr(self.state, "error", None):
            print("\nFAILED ENGINE")
            print(self.state.error["engine"])
            print(self.state.error["error"])
        else:
            print("\nPipeline completed successfully.")

        print("=" * 70)

        return self.state

    def events(self):
        return self.bus.history()

