from core.engine import Engine
from indicators.indicator_engine import IndicatorEngine as IndicatorCalculator


class IndicatorEngine(Engine):

    name = "Indicator Engine"

    def run(self, state, bus):

        bus.publish("INDICATORS")

        candles = state.market["candles"]

        state.indicators = IndicatorCalculator.calculate(candles)

        bus.publish("TECHNICAL_READY")

        return state
