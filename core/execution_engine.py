from core.engine import Engine
from strategy.execution_engine import ExecutionEngine


class ExecutionEngineRunner(Engine):

    name = "Execution"

    def run(self, state, bus):

        return ExecutionEngine().run(state, bus)
