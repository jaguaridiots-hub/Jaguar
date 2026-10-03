from dataclasses import dataclass
from typing import Optional


@dataclass
class Trade:
    symbol: str = ""
    timeframe: str = ""

    direction: str = ""          # BUY / SELL

    entry: float = 0.0
    stop_loss: float = 0.0

    take_profit_1: float = 0.0
    take_profit_2: float = 0.0

    exit_price: float = 0.0

    status: str = "OPEN"         # OPEN / WIN / LOSS / BREAKEVEN

    pnl: float = 0.0
    rr: float = 0.0

    entry_index: int = 0
    exit_index: int = 0

    entry_time: Optional[str] = None
    exit_time: Optional[str] = None

    reason: str = ""

    # --- NEW FIELDS for research integration ---
    quantity: float = 1.0        # position size (from risk)
    uuid: Optional[str] = None   # trade UUID from research DB

    def compute_pnl(self):
        """Calculate PnL and R-multiple after exit is known."""
        if self.exit_price == 0.0 or self.status not in ("WIN", "LOSS"):
            return

        if self.direction == "BUY":
            self.pnl = (self.exit_price - self.entry) * self.quantity
            risk = self.entry - self.stop_loss
        else:  # SELL
            self.pnl = (self.entry - self.exit_price) * self.quantity
            risk = self.stop_loss - self.entry

        if risk != 0:
            self.rr = self.pnl / risk
        else:
            self.rr = 0.0
