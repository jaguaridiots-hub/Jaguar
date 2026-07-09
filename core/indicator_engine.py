from core.engine import Engine
from indicators.indicator_engine import IndicatorEngine as IndicatorCalculator


class IndicatorEngine(Engine):

    name = "Indicator Engine"

    def run(self, state, bus):

        bus.publish("INDICATORS")

        candles = state.market_current["candles"]

        state.indicators = IndicatorCalculator.calculate(candles)

        state.ai = state.indicators

        bus.publish("TECHNICAL_READY")

        return state
