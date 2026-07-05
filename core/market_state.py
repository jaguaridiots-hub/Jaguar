class MarketState:

    def __init__(self):

        # =========================
        # MARKET
        # =========================

        self.symbol = ""
        self.timeframe = ""
        self.price = 0.0
        self.bid = 0.0
        self.ask = 0.0
        self.spread = 0.0
        self.volume = 0.0

        # =========================
        # INDICATORS
        # =========================

        self.ema20 = 0.0
        self.ema50 = 0.0
        self.ema100 = 0.0
        self.ema200 = 0.0

        self.rsi = 0.0
        self.atr = 0.0

        # =========================
        # TREND
        # =========================

        self.trend = "UNKNOWN"
        self.regime = "UNKNOWN"

        # =========================
        # SMC
        # =========================

        self.bos = False
        self.choch = False
        self.order_block = False
        self.fvg = False
        self.liquidity = False
        self.inducement = False
        self.discount = False
        self.premium = False

        # =========================
        # GANN
        # =========================

        self.gann = {}

        # =========================
        # FIBONACCI
        # =========================

        self.fibonacci = {}

        # =========================
        # SUPPORT / RESISTANCE
        # =========================

        self.support = 0.0
        self.resistance = 0.0

        # =========================
        # AI
        # =========================

        self.ai_score = 0
        self.smc_score = 0
        self.probability = 0
        self.confidence = ""
        self.decision = ""

        # =========================
        # TRADE
        # =========================

        self.entry = 0.0
        self.stoploss = 0.0

        self.tp1 = 0.0
        self.tp2 = 0.0
        self.tp3 = 0.0

        self.position = "NONE"

        self.pnl = 0.0
        self.pnl_percent = 0.0

        # =========================
        # PERFORMANCE
        # =========================

        self.win_rate = 0.0
        self.total_trades = 0

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

            "PnL": self.pnl,
            "PnL %": self.pnl_percent,

            "Position": self.position,

            "Win Rate": self.win_rate,
            "Trades": self.total_trades

        }
