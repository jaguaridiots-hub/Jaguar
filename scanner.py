from core.trading_kernel import TradingKernel
from indicators.indicator_engine import IndicatorEngine
from strategy.support_resistance import SupportResistance
from strategy.decision import DecisionEngine

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT"
]

print("=" * 80)
print("JAGUAR MARKET SCANNER")
print("=" * 80)

for symbol in symbols:

    k = TradingKernel(symbol)
    data = k.load()

    ind = IndicatorEngine.calculate(data["candles"])
    sr = SupportResistance.calculate(data["candles"])

    decision = DecisionEngine.analyze(ind, sr)

    print(f"{symbol:10} | {decision['signal']:10} | Score: {decision['score']:3} | Confidence: {decision['confidence']:3}")

