# research/replay_explainability.py
import sqlite3
import json
from collections import Counter
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_decisions(run_id=None):
    conn = get_connection()
    if run_id:
        rows = conn.execute("SELECT * FROM score_log WHERE run_id = ?", (run_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM score_log").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def count_executed_trades(run_id=None):
    conn = get_connection()
    if run_id:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM trades WHERE run_id = ? AND entry_price IS NOT NULL",
            (run_id,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM trades WHERE entry_price IS NOT NULL"
        ).fetchone()
    conn.close()
    return row["cnt"]

def fixed_histogram(values, buckets):
    counts = {label: 0 for _, _, label in buckets}
    for v in values:
        for lo, hi, label in buckets:
            if lo <= v < hi:
                counts[label] += 1
                break
    return counts

def infer_rejection_stage(d):
    """
    Determine the rejection stage for a decision, even when
    the rejection_stage column is NULL (historical data).
    """
    stage = d.get("rejection_stage")
    if stage and stage != "UNKNOWN":
        return stage

    decision = d.get("decision", "")
    trade_uuid = d.get("trade_uuid")
    validator_approved = d.get("validator_approved")
    # Rejection reasons may be present
    reasons = d.get("rejection_reasons")

    # 1. If a trade was actually opened, stage is EXECUTED (NONE during recording)
    if trade_uuid:
        return "NONE"   # positive decision that led to a trade

    # 2. If decision was BUY/SELL but no trade_uuid -> execution blocked
    if decision in ("BUY", "SELL") and not trade_uuid:
        return "EXECUTION"

    # 3. If validator_approved is explicitly 0 -> VALIDATOR
    if validator_approved == 0:
        return "VALIDATOR"

    # 4. If decision is REJECT/WAIT and validator_approved is 1 (or unknown) -> MASTER_DECISION
    if decision in ("REJECT", "WAIT"):
        return "MASTER_DECISION"

    # 5. Fallback
    return "UNKNOWN"

def generate_explainability_report(run_id=None):
    decisions = fetch_decisions(run_id)
    total_candles = len(decisions)
    executed = count_executed_trades(run_id)

    # ---- Stage classification using robust inference ----
    stage_counts = Counter()
    for d in decisions:
        stage = infer_rejection_stage(d)
        stage_counts[stage] += 1

    # ---- Rejection reasons ----
    reasons_counter = Counter()
    for d in decisions:
        if d.get("rejection_reasons"):
            try:
                reasons = json.loads(d["rejection_reasons"])
            except:
                reasons = []
            for r in reasons:
                reasons_counter[r] += 1

    # ---- Fixed histograms ----
    brain_buckets = [(-1e9, 0, "<0"), (0,20,"0-20"), (20,40,"20-40"), (40,60,"40-60"),
                     (60,80,"60-80"), (80,101,"80-100")]
    comp_buckets = [(0,20,"0-20"), (20,40,"20-40"), (40,60,"40-60"), (60,80,"60-80"),
                    (80,101,"80-100")]

    all_brain = [d["brain_score"] for d in decisions if d["brain_score"] is not None]
    all_composite = [d["composite_score"] for d in decisions if d["composite_score"] is not None]
    brain_hist = fixed_histogram(all_brain, brain_buckets)
    comp_hist = fixed_histogram(all_composite, comp_buckets)

    # ---- Top rejection combinations ----
    combo_counter = Counter()
    for d in decisions:
        reasons = []
        if d.get("rejection_reasons"):
            try:
                reasons = json.loads(d["rejection_reasons"])
            except:
                reasons = []
        regime = d.get("regime")
        if regime:
            reasons.append(f"Regime: {regime}")
        combo = " + ".join(reasons) if reasons else "No reason"
        combo_counter[combo] += 1

    # ---- MTF diagnostics ----
    # Try to infer from mtf_loaded JSON; if empty, default 15m available, others missing
    mtf_status = {"15m": True, "1h": False, "4h": False, "1d": False}
    for d in decisions:
        mtf_str = d.get("mtf_loaded")
        if mtf_str:
            try:
                loaded = json.loads(mtf_str)
                if isinstance(loaded, dict):
                    for tf, available in loaded.items():
                        if tf in mtf_status:
                            mtf_status[tf] = available
                elif isinstance(loaded, list):
                    for tf in loaded:
                        if tf in mtf_status:
                            mtf_status[tf] = True
            except:
                pass
        if mtf_status["15m"] and mtf_status["1h"] and mtf_status["4h"] and mtf_status["1d"]:
            break   # early exit if all found

    # ---- Build report ----
    report = []
    report.append("=" * 70)
    report.append("  JAGUAR QUANT X – REPLAY EXPLAINABILITY REPORT")
    report.append("=" * 70)

    report.append("\n[1] REPLAY SUMMARY & CANDIDATE FUNNEL")
    report.append(f"  Candles Analysed          : {total_candles}")
    # validator approved count (from inference)
    validator_approved = sum(1 for d in decisions if d.get("validator_approved"))
    master_buy_sell = sum(1 for d in decisions if d.get("decision") in ("BUY", "SELL"))
    report.append(f"  Validator Approved        : {validator_approved}")
    report.append(f"  Master BUY/SELL           : {master_buy_sell}")
    report.append(f"  Executed Trades (trades)  : {executed}")

    report.append("\n  ---- Rejection Stage Breakdown ----")
    for stage in ["VALIDATOR", "MASTER_DECISION", "EXECUTION", "NONE", "UNKNOWN"]:
        cnt = stage_counts.get(stage, 0)
        pct = (cnt / total_candles * 100) if total_candles else 0
        report.append(f"  {stage:20s}: {cnt:5d} ({pct:.1f}%)")

    report.append("\n[2] TOP REJECTION REASONS (with percentage)")
    if reasons_counter:
        for reason, cnt in reasons_counter.most_common(15):
            pct = (cnt / total_candles * 100) if total_candles else 0
            report.append(f"  {reason:40s}: {cnt:5d} ({pct:.1f}%)")
    else:
        report.append("  No rejection reasons recorded (historical data)")

    report.append("\n[3] BRAIN SCORE DISTRIBUTION (all decisions)")
    for label, cnt in brain_hist.items():
        report.append(f"  {label:8s}: {cnt:5d}")

    report.append("\n[4] COMPOSITE SCORE DISTRIBUTION (all decisions)")
    for label, cnt in comp_hist.items():
        report.append(f"  {label:8s}: {cnt:5d}")

    # Average rejected scores (only for MASTER_DECISION & EXECUTION)
    rejected = [d for d in decisions if d.get("decision") in ("REJECT", "WAIT") or
                (d.get("decision") in ("BUY", "SELL") and not d.get("trade_uuid"))]
    if rejected:
        avg_brain_rej = sum(d["brain_score"] for d in rejected if d["brain_score"]) / len(rejected)
        avg_comp_rej = sum(d["composite_score"] for d in rejected if d["composite_score"]) / len(rejected)
        report.append(f"\n[5] REJECTED DECISION SCORES")
        report.append(f"  Average Brain Score    : {avg_brain_rej:.2f}")
        report.append(f"  Average Composite Score: {avg_comp_rej:.2f}")
        threshold_vals = [d["threshold_required_score"] for d in rejected if d.get("threshold_required_score")]
        if threshold_vals:
            avg_thresh = sum(threshold_vals)/len(threshold_vals)
            report.append(f"  Average Required Threshold: {avg_thresh:.2f}")

    report.append("\n[6] TOP REJECTION COMBINATIONS")
    for combo, cnt in combo_counter.most_common(10):
        pct = (cnt / total_candles * 100) if total_candles else 0
        report.append(f"  {combo:50s}: {cnt:5d} ({pct:.1f}%)")

    report.append("\n[7] MTF DATA AVAILABILITY")
    for tf in ["15m","1h","4h","1d"]:
        status = "Loaded" if mtf_status.get(tf, False) else "Missing"
        report.append(f"  {tf:4s}: {status}")

    report.append("\n" + "=" * 70)
    print("\n".join(report))
