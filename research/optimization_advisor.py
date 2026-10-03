# research/optimization_advisor.py
import sqlite3
import json
from .database import DB_PATH
from .statistical_validator import (
    format_engine_recommendation,
    format_category_recommendation,
    generate_global_summary,
    confidence_level,
)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _fetch_trades_with_contributions():
    conn = get_connection()
    query = """
        SELECT t.win_loss, t.symbol, t.timeframe, t.mode,
               s.brain_score, s.composite_score, s.regime,
               s.contributions_json
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows

def engine_contribution_analysis(trades):
    engine_stats = {}
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        outcome = "WIN" if t["win_loss"] == 1 else "LOSS"
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib = eng.get("contribution", 0)
            if name not in engine_stats:
                engine_stats[name] = {
                    "pos_wins": 0, "pos_total": 0,
                    "neg_wins": 0, "neg_total": 0,
                    "all_contrib": []
                }
            engine_stats[name]["all_contrib"].append(contrib)
            if contrib > 0:
                engine_stats[name]["pos_total"] += 1
                if outcome == "WIN":
                    engine_stats[name]["pos_wins"] += 1
            elif contrib < 0:
                engine_stats[name]["neg_total"] += 1
                if outcome == "WIN":
                    engine_stats[name]["neg_wins"] += 1

    recommendations = []
    for eng, stats in engine_stats.items():
        pos_total = stats["pos_total"]
        neg_total = stats["neg_total"]
        avg_contrib = sum(stats["all_contrib"]) / len(stats["all_contrib"]) if stats["all_contrib"] else 0
        if pos_total < 20 or neg_total < 20:
            continue
        formatted, conf, sample, diff = format_engine_recommendation(
            eng, pos_total, stats["pos_wins"], neg_total, stats["neg_wins"], avg_contrib
        )
        recommendations.append((formatted, conf, sample, diff, "engine"))
    return engine_stats, recommendations

def score_range_analysis(trades):
    brain_buckets = {"0-20": [0,20], "20-40": [20,40], "40-60": [40,60], "60-80": [60,80], "80-100": [80,100]}
    comp_buckets = {"0-20": [0,20], "20-40": [20,40], "40-60": [40,60], "60-80": [60,80], "80-100": [80,100]}

    def bucket_score(score, buckets):
        for name, (lo, hi) in buckets.items():
            if lo <= score < hi:
                return name
        return "out"

    brain_data = {}
    comp_data = {}
    for t in trades:
        bs = t["brain_score"]
        cs = t["composite_score"]
        outcome = 1 if t["win_loss"] == 1 else 0
        if bs is not None:
            bucket = bucket_score(bs, brain_buckets)
            brain_data.setdefault(bucket, {"trades":0, "wins":0})
            brain_data[bucket]["trades"] += 1
            brain_data[bucket]["wins"] += outcome
        if cs is not None:
            bucket = bucket_score(cs, comp_buckets)
            comp_data.setdefault(bucket, {"trades":0, "wins":0})
            comp_data[bucket]["trades"] += 1
            comp_data[bucket]["wins"] += outcome

    recs = []
    for bname, data in brain_data.items():
        if data["trades"] < 20:
            continue
        formatted, conf, sample, wr = format_category_recommendation(
            "Brain Score Range", bname, data["trades"], data["wins"]
        )
        recs.append((formatted, conf, sample, wr, "brain_score"))
    for bname, data in comp_data.items():
        if data["trades"] < 20:
            continue
        formatted, conf, sample, wr = format_category_recommendation(
            "Composite Score Range", bname, data["trades"], data["wins"]
        )
        recs.append((formatted, conf, sample, wr, "comp_score"))
    return recs

def regime_analysis(trades):
    regimes = {}
    for t in trades:
        regime = t["regime"] or "UNKNOWN"
        regimes.setdefault(regime, {"trades":0, "wins":0})
        regimes[regime]["trades"] += 1
        if t["win_loss"] == 1:
            regimes[regime]["wins"] += 1
    recs = []
    for regime, data in regimes.items():
        if data["trades"] < 20:
            continue
        formatted, conf, sample, wr = format_category_recommendation(
            "Regime", regime, data["trades"], data["wins"]
        )
        recs.append((formatted, conf, sample, wr, "regime"))
    return recs

def symbol_analysis(trades):
    symbols = {}
    for t in trades:
        sym = t["symbol"]
        symbols.setdefault(sym, {"trades":0, "wins":0})
        symbols[sym]["trades"] += 1
        if t["win_loss"] == 1:
            symbols[sym]["wins"] += 1
    recs = []
    for sym, data in symbols.items():
        if data["trades"] < 20:
            continue
        formatted, conf, sample, wr = format_category_recommendation(
            "Symbol", sym, data["trades"], data["wins"]
        )
        recs.append((formatted, conf, sample, wr, "symbol"))
    return recs

def timeframe_analysis(trades):
    tfs = {}
    for t in trades:
        tf = t["timeframe"]
        tfs.setdefault(tf, {"trades":0, "wins":0})
        tfs[tf]["trades"] += 1
        if t["win_loss"] == 1:
            tfs[tf]["wins"] += 1
    recs = []
    for tf, data in tfs.items():
        if data["trades"] < 20:
            continue
        formatted, conf, sample, wr = format_category_recommendation(
            "Timeframe", tf, data["trades"], data["wins"]
        )
        recs.append((formatted, conf, sample, wr, "timeframe"))
    return recs

def loss_pattern_analysis(trades):
    combos = {}
    for t in trades:
        regime = t["regime"] or "UNKNOWN"
        sym = t["symbol"]
        key = f"{sym} in {regime}"
        combos.setdefault(key, {"trades":0, "losses":0})
        combos[key]["trades"] += 1
        if t["win_loss"] == 0:
            combos[key]["losses"] += 1
    recs = []
    for combo, data in combos.items():
        if data["trades"] < 20:
            continue
        losses = data["losses"]
        wins = data["trades"] - losses
        loss_rate = (losses / data["trades"] * 100) if data["trades"] > 0 else 0
        if loss_rate > 70:
            formatted, conf, sample, _ = format_category_recommendation(
                "Combination", combo, data["trades"], wins
            )
            formatted = formatted.replace("Performance is acceptable.",
                                        f"Recommendation: Avoid this combination (Loss Rate {loss_rate:.1f}%)")
            recs.append((formatted, conf, sample, loss_rate, "pattern"))
    return recs

def mode_comparison_analysis():
    """Compare SCALP, SWING, CLASSIC using all closed trades."""
    conn = get_connection()
    rows = conn.execute("SELECT mode, win_loss, pnl FROM trades WHERE close_time IS NOT NULL").fetchall()
    conn.close()
    modes = {}
    for r in rows:
        md = r["mode"] or "unknown"
        if md not in modes:
            modes[md] = {"trades": 0, "wins": 0, "gross_profit": 0.0, "gross_loss": 0.0}
        modes[md]["trades"] += 1
        if r["win_loss"] == 1:
            modes[md]["wins"] += 1
        pnl = r["pnl"] or 0.0
        if pnl > 0:
            modes[md]["gross_profit"] += pnl
        else:
            modes[md]["gross_loss"] += abs(pnl)

    print("\n[7] MODE COMPARISON (SCALP vs SWING vs CLASSIC)")
    best_mode = None
    best_expectancy = -float('inf')
    recommendations = []
    for md, data in modes.items():
        total = data["trades"]
        wins = data["wins"]
        if total < 20:
            continue
        pf = data["gross_profit"] / data["gross_loss"] if data["gross_loss"] else float('inf')
        avg_win = data["gross_profit"] / wins if wins else 0
        avg_loss = data["gross_loss"] / (total - wins) if (total - wins) else 0
        expectancy = (wins/total)*avg_win - ((total-wins)/total)*avg_loss
        wr = (wins/total*100)
        conf = confidence_level(total)
        recommendations.append((md, {
            "trades": total, "wins": wins, "win_rate": wr,
            "profit_factor": pf, "expectancy": expectancy, "confidence": conf
        }))
        if expectancy > best_expectancy:
            best_expectancy = expectancy
            best_mode = md

    if not recommendations:
        print("  Insufficient data to compare modes (need ≥20 trades per mode).")
        return

    recommendations.sort(key=lambda x: x[1]["expectancy"], reverse=True)
    for mode, data in recommendations:
        print(f"  {mode:8s}: Trades {data['trades']:4d} | WR {data['win_rate']:.1f}% | PF {data['profit_factor']:.2f} | Expect {data['expectancy']:.2f} | Confidence: {data['confidence'].value}")
    if best_mode:
        print(f"\n  Best Mode Overall: {best_mode} (highest expectancy)")

def print_optimization_report():
    trades = _fetch_trades_with_contributions()
    if not trades:
        print("No closed trades found. Run a research campaign first.")
        return

    print("=" * 70)
    print("  JAGUAR QUANT X – EVIDENCE‑BASED OPTIMIZATION ADVISOR")
    print("=" * 70)
    print(generate_global_summary(trades))

    all_recs = []

    engine_stats, engine_recs = engine_contribution_analysis(trades)
    all_recs.extend(engine_recs)

    score_recs = score_range_analysis(trades)
    all_recs.extend(score_recs)

    regime_recs = regime_analysis(trades)
    all_recs.extend(regime_recs)

    symbol_recs = symbol_analysis(trades)
    all_recs.extend(symbol_recs)

    tf_recs = timeframe_analysis(trades)
    all_recs.extend(tf_recs)

    pattern_recs = loss_pattern_analysis(trades)
    all_recs.extend(pattern_recs)

    if all_recs:
        confidence_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        all_recs.sort(key=lambda r: (
            confidence_order.get(r[1].value if hasattr(r[1], 'value') else r[1], 2),
            -r[2],
            -r[3] if isinstance(r[3], (int, float)) else 0
        ))

        print("\n  RANKED RECOMMENDATIONS (by evidence strength)")
        for i, rec in enumerate(all_recs, 1):
            print(f"\n  [{i}]")
            print(rec[0])
    else:
        print("\n  No recommendations met the minimum sample size (≥20).")

    # Mode comparison always shown if data exists
    mode_comparison_analysis()

    print("\n" + "=" * 70)
    print("  All recommendations are evidence‑based and statistically validated.")
    print("  No automatic changes have been applied.")
