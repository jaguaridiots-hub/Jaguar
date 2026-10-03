import math


class TradeManager:

    def __init__(self):
        self.break_even = False
        self.trailing = False

        self.position_open = False
        self.tp1_hit = False
        self.tp2_hit = False
        self.trade_closed = False

    def snapshot(self):
        return {
            "position_open": bool(self.position_open),
            "trade_closed": bool(self.trade_closed),
            "break_even": bool(self.break_even),
            "trailing": bool(self.trailing),
            "tp1_hit": bool(self.tp1_hit),
            "tp2_hit": bool(self.tp2_hit),
        }

    def restore(self, snapshot):
        if not isinstance(snapshot, dict):
            raise RuntimeError(
                "FAIL-CLOSED: Invalid TradeManager lifecycle state"
            )

        fields = (
            "position_open",
            "trade_closed",
            "break_even",
            "trailing",
            "tp1_hit",
            "tp2_hit",
        )

        for field in fields:
            value = snapshot.get(field)
            if not isinstance(value, bool):
                raise RuntimeError(
                    "FAIL-CLOSED: Invalid TradeManager lifecycle flag: "
                    f"{field}"
                )

        if snapshot["position_open"] is not True:
            raise RuntimeError(
                "FAIL-CLOSED: Restored active position has inactive manager"
            )

        if snapshot["trade_closed"] is not False:
            raise RuntimeError(
                "FAIL-CLOSED: Restored active position is marked closed"
            )

        if snapshot["tp2_hit"] and not snapshot["tp1_hit"]:
            raise RuntimeError(
                "FAIL-CLOSED: Invalid TradeManager TP lifecycle"
            )

        if snapshot["break_even"] and not snapshot["tp1_hit"]:
            raise RuntimeError(
                "FAIL-CLOSED: Invalid TradeManager break-even lifecycle"
            )

        if snapshot["trailing"] and not snapshot["tp2_hit"]:
            raise RuntimeError(
                "FAIL-CLOSED: Invalid TradeManager trailing lifecycle"
            )

        self.position_open = True
        self.trade_closed = False
        self.break_even = snapshot["break_even"]
        self.trailing = snapshot["trailing"]
        self.tp1_hit = snapshot["tp1_hit"]
        self.tp2_hit = snapshot["tp2_hit"]

    def activate(self):
        self.position_open = True
        self.trade_closed = False
        self.break_even = False
        self.trailing = False
        self.tp1_hit = False
        self.tp2_hit = False

    def deactivate(self):
        self.position_open = False
        self.trade_closed = True
        self.break_even = False
        self.trailing = False
        self.tp1_hit = False
        self.tp2_hit = False

    def manage(self, state, plan, current_stop=None):
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

        if current_stop is None:
            sl = float(plan["StopLoss"])
        else:
            sl = float(current_stop)

            if not math.isfinite(sl) or sl <= 0:
                raise RuntimeError(
                    "FAIL-CLOSED: Invalid current position stop"
                )

        tp1 = float(plan["TP1"])
        tp2 = float(plan["TP2"])
        tp3 = float(plan["TP3"])
        price = float(state.price)

        direction = str(
            plan.get("Direction", "")
        ).upper().strip()

        is_short = direction == "SELL"

        action = "HOLD"

        # ===========================
        # TP1
        # ===========================
        tp1_hit = (
            price <= tp1
            if is_short
            else price >= tp1
        )

        if self.position_open and not self.tp1_hit and tp1_hit:
            self.tp1_hit = True
            self.break_even = True
            sl = entry
            action = "BOOK 30%"
            print(
                "\n🎯 TP1 HIT - Stop Loss moved to Break Even"
            )

        # ===========================
        # TP2
        # ===========================
        tp2_hit = (
            price <= tp2
            if is_short
            else price >= tp2
        )

        if self.position_open and not self.tp2_hit and tp2_hit:
            self.tp2_hit = True
            self.trailing = True
            action = "BOOK 30%"
            print(
                "🎯 TP2 HIT - Trailing Stop Activated"
            )

        # ===========================
        # ATR Trailing
        # ===========================
        if self.trailing:
            atr = float(state.atr)

            atr_sl = (
                price + atr
                if is_short
                else price - atr
            )

            if is_short:
                if atr_sl < sl:
                    sl = atr_sl
            else:
                if atr_sl > sl:
                    sl = atr_sl

        # ===========================
        # TP3
        # ===========================
        tp3_hit = (
            price <= tp3
            if is_short
            else price >= tp3
        )

        if self.position_open and tp3_hit:
            self.trade_closed = True
            self.position_open = False
            action = "EXIT"
            print(
                "🏆 TP3 HIT - Trade Closed"
            )

        # ===========================
        # Stop Loss
        # ===========================
        stop_hit = (
            price >= sl
            if is_short
            else price <= sl
        )

        if self.position_open and stop_hit:
            self.trade_closed = True
            self.position_open = False
            action = "STOP LOSS"
            print(
                "🛑 STOP LOSS HIT"
            )

        return {
            "Action": action,
            "StopLoss": round(sl, 2),
            "BreakEven": self.break_even,
            "Trailing": self.trailing,
        }
