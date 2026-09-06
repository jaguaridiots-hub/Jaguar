class PositionManager:

    def __init__(self):
        self.position = "NONE"
        self.entry = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.pnl = 0.0

    def open_trade(self, direction, entry, sl, tp):
        self.position = direction
        self.entry = entry
        self.stop_loss = sl
        self.take_profit = tp

    def close_trade(self):
        self.position = "NONE"
        self.entry = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.pnl = 0.0

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
            "PnL": round(self.pnl, 2)
        }
