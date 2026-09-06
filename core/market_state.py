class MarketState:

    def __init__(self):

        # ==================================================
        # MARKET
        # ==================================================

        self.symbol = ""
        self.timeframe = ""

        # Legacy compatibility
        self.interval = ""

        self.price = 0.0
        self.bid = 0.0
        self.ask = 0.0
        self.spread = 0.0
        self.volume = 0.0

        # ==================================================
        # INDICATORS
        # ==================================================

        self.ema20 = 0.0
        self.ema50 = 0.0
        self.ema100 = 0.0
        self.ema200 = 0.0

        # Canonical current-timeframe indicator snapshot
        self.indicators = {}

        self.rsi = 0.0
        self.atr = 0.0

        # ==================================================
        # TREND
        # ==================================================

        self.trend = "UNKNOWN"
        self.regime = "UNKNOWN"

        # ==================================================
        # SMART MONEY CONCEPTS
        # ==================================================

        self.bos = False
        self.choch = False
        self.order_block = False
        self.fvg = False
        self.liquidity = False
        self.inducement = False
        self.discount = False
        self.premium = False

        # ==================================================
        # CANONICAL STRUCTURAL MEMORY
        #
        # Persistent across analytical pipeline cycles.
        #
        # Current-cycle market facts belong in state.market.
        # Structural character memory belongs on MarketState
        # because institutional_master rebuilds state.market.
        # ==================================================

        self.structural_memory = {
            "direction": "NEUTRAL",
            "state": "UNDEFINED",
            "protected_level": 0.0,
            "protected_pivot_index": None,
            "established_by": "NONE",
            "last_transition": "NONE",
            "last_high_index": None,
            "last_low_index": None,
        }

        # ==================================================
        # GANN
        # ==================================================

        self.gann = {}

        # ==================================================
        # FIBONACCI
        # ==================================================

        self.fibonacci = {}

        # ==================================================
        # SUPPORT / RESISTANCE
        # ==================================================

        self.support = 0.0
        self.resistance = 0.0

        # ==================================================
        # AI (LEGACY - KEEP FOR COMPATIBILITY)
        # ==================================================

        self.ai_score = 0
        self.smc_score = 0
        self.probability = 0
        self.confidence = ""
        self.decision = ""

        # ==================================================
        # TRADE (LEGACY)
        # ==================================================

        self.entry = 0.0
        self.stoploss = 0.0

        self.tp1 = 0.0
        self.tp2 = 0.0
        self.tp3 = 0.0

        self.position = "NONE"

        self.pnl = 0.0
        self.pnl_percent = 0.0

        # ==================================================
        # PERFORMANCE
        # ==================================================

        self.win_rate = 0.0
        self.total_trades = 0

        # ==================================================
        # ENTERPRISE STATE (NEW ARCHITECTURE)
        # ==================================================

        self.metadata = {
            "version": "2.0",
            "engine": "Jaguar Quant X",
            "symbol": "",
            "timeframe": ""
        }

        self.market_data = {}

        self.market = {
            "trend": self.trend,
            "regime": self.regime,
            "structure": {},
            "liquidity": {},
            "order_blocks": {},
            "fair_value_gaps": {},
            "wyckoff": {},
            "gann": self.gann,
            "fibonacci": self.fibonacci,
            "support": self.support,
            "resistance": self.resistance,
            "session": {},
            "volume_profile": {},
            "momentum": {}
        }

        self.institutional = {
            "score": 0,
            "grade": "F",
            "confidence": 0,
            "alignment": 0,
            "reasons": [],
            "warnings": []
        }

        self.brain = {
            "context": {},
            "narrative": "",
            "regime": "UNKNOWN",
            "conflicts": [],
            "summary": ""
        }

        self.idm = {
            "decision": "WAIT",
            "confidence": 0,
            "priority": "LOW",
            "reasons": []
        }

        self.trade = {
            "entry": 0.0,
            "stop_loss": 0.0,
            "targets": [],
            "risk_reward": 0.0,
            "status": "PENDING"
        }

        self.risk = {
            "approved": False,
            "position_size": 0.0,
            "risk_percent": 0.0,
            "reason": ""
        }

        self.execution = {
            "ready": False,
            "status": "WAIT",
            "broker": "",
            "order_id": ""
        }

        self.analytics = {
            "trade_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }

    @property
    def interval(self):
        """
        Legacy alias for timeframe.
        """
        return self.timeframe


    @interval.setter
    def interval(self, value):
        """
        Keep legacy interval and enterprise timeframe synchronized.
        """
        self.timeframe = value

    def summary(self):

        return {

            # Legacy Summary

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
            "Trades": self.total_trades,

            # Enterprise Summary

            "Institutional": self.institutional,
            "Brain": self.brain,
            "IDM": self.idm,
            "Trade": self.trade,
            "Risk": self.risk,
            "Execution": self.execution,
            "Analytics": self.analytics
        }
