from core.market_state import MarketState


class JaguarKernel:

    def __init__(self):
        self.state = MarketState()

    def initialize(self, symbol="BTCUSDT", timeframe="15m"):
        self.state.symbol = symbol.upper()
        self.state.timeframe = timeframe

        print("\n" + "=" * 60)
        print("                JAGUAR KERNEL")
        print("=" * 60)
        print(f"System Status : ONLINE")
        print(f"Symbol        : {self.state.symbol}")
        print(f"Timeframe     : {self.state.timeframe}")
        print("=" * 60)

    def get_state(self):
        return self.state

    def update_price(self, price, high, low, volume):
        self.state.price = float(price)
        self.state.high = float(high)
        self.state.low = float(low)
        self.state.volume = float(volume)

    def update_indicators(
        self,
        ema20,
        ema50,
        ema100,
        ema200,
        rsi,
        atr,
        trend
    ):
        self.state.ema20 = float(ema20)
        self.state.ema50 = float(ema50)
        self.state.ema100 = float(ema100)
        self.state.ema200 = float(ema200)
        self.state.rsi = float(rsi)
        self.state.atr = float(atr)
        self.state.trend = trend

    def update_levels(self, support, resistance):
        self.state.support = float(support)
        self.state.resistance = float(resistance)

    def update_decision(self, score, probability, confidence, decision):
        self.state.ai_score = score
        self.state.probability = probability
        self.state.confidence = confidence
        self.state.decision = decision

    def reset_trade(self):
        self.state.entry = 0.0
        self.state.stoploss = 0.0
        self.state.tp1 = 0.0
        self.state.tp2 = 0.0
        self.state.tp3 = 0.0
        self.state.position = "NONE"

    def summary(self):
        return self.state.summary()
