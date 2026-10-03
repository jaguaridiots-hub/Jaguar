from core.engine import Engine
from strategy.execution_confirmation_engine import ExecutionConfirmationEngine


class ExecutionConfirmationEngineRunner(Engine):

    name = "Execution Confirmation"

    def run(self, state, bus):
        bus.publish("EXECUTION_CONFIRMATION_ANALYSIS")

        state = ExecutionConfirmationEngine().run(state, bus)

        bus.publish("EXECUTION_CONFIRMATION_READY")

        return state
