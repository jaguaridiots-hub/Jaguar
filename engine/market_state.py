from dataclasses import dataclass

@dataclass
class MarketState:

    symbol = "BTCUSDT"
    timeframe = "15m"

    price = 0.0
    high = 0.0
    low = 0.0
    volume = 0.0

    ema20 = 0.0
    ema50 = 0.0
    ema100 = 0.0
    ema200 = 0.0

    rsi = 0.0
    atr = 0.0

    trend = "UNKNOWN"
    regime = "UNKNOWN"

    support = 0.0
    resistance = 0.0

    ai_score = 0
    probability = 0
    confidence = "D"

    decision = "NO TRADE"

    entry = 0.0
    stoploss = 0.0

    tp1 = 0.0
    tp2 = 0.0
    tp3 = 0.0

    position = "NONE"

    pnl = 0.0
    pnl_percent = 0.0

    win_rate = 0.0
    trades = 0

    def summary(self):

        return {
            "Symbol": self.symbol,
            "Timeframe": self.timeframe,
            "Price": self.price,
            "Trend": self.trend,
            "EMA20": self.ema20,
            "EMA50": self.ema50,
            "EMA100": self.ema100,
            "EMA200": self.ema200,
            "RSI": self.rsi,
            "ATR": self.atr,
            "Support": self.support,
            "Resistance": self.resistance,
            "AI Score": self.ai_score,
            "Probability": self.probability,
            "Confidence": self.confidence,
            "Decision": self.decision,
            "Entry": self.entry,
            "StopLoss": self.stoploss,
            "TP1": self.tp1,
            "TP2": self.tp2,
            "TP3": self.tp3,
            "Position": self.position,
            "PnL": self.pnl,
            "PnL %": self.pnl_percent,
            "Win Rate": self.win_rate,
            "Trades": self.trades
        }
