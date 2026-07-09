class EngineRegistry:

    def __init__(self):
        self.engines = []

    def register(self, engine):
        self.engines.append(engine)

    def run(self, state, bus):

        for engine in self.engines:
            engine.run(state, bus)

        return state
