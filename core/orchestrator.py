from core.state import JaguarState
from core.event_bus import EventBus
from core.logger import logger

from core.engine_registry import EngineRegistry

from core.market_engine import MarketEngine
from core.indicator_engine import IndicatorEngine
from core.score_engine import ScoreEngine


class JaguarOrchestrator:

    def __init__(self):

        self.state = JaguarState()
        self.bus = EventBus()

        self.registry = EngineRegistry()

        from core.register_engines import register

        register(self.registry)

    def publish(self, event, payload=None):

        logger.info(event)
        self.bus.publish(event, payload)

    def analyze(self,
                symbol="BTCUSDT",
                interval="15m"):

        self.state.symbol = symbol
        self.state.interval = interval

        self.publish("SYSTEM_START")

        self.registry.run(self.state, self.bus)

        self.publish("SYSTEM_FINISHED")

        return self.state

    def events(self):
        return self.bus.history()
