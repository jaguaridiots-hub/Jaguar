from core.state import JaguarState
from core.event_bus import EventBus
from core.engine_registry import EngineRegistry
from core.register_engines import register

from core.evidence_fusion import EvidenceFusionEngine
from core.decision_engine import DecisionEngine


def analyze(symbol, interval, state=None, bus=None):
    if state is None:
        state = JaguarState()

    if bus is None:
        bus = EventBus()

    state.symbol = symbol
    state.interval = interval

    # Ensure blackboard exists
    if not hasattr(state, "blackboard"):
        from core.market_blackboard import MarketBlackboard
        state.blackboard = MarketBlackboard()

    registry = EngineRegistry()
    register(registry)

    # ---------------------------------
    # Run institutional engines
    # ---------------------------------
    registry.run(state, bus)

    # ---------------------------------
    # Phase 2B - Evidence Fusion
    # ---------------------------------
    fusion = EvidenceFusionEngine().fuse(state.blackboard)
    state.fusion = fusion

    # ---------------------------------
    # Phase 3 - Decision Engine
    # ---------------------------------
    decision = DecisionEngine().evaluate(fusion)
    state.decision = decision

    return state
