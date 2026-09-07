class PositionManager:

    def __init__(self):
        self.position = "NONE"
        self.entry = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.pnl = 0.0
        self.position_size = 0.0
        self.initial_risk = 0.0
        self.trade_uuid = None

    def open_trade(
        self,
        direction,
        entry,
        sl,
        tp,
        position_size=0.0,
        initial_risk=0.0,
    ):
        self.position = direction
        self.entry = entry
        self.stop_loss = sl
        self.take_profit = tp
        self.position_size = float(position_size or 0.0)
        self.initial_risk = float(initial_risk or 0.0)
        self.trade_uuid = None

    def close_trade(self):
        self.position = "NONE"
        self.entry = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.pnl = 0.0
        self.position_size = 0.0
        self.initial_risk = 0.0
        self.trade_uuid = None

    def update(self, current_price):
        if self.position == "LONG":
            self.pnl = current_price - self.entry

        elif self.position == "SHORT":
            self.pnl = self.entry - current_price


    def update_stop_loss(self, stop_loss):
        self.stop_loss = stop_loss
    def status(self):
        return {
            "Position": self.position,
            "Entry": round(self.entry, 2),
            "StopLoss": round(self.stop_loss, 2),
            "TakeProfit": round(self.take_profit, 2),
            "PnL": round(self.pnl, 2),
            "PositionSize": round(self.position_size, 4),
            "InitialRisk": round(self.initial_risk, 2),
            "TradeUUID": self.trade_uuid,
        }
