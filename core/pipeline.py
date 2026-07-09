from core.state import JaguarState
from core.event_bus import EventBus
from core.engine_registry import EngineRegistry
from core.register_engines import register


def analyze(symbol, interval):

    state = JaguarState()

    state.symbol = symbol
    state.interval = interval

    bus = EventBus()

    registry = EngineRegistry()

    register(registry)

    registry.run(state, bus)

    return state
