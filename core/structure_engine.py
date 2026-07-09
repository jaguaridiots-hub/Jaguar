from core.engine import Engine
from strategy.structure_engine import StructureEngine


class StructureEngineRunner(Engine):

    name = "Structure Engine"

    def run(self, state, bus):

        bus.publish("STRUCTURE_ANALYSIS")

        candles = state.market_current["candles"]

        state.structure = StructureEngine.analyze(candles)

        bus.publish("STRUCTURE_READY")

        return state
