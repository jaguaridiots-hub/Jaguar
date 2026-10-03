# research/engine_activation_audit.py
import json
import statistics
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_all_trades():
    """Fetch all closed trades with engine snapshots AND contributions."""
    conn = get_connection()
    query = """
        SELECT s.engine_snapshot_json, s.contributions_json
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _is_active_signal(value):
    """Return True if the engine signal is something other than NONE/NEUTRAL."""
    if value is None:
        return False
    if isinstance(value, str):
        return value.upper() not in ("NONE", "NEUTRAL", "")
    # If it's a dict or other, treat as active
    return True

def _normalize_name(name):
    """Merge legacy snapshot names into the canonical form used in contributions_json."""
    mapping = {
        "OrderFlow": "Order Flow",
        "VolumeProfile": "Volume Profile",
        "PremiumDiscount": "Premium/Discount",
    }
    return mapping.get(name, name)

def run_engine_activation_audit():
    trades = fetch_all_trades()
    if not trades:
        print("No closed trades found.")
        return

    total_trades = len(trades)

    # 1. Activation counts from raw snapshots
    activation_counts = defaultdict(int)
    for t in trades:
        snap = json.loads(t["engine_snapshot_json"]) if t["engine_snapshot_json"] else {}
        if isinstance(snap, dict):
            for eng_name, signal in snap.items():
                eng_name = _normalize_name(eng_name)          # merge legacy names
                if _is_active_signal(signal):
                    activation_counts[eng_name] += 1

    # 2. Numeric contributions from contributions_json
    engine_contribs = defaultdict(list)
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            val = eng.get("contribution", 0)
            engine_contribs[name].append(val)

    # 3. Dominance analysis
    dominance_counts = defaultdict(int)
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        contrib_map = {}
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib_map[name] = eng.get("contribution", 0)
        abs_vals = [(name, abs(val)) for name, val in contrib_map.items()]
        if abs_vals:
            max_eng = max(abs_vals, key=lambda x: x[1])[0]
            dominance_counts[max_eng] += 1
    total_dominance = sum(dominance_counts.values())

    # 4. Build engine list from both sources (normalised)
    all_engines = sorted(set(
        _normalize_name(e) for e in 
        list(activation_counts.keys()) + list(engine_contribs.keys())
    ))

    print("=" * 70)
    print("  ENGINE ACTIVATION AUDIT (CORRECTED)")
    print("=" * 70)
    print(f"  Total closed trades analysed : {total_trades}")
    print(f"  Engines found                : {len(all_engines)}")

    print(f"\n  Per‑Engine Activation Statistics:")
    print(f"  {'Engine':20s} {'Active%':>7s} {'Activ.':>6s} {'Mean':>8s} {'StDev':>7s} {'Unique':>6s} {'Classification':>18s}")
    print(f"  {'-'*20} {'-'*7} {'-'*6} {'-'*8} {'-'*7} {'-'*6} {'-'*18}")
    for eng in all_engines:
        activations = activation_counts.get(eng, 0)
        activation_pct = (activations / total_trades * 100) if total_trades else 0
        vals = engine_contribs.get(eng, [])
        mean_val = statistics.mean(vals) if vals else 0
        stdev_val = statistics.stdev(vals) if len(vals) >= 2 else 0
        unique_vals = len(set(vals))

        # Classification
        non_zero_contribs = [v for v in vals if v != 0]
        if activations == 0 and len(non_zero_contribs) == 0:
            classification = "NEVER TRIGGERED"
        elif activations == 0 and len(non_zero_contribs) > 0:
            classification = "CONSTANT OUTPUT (always same contribution)"
        elif len(non_zero_contribs) < 30:
            classification = "UNDERUTILIZED"
        else:
            classification = "ACTIVE"

        print(f"  {eng:20s} {activation_pct:>6.1f}% {activations:>6d} {mean_val:>+8.2f} {stdev_val:>7.2f} {unique_vals:>6d} {classification:>18s}")

    print(f"\n  Dominance Analysis (engine with highest |contribution| per trade):")
    for eng in all_engines:
        pct = (dominance_counts[eng] / total_dominance * 100) if total_dominance else 0
        print(f"  {eng:25s}: {pct:5.1f}% of trades")

    if total_dominance:
        top3 = sorted(dominance_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"\n  Top 3 engines that dominate the score: {', '.join(f'{eng} ({cnt/total_dominance*100:.1f}%)' for eng, cnt in top3)}")

    # Classification summary
    class_counts = defaultdict(int)
    for eng in all_engines:
        activations = activation_counts.get(eng, 0)
        vals = engine_contribs.get(eng, [])
        non_zero = [v for v in vals if v != 0]
        if activations == 0 and len(non_zero) == 0:
            class_counts["NEVER TRIGGERED"] += 1
        elif activations == 0 and len(non_zero) > 0:
            class_counts["CONSTANT OUTPUT"] += 1
        elif len(non_zero) < 30:
            class_counts["UNDERUTILIZED"] += 1
        else:
            class_counts["ACTIVE"] += 1

    print(f"\n  Classification Summary:")
    for cls in ["ACTIVE", "CONSTANT OUTPUT", "UNDERUTILIZED", "NEVER TRIGGERED"]:
        print(f"  {cls:20s}: {class_counts.get(cls, 0)}")

    never_trig = [eng for eng in all_engines if activation_counts.get(eng, 0) == 0 and len([v for v in engine_contribs.get(eng, []) if v != 0]) == 0]
    underutilized = [eng for eng in all_engines if activation_counts.get(eng, 0) > 0 and len([v for v in engine_contribs.get(eng, []) if v != 0]) < 30]

    print("\n  RECOMMENDATIONS:")
    if never_trig:
        print(f"  - Engines never triggered (always NONE/NEUTRAL): {', '.join(never_trig)}")
    if underutilized:
        print(f"  - Underutilized engines (<30 non‑zero contributions): {', '.join(underutilized)}. More data needed.")
    print("=" * 70)
