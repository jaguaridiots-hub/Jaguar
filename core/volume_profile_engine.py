from core.engine import Engine
from strategy.volume_profile_engine import VolumeProfileEngine


class VolumeProfileEngineRunner(Engine):

    name = "Volume Profile Engine"

    def run(self, state, bus):

        bus.publish("VOLUME_PROFILE_ANALYSIS")

        candles = state.market_current["candles"]

        state.volume_profile = VolumeProfileEngine.analyze(candles)

        bus.publish("VOLUME_PROFILE_READY")

        return state
