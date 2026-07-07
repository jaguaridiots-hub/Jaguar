from indicators.ema import ema
from indicators.rsi import rsi
from indicators.volume import volume
from indicators.fibonacci import fibonacci
from indicators.atr import atr
from indicators.macd import macd
from indicators.adx import adx
from indicators.supertrend import supertrend
from indicators.bollinger import bollinger
from indicators.vwap import vwap

class IndicatorEngine:

    @staticmethod
    def calculate(candles):

        return {
            "ema": ema(candles),
            "rsi": rsi(candles),
            "volume": volume(candles),
            "fibonacci": fibonacci(candles),
            "atr": atr(candles),
            "macd": macd(candles),
            "adx": adx(candles),
            "supertrend": supertrend(candles),
            "bollinger": bollinger(candles),
            "vwap": vwap(candles),
        }
