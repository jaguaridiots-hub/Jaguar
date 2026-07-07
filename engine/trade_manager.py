class TradeManager:

    def __init__(self):
        self.break_even = False
        self.trailing = False

        self.position_open = True
        self.tp1_hit = False
        self.tp2_hit = False
        self.trade_closed = False

    def manage(self, state, plan):
        if not plan:
            return {
                "Action": "NO TRADE",
                "StopLoss": False,
                "BreakEven": False,
                "Trailing": False,
            }

        if plan.get("Entry") is None:
            return {
                "Action": "NO TRADE",
                "StopLoss": False,
                "BreakEven": False,
                "Trailing": False,
            }
        entry = float(plan["Entry"])
        sl = float(plan["StopLoss"])
        tp1 = float(plan["TP1"])
        tp2 = float(plan["TP2"])
        tp3 = float(plan["TP3"])

        price = float(state.price)

        action = "HOLD"

        # ===========================
        # TP1
        # ===========================
        if self.position_open and not self.tp1_hit and price >= tp1:
            self.tp1_hit = True
            self.break_even = True
            sl = entry
            action = "BOOK 30%"
            print("\n🎯 TP1 HIT - Stop Loss moved to Break Even")

        # ===========================
        # TP2
        # ===========================
        if self.position_open and not self.tp2_hit and price >= tp2:
            self.tp2_hit = True
            self.trailing = True
            action = "BOOK 30%"
            print("🎯 TP2 HIT - Trailing Stop Activated")

        # ===========================
        # ATR Trailing
        # ===========================
        if self.trailing:
            atr_sl = price - state.atr

            if atr_sl > sl:
                sl = atr_sl

        # ===========================
        # TP3
        # ===========================
        if self.position_open and price >= tp3:
            self.trade_closed = True
            self.position_open = False
            action = "EXIT"
            print("🏆 TP3 HIT - Trade Closed")

        # ===========================
        # Stop Loss
        # ===========================
        if self.position_open and price <= sl:
            self.trade_closed = True
            self.position_open = False
            action = "STOP LOSS"
            print("🛑 STOP LOSS HIT")

        return {
            "Action": action,
            "StopLoss": round(sl, 2),
            "BreakEven": self.break_even,
            "Trailing": self.trailing
        }
