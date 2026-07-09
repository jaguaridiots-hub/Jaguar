from ai.jaguar_brain_v4 import JaguarBrainV4


class BrainEngine:

    def run(self, state, bus):

        bus.publish("BRAIN_ANALYSIS")

        state.brain = JaguarBrainV4.analyze(state)

        bus.publish("BRAIN_READY")

        return state
