# research/feature_predictiveness_audit.py
import json
import math
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_all_trades():
    """Fetch all closed trades with contributions, regime, symbol, mode, and outcome."""
    conn = get_connection()
    query = """
        SELECT t.win_loss, t.pnl, t.r_multiple, s.brain_score, s.composite_score,
               s.contributions_json, s.regime, s.run_id, t.symbol, t.mode, t.timeframe
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mutual_information(x, y, bins=10):
    """Approximate mutual information for continuous x and binary y."""
    if len(x) == 0:
        return 0.0
    # Discretize x into bins
    min_x, max_x = min(x), max(x)
    if min_x == max_x:
        return 0.0
    bin_width = (max_x - min_x) / bins
    bin_indices = [int((v - min_x) / bin_width) for v in x]
    bin_indices = [min(b, bins-1) for b in bin_indices]

    # Counts
    total = len(x)
    # P(y)
    p_y1 = sum(y) / total
    p_y0 = 1 - p_y1
    # P(x_bin)
    bin_counts = defaultdict(int)
    bin_y1_counts = defaultdict(int)
    for b, yi in zip(bin_indices, y):
        bin_counts[b] += 1
        if yi == 1:
            bin_y1_counts[b] += 1

    mi = 0.0
    for b in bin_counts:
        p_x = bin_counts[b] / total
        p_y1_given_x = bin_y1_counts.get(b, 0) / bin_counts[b] if bin_counts[b] > 0 else 0
        # MI = sum_{x,y} p(x,y) log( p(x,y) / (p(x)p(y)) )
        # p(x,y) = p(x) * p(y|x)
        if p_x == 0:
            continue
        for yi, p_y_given_x in [(1, p_y1_given_x), (0, 1-p_y1_given_x)]:
            p_y = p_y1 if yi == 1 else p_y0
            if p_y == 0 or p_y_given_x == 0:
                continue
            p_xy = p_x * p_y_given_x
            mi += p_xy * math.log(p_xy / (p_x * p_y))
    return max(0.0, mi)  # MI is non-negative

def run_feature_predictiveness_audit():
    trades = fetch_all_trades()
    if not trades:
        print("No closed trades found.")
        return

    # Group by symbol, mode, regime
    groups = defaultdict(list)
    for t in trades:
        regime = t.get("regime") or "UNKNOWN"
        groups[(t["symbol"], t["mode"], regime)].append(t)

    # For each group, compute average contribution per engine for winners vs losers,
    # and mutual information for continuous contributions.
    print("=" * 70)
    print("  FEATURE PREDICTIVENESS AUDIT")
    print("=" * 70)

    for (sym, md, regime), group_trades in sorted(groups.items()):
        if len(group_trades) < 20:
            continue
        engine_contribs = defaultdict(lambda: {"winner_vals": [], "loser_vals": []})
        for t in group_trades:
            contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
            is_win = t["win_loss"] == 1
            for eng in contribs:
                name = eng.get("engine") or eng.get("label") or "Unknown"
                val = eng.get("contribution", 0)
                if is_win:
                    engine_contribs[name]["winner_vals"].append(val)
                else:
                    engine_contribs[name]["loser_vals"].append(val)

        print(f"\n  Symbol: {sym}  Mode: {md}  Regime: {regime}  Trades: {len(group_trades)}")
        print(f"  {'Engine':25s} {'MI':>6s} {'Winner μ':>9s} {'Loser μ':>9s} {'Δ μ':>8s} {'WR if >0':>8s} {'WR if <0':>8s}")
        print(f"  {'-'*25} {'-'*6} {'-'*9} {'-'*9} {'-'*8} {'-'*8} {'-'*8}")

        # Sort by mutual information descending
        engine_mi = {}
        for eng, data in engine_contribs.items():
            all_vals = data["winner_vals"] + data["loser_vals"]
            outcomes = [1]*len(data["winner_vals"]) + [0]*len(data["loser_vals"])
            mi_val = mutual_information(all_vals, outcomes)
            engine_mi[eng] = mi_val

        sorted_engines = sorted(engine_mi.items(), key=lambda x: x[1], reverse=True)

        for eng, mi_val in sorted_engines:
            data = engine_contribs[eng]
            w_mean = sum(data["winner_vals"]) / len(data["winner_vals"]) if data["winner_vals"] else 0
            l_mean = sum(data["loser_vals"]) / len(data["loser_vals"]) if data["loser_vals"] else 0
            diff = w_mean - l_mean
            # Win rate when contribution > 0 vs < 0
            pos_wins = sum(1 for v in data["winner_vals"] if v > 0)
            pos_total = sum(1 for v in data["winner_vals"] + data["loser_vals"] if v > 0)
            pos_wr = pos_wins / pos_total * 100 if pos_total else 0
            neg_wins = sum(1 for v in data["winner_vals"] if v < 0)
            neg_total = sum(1 for v in data["winner_vals"] + data["loser_vals"] if v < 0)
            neg_wr = neg_wins / neg_total * 100 if neg_total else 0
            print(f"  {eng:25s} {mi_val:>6.4f} {w_mean:>+9.2f} {l_mean:>+9.2f} {diff:>+8.2f} {pos_wr:>7.1f}% {neg_wr:>7.1f}%")

    # Compute regime stability: do engines keep the same sign of predictiveness across regimes?
    # We'll collect engine-sign consistency across groups
    engine_signs = defaultdict(list)  # engine -> list of +1/-1 for each group where diff is computed
    for (sym, md, regime), group_trades in groups.items():
        if len(group_trades) < 20:
            continue
        for eng in engine_contribs:
            data = engine_contribs[eng]
            w_mean = sum(data["winner_vals"]) / len(data["winner_vals"]) if data["winner_vals"] else 0
            l_mean = sum(data["loser_vals"]) / len(data["loser_vals"]) if data["loser_vals"] else 0
            sign = 1 if w_mean > l_mean else -1 if w_mean < l_mean else 0
            engine_signs[eng].append(sign)

    print("\n  [REGIME STABILITY]")
    print(f"  {'Engine':25s} {'Stability':>10s}")
    print(f"  {'-'*25} {'-'*10}")
    for eng, signs in engine_signs.items():
        if len(signs) < 2:
            continue
        # stability = fraction of groups where sign equals the majority sign
        pos = sum(1 for s in signs if s == 1)
        neg = sum(1 for s in signs if s == -1)
        majority = max(pos, neg)
        stability = majority / len(signs) * 100
        print(f"  {eng:25s} {stability:>9.1f}%")

    # Final recommendation
    print("\n  [RECOMMENDATION]")
    print("  Engines with low MI and low |Δ μ| across all regimes may be candidates for removal.")
    print("  Engines with high regime stability (>80%) are safer to use in all market conditions.")
    print("=" * 70)
