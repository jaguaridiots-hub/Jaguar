# research/trade_forensics.py
import sqlite3
import json
from datetime import datetime
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_trade_summary(trade_uuid):
    conn = get_connection()
    trade = conn.execute(
        "SELECT * FROM trades WHERE uuid = ?", (trade_uuid,)
    ).fetchone()
    conn.close()
    if not trade:
        return None
    return dict(trade)

def get_decision_context(trade_uuid):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM score_log WHERE trade_uuid = ?", (trade_uuid,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def get_all_trades_for_run(run_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT uuid FROM trades WHERE run_id = ? AND close_time IS NOT NULL", (run_id,)
    ).fetchall()
    conn.close()
    return [r["uuid"] for r in rows]

def get_latest_trade():
    conn = get_connection()
    row = conn.execute(
        "SELECT uuid FROM trades WHERE close_time IS NOT NULL ORDER BY open_time DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["uuid"] if row else None

def engine_contributions_sorted(context):
    contribs = context.get("contributions_json")
    if not contribs:
        return []
    try:
        items = json.loads(contribs)
    except:
        return []
    entries = []
    for eng in items:
        name = eng.get("engine") or eng.get("label") or "Unknown"
        contrib = eng.get("contribution", 0)
        entries.append((name, contrib))
    entries.sort(key=lambda x: x[1], reverse=True)
    return entries

def primary_drivers(contrib_sorted):
    positive = None
    negative = None
    if contrib_sorted and contrib_sorted[0][1] > 0:
        positive = contrib_sorted[0]
    if contrib_sorted and contrib_sorted[-1][1] < 0:
        negative = contrib_sorted[-1]
    return positive, negative

def generate_verdict(context, contrib_sorted, trade_result):
    if not contrib_sorted:
        return "No engine contribution data available."

    pos_driver, neg_driver = primary_drivers(contrib_sorted)
    outcome = "won" if trade_result == "WIN" else "lost"
    verdict_parts = [f"The trade {outcome}."]

    if pos_driver and neg_driver:
        verdict_parts.append(f"It was driven strongly by {pos_driver[0]} (+{pos_driver[1]:.1f})")
        verdict_parts.append(f"but faced significant headwinds from {neg_driver[0]} ({neg_driver[1]:.1f})")
        if trade_result == "WIN":
            verdict_parts.append("– the positive signal outweighed the negative, leading to a win.")
        else:
            verdict_parts.append("– the negative pressure overwhelmed the positive, contributing to the loss.")
        verdict_parts.append("Conflicting signals were present.")
    elif pos_driver:
        verdict_parts.append(f"It was driven strongly by {pos_driver[0]} (+{pos_driver[1]:.1f}) with no major negative signals.")
    elif neg_driver:
        verdict_parts.append(f"It was pulled down by {neg_driver[0]} ({neg_driver[1]:.1f}) without strong positive support.")
    else:
        verdict_parts.append("No significant directional engine contributions were present.")

    brain = context.get("brain_score")
    composite = context.get("composite_score")
    if brain is not None and composite is not None:
        verdict_parts.append(f"At decision time, the Brain Score was {brain:.1f} and Composite Score was {composite:.1f}.")
        if composite >= 70:
            verdict_parts.append("Confidence was high.")
        elif composite < 50:
            verdict_parts.append("Confidence was low.")

    return " ".join(verdict_parts)

def generate_suggestions(contrib_sorted, context):
    suggestions = []
    for name, contrib in contrib_sorted:
        if name == "Structure" and contrib < 0:
            suggestions.append("Wait for BOS (Break of Structure) confirmation before entry.")
        if name == "Premium/Discount" and contrib < 0:
            suggestions.append("Avoid trades in Premium zone unless strong reversal signals exist.")
        if name == "Volume Profile" and contrib < 0:
            suggestions.append("Wait for higher Volume Profile score (price near value area).")
        if name == "Liquidity" and contrib < 0:
            suggestions.append("Look for liquidity sweeps or order block confirmations.")
        if name == "Order Flow" and contrib < 0:
            suggestions.append("Require stronger Order Flow signals (delta, pressure).")
        if name == "Equal Levels" and contrib < 0:
            suggestions.append("Avoid trading near Equal Highs/Lows (potential liquidity grab).")
    regime = context.get("regime")
    if regime == "COMPRESSION":
        suggestions.append("Compression regime often leads to breakouts; use breakout entry rules.")
    if not suggestions:
        suggestions.append("All engine contributions were positive. Consider tighter risk management to maximize gains.")
    unique = []
    for s in suggestions:
        if s not in unique:
            unique.append(s)
    return unique

def print_trade_forensics(trade_uuid):
    trade = get_trade_summary(trade_uuid)
    if not trade:
        print(f"Trade {trade_uuid} not found.")
        return

    context = get_decision_context(trade_uuid)
    if not context:
        print("No decision context found for this trade (likely not linked to score_log).")
        return

    contrib_sorted = engine_contributions_sorted(context)
    pos_driver, neg_driver = primary_drivers(contrib_sorted)

    direction = context.get("decision", "?")
    trade_result = "WIN" if trade["win_loss"] == 1 else "LOSS"

    print("\n" + "=" * 70)
    print(f"  TRADE FORENSICS REPORT – {trade_uuid[:8]}...")
    print("=" * 70)

    print("\n[1] TRADE SUMMARY")
    print(f"  Run ID      : {context.get('run_id', 'N/A')}")
    print(f"  Trade ID    : {trade_uuid}")
    print(f"  Symbol      : {trade['symbol']}")
    print(f"  Timeframe   : {trade['timeframe']}")
    print(f"  Direction   : {direction}")
    print(f"  Entry       : {trade['entry_price']}")
    print(f"  Exit        : {trade['exit_price']}")
    print(f"  PnL         : {trade['pnl']:.2f}")
    print(f"  Result      : {trade_result}")

    print("\n[2] DECISION CONTEXT")
    print(f"  Brain Score       : {context.get('brain_score', 'N/A')}")
    print(f"  Composite Score   : {context.get('composite_score', 'N/A')}")
    print(f"  Market Regime     : {context.get('regime', 'N/A')}")
    print(f"  Session Score     : {context.get('session_score', 'N/A')}")
    print(f"  Probability Score : {trade.get('probability_score', 'N/A')}")
    print(f"  Confidence        : {trade.get('confidence', 'N/A')}")

    print("\n[3] ENGINE CONTRIBUTIONS")
    for name, contrib in contrib_sorted:
        print(f"  {name:25s}: {contrib:+.2f}")

    print("\n[4] ROOT CAUSE ANALYSIS")
    if pos_driver:
        print(f"  Primary Positive Driver : {pos_driver[0]} ({pos_driver[1]:+.2f})")
    else:
        print("  No positive driver identified.")
    if neg_driver:
        print(f"  Primary Negative Driver : {neg_driver[0]} ({neg_driver[1]:+.2f})")
    else:
        print("  No negative driver identified.")

    verdict = generate_verdict(context, contrib_sorted, trade_result)
    print("\n[5] EXPLAINABLE VERDICT")
    print(f"  {verdict}")

    suggestions = generate_suggestions(contrib_sorted, context)
    print("\n[6] IMPROVEMENT SUGGESTIONS")
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
    else:
        print("  None derived from current data.")

    print("\n" + "=" * 70)

def run_trade_forensics(args):
    if "--trade-id" in args:
        idx = args.index("--trade-id")
        if idx + 1 < len(args):
            trade_id = args[idx + 1]
            print_trade_forensics(trade_id)
            return
    if "--last" in args:
        trade_id = get_latest_trade()
        if not trade_id:
            print("No closed trades found.")
            return
        print_trade_forensics(trade_id)
        return
    if "--run-id" in args:
        idx = args.index("--run-id")
        if idx + 1 < len(args):
            run_id = args[idx + 1]
            trade_ids = get_all_trades_for_run(run_id)
            if not trade_ids:
                print(f"No closed trades found for run {run_id}.")
                return
            for tid in trade_ids:
                print_trade_forensics(tid)
            return
    print("Usage: python jaguar.py --trade-forensics [--trade-id <uuid> | --last | --run-id <run_id>]")
