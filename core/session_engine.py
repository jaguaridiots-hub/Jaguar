from core.engine import Engine
from strategy.session_engine import SessionEngine


class SessionEngineRunner(Engine):

    name = "Session Engine"

    def run(self, state, bus):

        engine = SessionEngine()

        return engine.run(state, bus)
