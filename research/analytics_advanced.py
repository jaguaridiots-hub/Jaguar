# research/analytics_advanced.py
import json
import math
from datetime import datetime
from .database import get_connection

def get_trades_with_filters(symbol=None, mode=None, asset_class=None):
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
    if asset_class:
        query += " AND asset_class = ?"
        params.append(asset_class)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    columns = [desc[0] for desc in cur.description]
    trades = [dict(zip(columns, row)) for row in rows]
    trades.sort(key=lambda t: t.get('close_time', ''))
    return trades

def compute_institutional_metrics(trades):
    if not trades:
        return {}

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

    avg_r = sum(t.get('r_multiple', 0) for t in trades) / total_trades if total_trades > 0 else 0

    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    expectancy = (avg_win * win_rate) - (avg_loss * (1 - win_rate))

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
        "loss_rate": 1 - win_rate if total_trades > 0 else 0,
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
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
    }

def compute_grouped_stats(symbol=None, mode=None, asset_class=None):
    trades = get_trades_with_filters(symbol, mode, asset_class)
    overall = compute_institutional_metrics(trades)

    by_symbol = {}
    by_mode = {}
    by_regime = {}
    by_asset_class = {}
    by_year = {}
    by_month = {}
    by_session = {}

    for t in trades:
        sym = t.get('symbol')
        if sym:
            by_symbol.setdefault(sym, []).append(t)
        m = t.get('mode')
        if m:
            by_mode.setdefault(m, []).append(t)
        regime = t.get('market_regime')
        if regime:
            by_regime.setdefault(regime, []).append(t)
        ac = t.get('asset_class')
        if ac:
            by_asset_class.setdefault(ac, []).append(t)
        if t.get('close_time'):
            dt = datetime.fromisoformat(t['close_time'])
            year = str(dt.year)
            month = dt.strftime('%Y-%m')
            hour = dt.hour
            if 6 <= hour < 12:
                session = "Morning"
            elif 12 <= hour < 17:
                session = "Afternoon"
            elif 17 <= hour < 22:
                session = "Evening"
            else:
                session = "Night"
            by_year.setdefault(year, []).append(t)
            by_month.setdefault(month, []).append(t)
            by_session.setdefault(session, []).append(t)

    return {
        "overall": overall,
        "by_symbol": {k: compute_institutional_metrics(v) for k, v in by_symbol.items()},
        "by_mode": {k: compute_institutional_metrics(v) for k, v in by_mode.items()},
        "by_regime": {k: compute_institutional_metrics(v) for k, v in by_regime.items()},
        "by_asset_class": {k: compute_institutional_metrics(v) for k, v in by_asset_class.items()},
        "by_year": {k: compute_institutional_metrics(v) for k, v in by_year.items()},
        "by_month": {k: compute_institutional_metrics(v) for k, v in by_month.items()},
        "by_session": {k: compute_institutional_metrics(v) for k, v in by_session.items()},
    }

def get_engine_contributions(symbol=None, mode=None, asset_class=None):
    """Aggregate engine contributions across trades."""
    trades = get_trades_with_filters(symbol, mode, asset_class)
    contrib_data = {}
    for t in trades:
        snap = t.get('snapshot_open')
        if snap:
            try:
                snap_data = json.loads(snap)
                brain_explain = snap_data.get('brain_explain', {})
                for contrib in brain_explain.get('contributions', []):
                    label = contrib.get('label')
                    if label:
                        if label not in contrib_data:
                            contrib_data[label] = {'total': 0, 'count': 0, 'wins': 0, 'losses': 0}
                        contrib_data[label]['total'] += contrib.get('contribution', 0)
                        contrib_data[label]['count'] += 1
                        if t.get('win_loss') == 1:
                            contrib_data[label]['wins'] += 1
                        else:
                            contrib_data[label]['losses'] += 1
            except:
                pass

    result = []
    for label, data in contrib_data.items():
        avg = data['total'] / data['count'] if data['count'] > 0 else 0
        win_rate_contrib = data['wins'] / data['count'] if data['count'] > 0 else 0
        result.append({
            "engine": label,
            "avg_contribution": avg,
            "count": data['count'],
            "win_rate": win_rate_contrib
        })
    return sorted(result, key=lambda x: x['avg_contribution'], reverse=True)
