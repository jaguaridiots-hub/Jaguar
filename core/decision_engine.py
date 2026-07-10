from core.engine import Engine
from strategy.idm_engine import InstitutionalDecisionMatrix


class DecisionEngineRunner(Engine):

    name = "DecisionEngine"

    def run(self, state, bus):

        bus.publish("DECISION_ANALYSIS")

        state = InstitutionalDecisionMatrix.evaluate(state)

        state.decision = {
            "decision": state.idm["decision"],
            "score": state.idm["score"],
            "approved": state.idm["approved"],
            "reasons": state.idm["reasons"],
        }

        bus.publish("DECISION_READY")

        return state
