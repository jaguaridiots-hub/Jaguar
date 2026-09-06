# validation/analytics.py
import math
from research.database import get_connection

def get_closed_trades(symbol=None, mode=None):
    """Fetch closed trades from the research database."""
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

def compute_backtest_metrics(symbol=None, mode=None):
    """Compute all institutional metrics for a given symbol/mode."""
    trades = get_closed_trades(symbol, mode)
    if not trades:
        return None

    total_trades = len(trades)
    wins = [t for t in trades if t.get('win_loss') == 1]
    losses = [t for t in trades if t.get('win_loss') == 0]
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = win_count / total_trades if total_trades > 0 else 0

    gross_profit = sum(t.get('pnl', 0) for t in wins) if wins else 0
    gross_loss = sum(abs(t.get('pnl', 0)) for t in losses) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    net_profit = gross_profit - gross_loss

    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    expectancy = (avg_win * win_rate) - (avg_loss * (1 - win_rate))

    avg_r = sum(t.get('r_multiple', 0) for t in trades) / total_trades if total_trades > 0 else 0

    returns = [t.get('pnl', 0) for t in trades]
    if returns:
        mean_return = sum(returns) / len(returns)
        std_dev = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
        sharpe = mean_return / std_dev if std_dev > 0 else 0
    else:
        sharpe = 0

    downside = [r for r in returns if r < 0]
    if downside:
        mean_down = sum(downside) / len(downside)
        downside_dev = math.sqrt(sum((r - mean_down) ** 2 for r in downside) / len(downside)) if len(downside) > 1 else 0
        sortino = mean_return / downside_dev if downside_dev > 0 else 0
    else:
        sortino = 0

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

    # Max consecutive wins/losses
    max_win_streak = 0
    max_loss_streak = 0
    current_streak = 0
    current_type = None
    for t in trades:
        wl = t.get('win_loss', 0)
        if current_type is None:
            current_type = wl
            current_streak = 1
        elif wl == current_type:
            current_streak += 1
        else:
            if current_type == 1:
                max_win_streak = max(max_win_streak, current_streak)
            else:
                max_loss_streak = max(max_loss_streak, current_streak)
            current_type = wl
            current_streak = 1
    if current_type == 1:
        max_win_streak = max(max_win_streak, current_streak)
    else:
        max_loss_streak = max(max_loss_streak, current_streak)

    return {
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "net_profit": net_profit,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "avg_r": avg_r,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown": max_drawdown,
        "recovery_factor": recovery_factor,
        "max_consecutive_wins": max_win_streak,
        "max_consecutive_losses": max_loss_streak,
    }

def compute_engine_contributions(symbol=None, mode=None):
    """Compute average contribution per engine for all closed trades."""
    conn = get_connection()
    cur = conn.cursor()
    query = '''
        SELECT ec.engine_name, AVG(ec.final_contribution) as avg_contrib
        FROM engine_contributions ec
        JOIN trades t ON ec.trade_id = t.id
        WHERE t.status = 'CLOSED'
    '''
    params = []
    if symbol:
        query += " AND t.symbol = ?"
        params.append(symbol)
    if mode:
        query += " AND t.mode = ?"
        params.append(mode)
    query += " GROUP BY ec.engine_name ORDER BY avg_contrib DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [{"engine": row[0], "avg_contribution": row[1]} for row in rows]
