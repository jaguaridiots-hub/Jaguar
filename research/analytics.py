# research/analytics.py
import math
from .database import get_connection

def calculate_metrics(trades):
    """
    Compute performance metrics from a list of trades.
    Expects a list of dicts with keys: pnl, r_multiple, win_loss.
    """
    if not trades:
        return {}

    total = len(trades)
    wins = [t for t in trades if t.get('win_loss') == 1]
    losses = [t for t in trades if t.get('win_loss') == 0]
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = win_count / total if total > 0 else 0

    gross_profit = sum(t.get('pnl', 0) for t in wins) if wins else 0
    gross_loss = sum(abs(t.get('pnl', 0)) for t in losses) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    net_profit = gross_profit - gross_loss

    avg_r = sum(t.get('r_multiple', 0) for t in trades) / total if total > 0 else 0

    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    expectancy = (avg_win * win_rate) - (avg_loss * (1 - win_rate))

    # Sharpe (based on PnL)
    returns = [t.get('pnl', 0) for t in trades]
    if returns:
        mean_return = sum(returns) / len(returns)
        std_dev = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
        sharpe = mean_return / std_dev if std_dev > 0 else 0
    else:
        sharpe = 0

    # Sortino
    downside = [r for r in returns if r < 0]
    if downside:
        mean_down = sum(downside) / len(downside)
        downside_dev = math.sqrt(sum((r - mean_down) ** 2 for r in downside) / len(downside)) if len(downside) > 1 else 0
        sortino = mean_return / downside_dev if downside_dev > 0 else 0
    else:
        sortino = 0

    # Drawdown (equity curve)
    equity = []
    cum = 0
    for t in trades:
        cum += t.get('pnl', 0)
        equity.append(cum)
    max_equity = 0
    max_drawdown = 0
    for e in equity:
        if e > max_equity:
            max_equity = e
        drawdown = max_equity - e
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    recovery_factor = net_profit / max_drawdown if max_drawdown > 0 else float('inf')

    return {
        "total_trades": total,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "loss_rate": 1 - win_rate if total > 0 else 0,
        "profit_factor": profit_factor,
        "net_profit": net_profit,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "avg_r": avg_r,
        "expectancy": expectancy,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown": max_drawdown,
        "recovery_factor": recovery_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
    }

def get_trades(symbol=None, mode=None):
    """Fetch closed trades with optional filters."""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM trades WHERE status = 'CLOSED'"
    params = []
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    if mode:
        query += " AND mode = ?"
        params.append(mode)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]
