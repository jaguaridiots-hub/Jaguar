from core.engine import Engine
from strategy.execution_trigger_engine import ExecutionTriggerEngine


class ExecutionTriggerEngineRunner(Engine):

    name = "Execution Trigger Engine"

    def run(self, state, bus):

        bus.publish("EXECUTION_TRIGGER_ANALYSIS")

        state = ExecutionTriggerEngine.analyze(state)

        bus.publish("EXECUTION_TRIGGER_READY")

        return state
