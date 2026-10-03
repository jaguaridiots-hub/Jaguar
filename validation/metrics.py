# validation/metrics.py
import math
from research.database import get_connection
from research.analytics import calculate_metrics

def get_metrics_for_symbol_mode(symbol, mode):
    """Retrieve closed trades for a symbol and mode, compute metrics."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM trades
        WHERE symbol = ? AND mode = ? AND status = 'CLOSED'
        ORDER BY open_time ASC
    ''', (symbol, mode))
    rows = cur.fetchall()
    conn.close()
    columns = [desc[0] for desc in cur.description]
    trades = [dict(zip(columns, row)) for row in rows]
    return calculate_metrics(trades)

def get_regime_metrics(symbol, mode):
    """Placeholder for regime-wise metrics."""
    return {}
