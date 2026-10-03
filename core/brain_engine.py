from ai.jaguar_brain_v4 import JaguarBrainV4

class BrainEngine:
    def run(self, state, bus):
        bus.publish("BRAIN_ANALYSIS")
        state.debug_brain = True
        brain_data = JaguarBrainV4.analyze(state)
        state.brain = brain_data          # legacy
        state.ai_brain = brain_data       # canonical (identical)
        bus.publish("BRAIN_READY")
        return state
