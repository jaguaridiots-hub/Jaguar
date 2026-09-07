from core.engine import Engine
from strategy.dashboard_engine import DashboardEngine


class DashboardEngineRunner(Engine):

    name = "Dashboard"

    def run(self, state, bus):

        return DashboardEngine().run(state, bus)
