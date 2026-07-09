from strategy.structure_engine import StructureEngine


class StructureEngineRunner:

    def run(self, state, bus):

        bus.publish("STRUCTURE_ANALYSIS")

        candles = state.market["candles"]

        state.structure = StructureEngine.analyze(candles)

        bus.publish("STRUCTURE_READY")

        return state
