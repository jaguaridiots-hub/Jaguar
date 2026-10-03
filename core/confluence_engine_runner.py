from core.engine import Engine
from core.confluence_engine import ConfluenceEngine


class ConfluenceEngineRunner(Engine):

    name = "ConfluenceEngine"

    def run(self, state, bus):

        bus.publish("CONFLUENCE_ANALYSIS")

        ConfluenceEngine.evaluate(state)

        bus.publish("CONFLUENCE_READY")

        return state
