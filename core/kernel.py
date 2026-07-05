from core.market_state import MarketState

class JaguarKernel:

    def __init__(self):
        self.state = MarketState()

    def initialize(self, symbol, timeframe):
        self.state.symbol = symbol
        self.state.timeframe = timeframe

        print("\n========== JAGUAR KERNEL ==========")
        print("System Status : ONLINE")
        print("Symbol        :", symbol)
        print("Timeframe     :", timeframe)
        print("==================================")

    def get_state(self):
        return self.state
