from core.state import JaguarState
from core.event_bus import EventBus
from core.logger import logger

from core.engine_registry import EngineRegistry


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

    def analyze(
        self,
        symbol="BTCUSDT",
        interval="15m"
    ):

        self.state.symbol = symbol
        self.state.interval = interval

        print("\n" + "=" * 70)
        print("JAGUAR QUANT X ENTERPRISE")
        print("=" * 70)

        self.publish("SYSTEM_START")

        self.registry.run(self.state, self.bus)

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
