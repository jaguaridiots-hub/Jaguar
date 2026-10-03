from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BacktestResult:
    total_trades: int = 0

    wins: int = 0
    losses: int = 0

    win_rate: float = 0.0
    loss_rate: float = 0.0

    gross_profit: float = 0.0
    gross_loss: float = 0.0

    net_profit: float = 0.0

    max_drawdown: float = 0.0

    profit_factor: float = 0.0

    average_rr: float = 0.0

    expectancy: float = 0.0

    sharpe_ratio: float = 0.0

    trades: List[Dict] = field(default_factory=list)
