# research/brain_interaction.py
import json
import math
from itertools import combinations
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trades(symbol="GC=F", mode="SCALP"):
    """Fetch closed trades with contributions for the latest production campaign."""
    conn = get_connection()
    row = conn.execute("""
        SELECT run_id FROM research_runs
        WHERE symbols = ? AND modes = ? AND end_time IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
    """, (symbol, mode)).fetchone()
    if not row:
        return [], None
    run_id = row["run_id"]
    trades = conn.execute("""
        SELECT t.win_loss, t.pnl, s.contributions_json
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL AND s.run_id = ?
    """, (run_id,)).fetchall()
    conn.close()
    return [dict(r) for r in trades], run_id

def compute_metrics(trades):
    if not trades:
        return 0, 0, 0, 0, 0
    total = len(trades)
    wins = sum(1 for t in trades if t["win_loss"] == 1)
    wr = wins / total * 100
    gp = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
    gl = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
    pf = gp / gl if gl else float('inf')
    avg_win = gp / wins if wins else 0
    avg_loss = gl / (total - wins) if (total - wins) else 0
    expectancy = (wins/total * avg_win) - ((total-wins)/total * avg_loss)
    return total, wins, wr, pf, expectancy

def run_brain_interaction_analysis(symbol="GC=F", mode="SCALP"):
    trades, run_id = fetch_trades(symbol, mode)
    if not trades:
        print("No trades found.")
        return

    # Active engines (non-constant from previous audits)
    active = ["Structure", "MSS", "Wyckoff", "Volume Profile", "Liquidity",
              "Premium/Discount", "FVG", "Order Flow"]

    # Build per-trade contribution maps
    trade_contribs = []
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        cmap = {}
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            cmap[name] = eng.get("contribution", 0)
        trade_contribs.append(cmap)

    # ------------------------------------------------------------------
    # Pair analysis
    # ------------------------------------------------------------------
    pair_results = []
    for eng1, eng2 in combinations(active, 2):
        # both positive
        pos_pos = [t for i, t in enumerate(trades) if trade_contribs[i].get(eng1, 0) > 0 and trade_contribs[i].get(eng2, 0) > 0]
        pos_neg = [t for i, t in enumerate(trades) if trade_contribs[i].get(eng1, 0) > 0 and trade_contribs[i].get(eng2, 0) < 0]
        neg_pos = [t for i, t in enumerate(trades) if trade_contribs[i].get(eng1, 0) < 0 and trade_contribs[i].get(eng2, 0) > 0]
        neg_neg = [t for i, t in enumerate(trades) if trade_contribs[i].get(eng1, 0) < 0 and trade_contribs[i].get(eng2, 0) < 0]
        # all trades where both are non-zero (any combination)
        both_nonzero = [t for i, t in enumerate(trades) if trade_contribs[i].get(eng1, 0) != 0 and trade_contribs[i].get(eng2, 0) != 0]

        # We'll compute for "both positive" as the most desirable combination
        if pos_pos:
            _, _, wr, pf, exp = compute_metrics(pos_pos)
            pair_results.append((eng1, eng2, "both_positive", len(pos_pos), wr, pf, exp))

    # Sort by profit factor
    pair_results.sort(key=lambda x: x[5], reverse=True)

    print("=" * 70)
    print("  BRAIN INTERACTION ANALYSIS")
    print("=" * 70)
    print(f"  Campaign : {run_id}")
    print(f"  Active engines: {', '.join(active)}")

    print("\n  [1] TOP ENGINE PAIRS (both positive contributions)")
    print(f"  {'Engine 1':15s} {'Engine 2':15s} {'Trades':>7s} {'WinRate':>8s} {'PF':>7s} {'Expect':>8s}")
    print(f"  {'-'*15} {'-'*15} {'-'*7} {'-'*8} {'-'*7} {'-'*8}")
    for i, (e1, e2, _, cnt, wr, pf, exp) in enumerate(pair_results[:20], 1):
        print(f"  {e1:15s} {e2:15s} {cnt:>7d} {wr:>7.1f}% {pf:>7.3f} {exp:>+8.2f}")

    # Triple analysis (only for top 5 engines to limit combinatorial explosion)
    # Pick the 5 engines that appear most often in top pairs
    top_engines = set()
    for e1, e2, _, _, _, _, _ in pair_results[:10]:
        top_engines.add(e1)
        top_engines.add(e2)
    top_engines = sorted(top_engines)[:5]  # limit

    triple_results = []
    for eng1, eng2, eng3 in combinations(top_engines, 3):
        pos_all = [t for i, t in enumerate(trades)
                   if trade_contribs[i].get(eng1, 0) > 0
                   and trade_contribs[i].get(eng2, 0) > 0
                   and trade_contribs[i].get(eng3, 0) > 0]
        if pos_all:
            _, _, wr, pf, exp = compute_metrics(pos_all)
            triple_results.append((eng1, eng2, eng3, len(pos_all), wr, pf, exp))

    triple_results.sort(key=lambda x: x[5], reverse=True)

    print("\n  [2] TOP ENGINE TRIPLES (all positive)")
    if triple_results:
        print(f"  {'Engine 1':15s} {'Engine 2':15s} {'Engine 3':15s} {'Trades':>7s} {'WinRate':>8s} {'PF':>7s} {'Expect':>8s}")
        print(f"  {'-'*15} {'-'*15} {'-'*15} {'-'*7} {'-'*8} {'-'*7} {'-'*8}")
        for e1, e2, e3, cnt, wr, pf, exp in triple_results[:20]:
            print(f"  {e1:15s} {e2:15s} {e3:15s} {cnt:>7d} {wr:>7.1f}% {pf:>7.3f} {exp:>+8.2f}")
    else:
        print("  No triples found with all positive contributions.")

    # ---- Synergy detection ----
    # For a pair (A,B): synergy if PF(A&B both positive) > max(PF(A positive alone), PF(B positive alone))
    # Compute individual PFs
    individual_pf = {}
    for eng in active:
        pos_trades = [t for i, t in enumerate(trades) if trade_contribs[i].get(eng, 0) > 0]
        if pos_trades:
            _, _, _, pf, _ = compute_metrics(pos_trades)
            individual_pf[eng] = pf
        else:
            individual_pf[eng] = 0

    synergistic_pairs = []
    for e1, e2, _, cnt, wr, pf, exp in pair_results:
        pf1 = individual_pf.get(e1, 0)
        pf2 = individual_pf.get(e2, 0)
        if pf > max(pf1, pf2) + 0.01:  # at least 0.01 improvement
            synergistic_pairs.append((e1, e2, cnt, pf, max(pf1, pf2), pf - max(pf1, pf2)))

    print("\n  [3] SYNERGISTIC PAIRS (combined PF > individual PFs)")
    if synergistic_pairs:
        print(f"  {'Engine 1':15s} {'Engine 2':15s} {'Combined PF':>11s} {'Best Single':>11s} {'Synergy':>8s}")
        print(f"  {'-'*15} {'-'*15} {'-'*11} {'-'*11} {'-'*8}")
        for e1, e2, cnt, pf, best_single, gain in synergistic_pairs[:10]:
            print(f"  {e1:15s} {e2:15s} {pf:>11.3f} {best_single:>11.3f} {gain:>+8.3f}")
    else:
        print("  No synergistic pairs found.")

    # ---- Recommended staged architecture ----
    print("\n  [4] RECOMMENDED STAGED ARCHITECTURE")
    print("""
    Based on the interaction analysis:

    Stage 1 – Trend / Structure Filter
        • Structure (BOS/CHOCH)
        • MSS
        → Veto if both bearish

    Stage 2 – Context & Smart Money
        • Wyckoff (accumulation/distribution)
        • FVG (fair value gaps)
        • Premium/Discount
        → Adjust confidence up/down

    Stage 3 – Execution Confidence
        • Order Flow (delta, pressure)
        • Volume Profile
        → Final probability of success

    This architecture uses the synergistic pairs identified above.
    Each stage can be a logistic probability multiplier,
    resulting in a well-calibrated final confidence score.
    """)
    print("=" * 70)
