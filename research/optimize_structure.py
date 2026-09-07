# research/optimize_structure.py
import json
import math
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_structure_trades(symbol="GC=F", mode="SCALP"):
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
        SELECT t.win_loss, t.pnl, s.contributions_json, s.engine_snapshot_json
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL AND s.run_id = ?
    """, (run_id,)).fetchall()
    conn.close()
    return [dict(r) for r in trades], run_id

def _get_structure_signal(engine_snapshot_json):
    """
    Extract the Structure signal string from the engine snapshot.
    Returns a string like 'BULLISH', 'BEARISH', 'NONE', or None.
    """
    if not engine_snapshot_json:
        return None
    snap = json.loads(engine_snapshot_json)
    if isinstance(snap, dict):
        struct = snap.get("Structure")
        if isinstance(struct, str):
            return struct
        # maybe the whole snapshot IS the Structure output
        # check for presence of typical Structure keys
        if "signal" in snap:
            return snap["signal"]
    return None

def logistic(x):
    return 1.0 / (1.0 + math.exp(-x * 3))

# ---- Scoring models (now based on signal string + contribution) ----
def structure_score_current(contrib, signal):
    """Return the original contribution unchanged."""
    return contrib

def structure_score_weighted(signal, weights=None):
    """
    Map signal string to a numeric score.
    Weights dict: 'BULLISH' -> positive, 'BEARISH' -> negative.
    """
    w = weights or {"BULLISH": 70, "BEARISH": -70, "BUY": 80, "SELL": -80, "NONE": 0}
    return w.get(signal.upper() if signal else "NONE", 0)

def structure_score_nonlinear(signal):
    """Amplify strong signals, keep neutral unchanged."""
    base = structure_score_weighted(signal)
    if base > 0:
        return min(100, base * 1.2)
    elif base < 0:
        return max(-100, base * 0.8)
    return 0.0

def structure_score_staged(signal):
    """
    Binary: if signal is BULLISH or BUY -> +100,
    if BEARISH or SELL -> -100, else 0.
    """
    s = signal.upper() if signal else ""
    if s in ("BULLISH", "BUY"):
        return 100.0
    elif s in ("BEARISH", "SELL"):
        return -100.0
    else:
        return 0.0

# ---- Simulation ----
def simulate_model(trades, model_func, model_name, use_signal=False):
    """
    Apply the model to every trade and simulate acceptance with the
    experimental Brain's multipliers (Structure ×2, MSS ×2, etc.).
    """
    accepted = []
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []

        # Find original Structure contribution and signal
        orig_struct_contrib = 0.0
        signal = None
        if use_signal:
            raw_snap = t.get("engine_snapshot_json")
            signal = _get_structure_signal(raw_snap)

        for eng in contribs:
            name = eng.get("engine") or eng.get("label")
            if name == "Structure":
                orig_struct_contrib = eng.get("contribution", 0)
                break

        if model_func == structure_score_current:
            new_contrib = model_func(orig_struct_contrib, signal)
        else:
            new_contrib = model_func(signal)

        # Replace Structure contribution in the list
        new_contribs = []
        for eng in contribs:
            name = eng.get("engine") or eng.get("label")
            if name == "Structure":
                new_contribs.append({"engine": "Structure", "contribution": new_contrib})
            else:
                new_contribs.append(eng)

        total_contrib = 0.0
        multipliers = {
            "Structure": 2.0 if model_func != structure_score_current else 1.0,
            "MSS": 2.0,
            "Wyckoff": 2.0,
            "Volume Profile": 0.5,
            "Liquidity": 0.5,
        }
        for eng in new_contribs:
            name = eng.get("engine") or eng.get("label", "Unknown")
            contrib = eng.get("contribution", 0)
            mult = multipliers.get(name, 1.0)
            total_contrib += contrib * mult

        evidence = total_contrib / 100.0
        prob = logistic(evidence)
        if prob >= 0.55 and evidence > 0:
            accepted.append(t)

    if not accepted:
        return None, 0, 0, 0, 0, 0, 0

    total = len(accepted)
    wins = sum(1 for t in accepted if t["win_loss"] == 1)
    wr = wins / total * 100
    gp = sum(t["pnl"] for t in accepted if t["pnl"] and t["pnl"] > 0)
    gl = abs(sum(t["pnl"] for t in accepted if t["pnl"] and t["pnl"] < 0))
    pf = gp / gl if gl else float('inf')
    avg_win = gp / wins if wins else 0
    avg_loss = gl / (total - wins) if (total - wins) else 0
    expectancy = (wins/total * avg_win) - ((total-wins)/total * avg_loss)
    return accepted, total, wins, wr, pf, expectancy, None

# ---- Main ----
def run_optimize_structure(symbol="GC=F", mode="SCALP"):
    trades, run_id = fetch_structure_trades(symbol, mode)
    if not trades:
        print("No trades found.")
        return

    raw_available = all(t.get("engine_snapshot_json") for t in trades)
    print("=" * 70)
    print("  STRUCTURE ENGINE OPTIMIZATION")
    print("=" * 70)
    print(f"  Production campaign : {run_id}")
    print(f"  Raw Structure snapshots : {'available' if raw_available else 'not available'}")

    models = [
        ("Current (no change)", structure_score_current, False),
        ("Weighted (BULLISH=+70, BEARISH=-70)", structure_score_weighted, True),
        ("Weighted (BUY=+80, SELL=-80)", structure_score_weighted, True),
        ("Nonlinear (amplify)", structure_score_nonlinear, True),
        ("Staged (binary ±100)", structure_score_staged, True),
    ]

    print("\n  MODEL PERFORMANCE")
    print(f"  {'Model':35s} {'Trades':>7s} {'WinRate':>8s} {'PF':>7s} {'Expect':>8s}")
    print(f"  {'-'*35} {'-'*7} {'-'*8} {'-'*7} {'-'*8}")

    best_model = None
    best_pf = -1.0
    for name, func, use_signal in models:
        accepted, total, wins, wr, pf, exp, _ = simulate_model(trades, func, name, use_signal=use_signal)
        if accepted is None:
            print(f"  {name:35s} {'N/A':>7s}")
            continue
        print(f"  {name:35s} {total:>7d} {wr:>7.1f}% {pf:>7.3f} {exp:>+8.2f}")
        if pf > best_pf:
            best_pf = pf
            best_model = name

    print(f"\n  RECOMMENDED STRUCTURE MODEL: {best_model}")
    print("=" * 70)
