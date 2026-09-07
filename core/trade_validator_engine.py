from strategy.trade_validator_engine import TradeValidatorEngine


class TradeValidatorEngineRunner:

    def run(self, state, bus):
        return TradeValidatorEngine().run(state, bus)
