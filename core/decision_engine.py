from strategy.master_decision import MasterDecision

class DecisionEngineRunner:

    def run(self, state, bus):

        bus.publish("DECISION_ANALYSIS")

        state = MasterDecision.decide(state)

        bus.publish("DECISION_READY")

        return state
