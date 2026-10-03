# learning/performance_analyzer.py
from paper_trading import load_ledger

def analyze_performance(symbol=None):
    ledger = load_ledger()
    trades = ledger.get("positions", [])
    closed = [t for t in trades if t.get("status") == "CLOSED"]
    stats = {
        "total_trades": len(closed),
        "wins": len([t for t in closed if t["pnl"] > 0]),
        "losses": len([t for t in closed if t["pnl"] < 0]),
        "win_rate": 0,
        "profit_factor": 0,
        "symbol_stats": {}
    }
    if closed:
        stats["win_rate"] = round(stats["wins"] / len(closed) * 100, 2)
        total_profit = sum(t["pnl"] for t in closed if t["pnl"] > 0)
        total_loss = abs(sum(t["pnl"] for t in closed if t["pnl"] < 0))
        stats["profit_factor"] = round(total_profit / total_loss, 2) if total_loss > 0 else 0
        for t in closed:
            sym = t["symbol"]
            if sym not in stats["symbol_stats"]:
                stats["symbol_stats"][sym] = {"wins": 0, "losses": 0, "pnl": 0}
            if t["pnl"] > 0:
                stats["symbol_stats"][sym]["wins"] += 1
            else:
                stats["symbol_stats"][sym]["losses"] += 1
            stats["symbol_stats"][sym]["pnl"] += t["pnl"]
    return stats

def get_performance_summary():
    stats = analyze_performance()
    summary = f"""
📊 PERFORMANCE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━
Total Trades : {stats['total_trades']}
Win Rate     : {stats['win_rate']}%
Profit Factor: {stats['profit_factor']}
Wins         : {stats['wins']}
Losses       : {stats['losses']}
"""
    for sym, data in stats["symbol_stats"].items():
        total = data["wins"] + data["losses"]
        wr = round(data["wins"] / total * 100, 2) if total > 0 else 0
        summary += f"\n{sym} -> {data['wins']}W / {data['losses']}L (WR: {wr}%) PnL: ${data['pnl']:.2f}"
    return summary
