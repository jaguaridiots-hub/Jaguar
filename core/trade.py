from dataclasses import dataclass
from typing import Optional


@dataclass
class Trade:
    symbol: str = ""
    timeframe: str = ""

    direction: str = ""      # BUY / SELL

    entry: float = 0.0
    stop_loss: float = 0.0

    take_profit_1: float = 0.0
    take_profit_2: float = 0.0

    exit_price: float = 0.0

    status: str = "OPEN"      # OPEN / WIN / LOSS / BREAKEVEN

    pnl: float = 0.0
    rr: float = 0.0

    entry_index: int = 0
    exit_index: int = 0

    entry_time: Optional[str] = None
    exit_time: Optional[str] = None

    reason: str = ""
