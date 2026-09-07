# research/research_report.py
import sqlite3
import json
from datetime import datetime
from math import sqrt
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _run_id_filter(run_id=None):
    if run_id:
        return "AND run_id = ?", (run_id,)
    return "", ()

def _closed_trades_where(run_id=None):
    clause, params = _run_id_filter(run_id)
    base = "close_time IS NOT NULL"
    if clause:
        return f"WHERE {base} {clause}", params
    return f"WHERE {base}", ()

# ----------------------------------------------------------------------
# 1. Overall Performance
# ----------------------------------------------------------------------
def overall_performance(run_id=None):
    where, params = _closed_trades_where(run_id)
    conn = get_connection()
    trades = conn.execute(
        f"SELECT win_loss, pnl, r_multiple, holding_time, open_time, exit_price FROM trades {where} ORDER BY open_time",
        params
    ).fetchall()
    conn.close()

    total = len(trades)
    wins = sum(1 for t in trades if t["win_loss"] == 1)
    losses = total - wins
    win_rate = (wins / total * 100) if total else 0

    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss else float('inf')

    avg_holding = sum(t["holding_time"] for t in trades if t["holding_time"]) / total if total else 0
    avg_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None) / total if total else 0

    avg_win = gross_profit / wins if wins else 0
    avg_loss = gross_loss / losses if losses else 0
    win_pct = wins / total if total else 0
    loss_pct = losses / total if total else 0
    expectancy = (win_pct * avg_win) - (loss_pct * avg_loss)

    peak = -float('inf')
    max_dd = 0
    cumulative_pnl = 0
    for t in trades:
        cumulative_pnl += (t["pnl"] or 0)
        if cumulative_pnl > peak:
            peak = cumulative_pnl
        else:
            dd = peak - cumulative_pnl
            if dd > max_dd:
                max_dd = dd

    max_con_wins = max_con_losses = cur_wins = cur_losses = 0
    for t in trades:
        if t["win_loss"] == 1:
            cur_wins += 1
            cur_losses = 0
            max_con_wins = max(max_con_wins, cur_wins)
        else:
            cur_losses += 1
            cur_wins = 0
            max_con_losses = max(max_con_losses, cur_losses)

    return {
        "total": total, "wins": wins, "losses": losses,
        "win_rate": win_rate, "profit_factor": profit_factor,
        "avg_holding_seconds": avg_holding,
        "avg_r_multiple": avg_r,
        "expectancy": expectancy,
        "max_drawdown": max_dd,
        "peak_cumulative_pnl": peak,
        "max_consecutive_wins": max_con_wins,
        "max_consecutive_losses": max_con_losses
    }

# ----------------------------------------------------------------------
# 2. Brain Score Buckets
# ----------------------------------------------------------------------
def brain_score_buckets(run_id=None):
    clause, params = _run_id_filter(run_id)
    query = f"""
        SELECT s.brain_score, t.win_loss
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE t.close_time IS NOT NULL {clause}
    """
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    buckets = {"0-20":[], "20-40":[], "40-60":[], "60-80":[], "80-100":[]}
    for r in rows:
        score = r["brain_score"] or 0
        if score < 20: bucket = "0-20"
        elif score < 40: bucket = "20-40"
        elif score < 60: bucket = "40-60"
        elif score < 80: bucket = "60-80"
        else: bucket = "80-100"
        buckets[bucket].append("WIN" if r["win_loss"] == 1 else "LOSS")
    result = {}
    for b, outcomes in buckets.items():
        total = len(outcomes)
        wins = outcomes.count("WIN")
        result[b] = {"trades": total, "wins": wins, "win_rate": (wins/total*100) if total else 0}
    return result

# ----------------------------------------------------------------------
# 3. Composite Score Buckets
# ----------------------------------------------------------------------
def composite_score_buckets(run_id=None):
    clause, params = _run_id_filter(run_id)
    query = f"""
        SELECT s.composite_score, t.win_loss
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE t.close_time IS NOT NULL {clause}
    """
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    buckets = {"0-20":[], "20-40":[], "40-60":[], "60-80":[], "80-100":[]}
    for r in rows:
        score = r["composite_score"] or 0
        if score < 20: bucket = "0-20"
        elif score < 40: bucket = "20-40"
        elif score < 60: bucket = "40-60"
        elif score < 80: bucket = "60-80"
        else: bucket = "80-100"
        buckets[bucket].append("WIN" if r["win_loss"] == 1 else "LOSS")
    result = {}
    for b, outcomes in buckets.items():
        total = len(outcomes)
        wins = outcomes.count("WIN")
        result[b] = {"trades": total, "wins": wins, "win_rate": (wins/total*100) if total else 0}
    return result

# ----------------------------------------------------------------------
# 4. Engine Attribution (same as before, not repeated for brevity)
# ----------------------------------------------------------------------
def engine_attribution(run_id=None):
    clause, params = _run_id_filter(run_id)
    query = f"""
        SELECT s.contributions_json, t.win_loss
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE t.close_time IS NOT NULL {clause}
    """
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    engine_totals = {}
    engine_counts = {}
    engine_pos_wins = {}
    engine_pos_total = {}
    for r in rows:
        contribs = json.loads(r["contributions_json"]) if r["contributions_json"] else []
        outcome = "WIN" if r["win_loss"] == 1 else "LOSS"
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib = eng.get("contribution", 0)
            engine_totals[name] = engine_totals.get(name, 0) + contrib
            engine_counts[name] = engine_counts.get(name, 0) + 1
            if contrib > 0:
                engine_pos_total[name] = engine_pos_total.get(name, 0) + 1
                if outcome == "WIN":
                    engine_pos_wins[name] = engine_pos_wins.get(name, 0) + 1
    result = {}
    for name in engine_totals:
        avg = engine_totals[name] / engine_counts[name] if engine_counts[name] else 0
        pos_total = engine_pos_total.get(name, 0)
        pos_wins = engine_pos_wins.get(name, 0)
        pos_winrate = (pos_wins/pos_total*100) if pos_total else 0
        result[name] = {
            "avg_contribution": avg,
            "positive_win_rate": pos_winrate,
            "occurrences": engine_counts[name],
            "total_contribution": engine_totals[name]
        }
    return dict(sorted(result.items(), key=lambda x: abs(x[1]["avg_contribution"]), reverse=True))

# ----------------------------------------------------------------------
# 5. Market Regime
# ----------------------------------------------------------------------
def regime_analysis(run_id=None):
    clause, params = _run_id_filter(run_id)
    query = f"""
        SELECT s.regime, t.win_loss
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE t.close_time IS NOT NULL AND s.regime IS NOT NULL {clause}
    """
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    regimes = {}
    for r in rows:
        reg = r["regime"]
        if reg not in regimes:
            regimes[reg] = {"trades":0, "wins":0}
        regimes[reg]["trades"] += 1
        if r["win_loss"] == 1:
            regimes[reg]["wins"] += 1
    for reg in regimes:
        total = regimes[reg]["trades"]
        regimes[reg]["win_rate"] = (regimes[reg]["wins"]/total*100) if total else 0
    return regimes

# ----------------------------------------------------------------------
# 6. Session
# ----------------------------------------------------------------------
def session_analysis(run_id=None):
    clause, params = _run_id_filter(run_id)
    query = f"""
        SELECT s.timestamp, t.win_loss
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE t.close_time IS NOT NULL AND s.timestamp IS NOT NULL {clause}
    """
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    sessions = {"Asia": {"trades":0, "wins":0}, "London": {"trades":0, "wins":0},
                "New York": {"trades":0, "wins":0}, "Overlap": {"trades":0, "wins":0}}
    for r in rows:
        try:
            dt = datetime.fromisoformat(r["timestamp"])
            hour = dt.hour
            if 0 <= hour < 7: sess = "Asia"
            elif 7 <= hour < 12: sess = "London"
            elif 12 <= hour < 16: sess = "Overlap"
            elif 16 <= hour < 21: sess = "New York"
            else: sess = "Asia"
            sessions[sess]["trades"] += 1
            if r["win_loss"] == 1:
                sessions[sess]["wins"] += 1
        except:
            pass
    for s in sessions:
        total = sessions[s]["trades"]
        sessions[s]["win_rate"] = (sessions[s]["wins"]/total*100) if total else 0
    return sessions

# ----------------------------------------------------------------------
# 7. Symbol
# ----------------------------------------------------------------------
def symbol_analysis(run_id=None):
    where, params = _closed_trades_where(run_id)
    conn = get_connection()
    rows = conn.execute(f"SELECT symbol, win_loss FROM trades {where}", params).fetchall()
    conn.close()
    syms = {}
    for r in rows:
        sym = r["symbol"]
        if sym not in syms:
            syms[sym] = {"trades":0, "wins":0}
        syms[sym]["trades"] += 1
        if r["win_loss"] == 1:
            syms[sym]["wins"] += 1
    for s in syms:
        total = syms[s]["trades"]
        syms[s]["win_rate"] = (syms[s]["wins"]/total*100) if total else 0
    return syms

# ----------------------------------------------------------------------
# 8. Timeframe
# ----------------------------------------------------------------------
def timeframe_analysis(run_id=None):
    where, params = _closed_trades_where(run_id)
    conn = get_connection()
    rows = conn.execute(f"SELECT timeframe, win_loss FROM trades {where}", params).fetchall()
    conn.close()
    tfs = {}
    for r in rows:
        tf = r["timeframe"]
        if tf not in tfs:
            tfs[tf] = {"trades":0, "wins":0}
        tfs[tf]["trades"] += 1
        if r["win_loss"] == 1:
            tfs[tf]["wins"] += 1
    for t in tfs:
        total = tfs[t]["trades"]
        tfs[t]["win_rate"] = (tfs[t]["wins"]/total*100) if total else 0
    return tfs

# ----------------------------------------------------------------------
# 9. Score Calibration
# ----------------------------------------------------------------------
def score_calibration(run_id=None):
    clause, params = _run_id_filter(run_id)
    query = f"""
        SELECT s.brain_score, s.composite_score, t.win_loss
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE t.close_time IS NOT NULL {clause}
    """
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    brain_wins = []
    brain_losses = []
    comp_wins = []
    comp_losses = []
    all_scores = []
    for r in rows:
        outcome = "WIN" if r["win_loss"] == 1 else "LOSS"
        bs = r["brain_score"]
        cs = r["composite_score"]
        if bs is not None:
            all_scores.append((bs, outcome))
            if outcome == "WIN":
                brain_wins.append(bs)
            else:
                brain_losses.append(bs)
        if cs is not None:
            if outcome == "WIN":
                comp_wins.append(cs)
            else:
                comp_losses.append(cs)

    avg_brain_win = sum(brain_wins)/len(brain_wins) if brain_wins else 0
    avg_brain_loss = sum(brain_losses)/len(brain_losses) if brain_losses else 0
    avg_comp_win = sum(comp_wins)/len(comp_wins) if comp_wins else 0
    avg_comp_loss = sum(comp_losses)/len(comp_losses) if comp_losses else 0

    all_scores.sort(key=lambda x: x[0])
    deciles = []
    n = len(all_scores)
    chunk_size = max(1, n // 10)
    for i in range(0, n, chunk_size):
        chunk = all_scores[i:i+chunk_size]
        if not chunk:
            continue
        low = chunk[0][0]
        high = chunk[-1][0]
        wins = sum(1 for _, out in chunk if out == "WIN")
        total = len(chunk)
        deciles.append({
            "range": f"{low:.0f}-{high:.0f}",
            "trades": total,
            "win_rate": (wins/total*100) if total else 0
        })
    return {
        "avg_brain_win": avg_brain_win,
        "avg_brain_loss": avg_brain_loss,
        "avg_composite_win": avg_comp_win,
        "avg_composite_loss": avg_comp_loss,
        "brain_deciles": deciles
    }

# ----------------------------------------------------------------------
# 10. Campaign Comparison
# ----------------------------------------------------------------------
def campaign_list():
    conn = get_connection()
    rows = conn.execute("SELECT run_id, start_time, end_time, total_decisions, executed_trades, wins, losses FROM research_runs ORDER BY start_time").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def campaign_compare(selected_ids=None):
    if not selected_ids:
        campaigns = campaign_list()
        selected_ids = [c["run_id"] for c in campaigns]
    comparison = {}
    for rid in selected_ids:
        perf = overall_performance(run_id=rid)
        comparison[rid] = perf
    return comparison

# ----------------------------------------------------------------------
# 11. Mode Performance (New)
# ----------------------------------------------------------------------
def mode_performance(run_id=None):
    where, params = _closed_trades_where(run_id)
    conn = get_connection()
    rows = conn.execute(f"SELECT mode, win_loss, pnl FROM trades {where}", params).fetchall()
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
    result = {}
    for md, data in modes.items():
        total = data["trades"]
        wins = data["wins"]
        wr = (wins / total * 100) if total else 0
        pf = data["gross_profit"] / data["gross_loss"] if data["gross_loss"] else float('inf')
        avg_win = data["gross_profit"] / wins if wins else 0
        avg_loss = data["gross_loss"] / (total - wins) if (total - wins) else 0
        expectancy = (wins/total)*avg_win - ((total-wins)/total)*avg_loss if total else 0
        result[md] = {
            "trades": total,
            "win_rate": wr,
            "profit_factor": pf,
            "expectancy": expectancy
        }
    return result

# ----------------------------------------------------------------------
# Report Generation
# ----------------------------------------------------------------------
def print_section_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def generate_research_report(run_id=None):
    if run_id:
        print(f"\n*** Filtered by Run ID: {run_id} ***")

    perf = overall_performance(run_id=run_id)
    print_section_header("1. OVERALL PERFORMANCE")
    print(f"  Total Trades      : {perf['total']}")
    print(f"  Wins / Losses     : {perf['wins']} / {perf['losses']}")
    print(f"  Win Rate          : {perf['win_rate']:.2f}%")
    print(f"  Profit Factor     : {perf['profit_factor']:.2f}")
    print(f"  Expectancy        : {perf['expectancy']:.2f}")
    print(f"  Max Drawdown      : {perf['max_drawdown']:.2f}")
    print(f"  Avg Holding (s)   : {perf['avg_holding_seconds']:.0f}")
    print(f"  Avg R‑Multiple    : {perf['avg_r_multiple']:.2f}")
    print(f"  Max Consec Wins   : {perf['max_consecutive_wins']}")
    print(f"  Max Consec Losses : {perf['max_consecutive_losses']}")

    brain = brain_score_buckets(run_id=run_id)
    print_section_header("2. BRAIN SCORE ANALYSIS")
    for bucket in ["0-20","20-40","40-60","60-80","80-100"]:
        d = brain.get(bucket, {"trades":0,"wins":0,"win_rate":0})
        print(f"  {bucket:8s}: Trades {d['trades']:4d} | Wins {d['wins']:4d} | WR {d['win_rate']:.1f}%")

    comp = composite_score_buckets(run_id=run_id)
    print_section_header("3. COMPOSITE SCORE ANALYSIS")
    for bucket in ["0-20","20-40","40-60","60-80","80-100"]:
        d = comp.get(bucket, {"trades":0,"wins":0,"win_rate":0})
        print(f"  {bucket:8s}: Trades {d['trades']:4d} | Wins {d['wins']:4d} | WR {d['win_rate']:.1f}%")

    engines = engine_attribution(run_id=run_id)
    print_section_header("4. ENGINE ATTRIBUTION")
    for name, data in engines.items():
        print(f"  {name:25s}: Avg {data['avg_contribution']:+.2f} | Pos WR {data['positive_win_rate']:.1f}% | N={data['occurrences']} | Total {data['total_contribution']:+.2f}")

    regimes = regime_analysis(run_id=run_id)
    print_section_header("5. MARKET REGIME PERFORMANCE")
    for regime, d in regimes.items():
        print(f"  {regime:20s}: Trades {d['trades']:4d} | WR {d['win_rate']:.1f}%")

    sessions = session_analysis(run_id=run_id)
    print_section_header("6. SESSION PERFORMANCE (approx UTC)")
    for session, d in sessions.items():
        print(f"  {session:10s}: Trades {d['trades']:4d} | WR {d['win_rate']:.1f}%")

    syms = symbol_analysis(run_id=run_id)
    print_section_header("7. SYMBOL PERFORMANCE")
    for sym, d in syms.items():
        print(f"  {sym:10s}: Trades {d['trades']:4d} | WR {d['win_rate']:.1f}%")

    tfs = timeframe_analysis(run_id=run_id)
    print_section_header("8. TIMEFRAME PERFORMANCE")
    for tf, d in tfs.items():
        print(f"  {tf:6s}: Trades {d['trades']:4d} | WR {d['win_rate']:.1f}%")

    cal = score_calibration(run_id=run_id)
    print_section_header("9. SCORE CALIBRATION")
    print(f"  Avg Brain Score (Wins)   : {cal['avg_brain_win']:.2f}")
    print(f"  Avg Brain Score (Losses) : {cal['avg_brain_loss']:.2f}")
    print(f"  Avg Composite (Wins)     : {cal['avg_composite_win']:.2f}")
    print(f"  Avg Composite (Losses)   : {cal['avg_composite_loss']:.2f}")
    print("  Brain Score Deciles:")
    for dec in cal["brain_deciles"]:
        print(f"    {dec['range']:10s}: Trades {dec['trades']:4d} | WR {dec['win_rate']:.1f}%")

    # New: Mode Performance
    modes = mode_performance(run_id=run_id)
    print_section_header("10. MODE PERFORMANCE")
    if modes:
        for md, data in modes.items():
            print(f"  {md:8s}: Trades {data['trades']:4d} | WR {data['win_rate']:.1f}% | PF {data['profit_factor']:.2f} | Expect {data['expectancy']:.2f}")
    else:
        print("  No mode data available.")

    print("\n" + "="*70)
    print("END OF REPORT")

# ----------------------------------------------------------------------
# Validation & Aggregation (Phase 32)
# ----------------------------------------------------------------------
def get_all_campaigns():
    conn = get_connection()
    rows = conn.execute("""
        SELECT run_id, symbols, modes, timeframes,
               total_decisions, executed_trades, wins, losses,
               avg_brain_score, avg_composite_score, duration
        FROM research_runs
        WHERE end_time IS NOT NULL
        ORDER BY start_time
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def rank_symbols():
    campaigns = get_all_campaigns()
    symbols = {}
    for c in campaigns:
        sym = c["symbols"]
        if sym not in symbols:
            symbols[sym] = {"trades":0, "wins":0, "campaigns":0}
        symbols[sym]["trades"] += c["executed_trades"]
        symbols[sym]["wins"] += c["wins"]
        symbols[sym]["campaigns"] += 1
    for sym in symbols:
        total = symbols[sym]["trades"]
        symbols[sym]["win_rate"] = (symbols[sym]["wins"]/total*100) if total else 0
    return dict(sorted(symbols.items(), key=lambda x: x[1]["win_rate"], reverse=True))

def rank_timeframes():
    campaigns = get_all_campaigns()
    tfs = {}
    for c in campaigns:
        tf = c["timeframes"].split(",")[0].strip() if c["timeframes"] else "15m"
        if tf not in tfs:
            tfs[tf] = {"trades":0, "wins":0, "campaigns":0}
        tfs[tf]["trades"] += c["executed_trades"]
        tfs[tf]["wins"] += c["wins"]
        tfs[tf]["campaigns"] += 1
    for tf in tfs:
        total = tfs[tf]["trades"]
        tfs[tf]["win_rate"] = (tfs[tf]["wins"]/total*100) if total else 0
    return dict(sorted(tfs.items(), key=lambda x: x[1]["win_rate"], reverse=True))

def flag_campaigns():
    campaigns = get_all_campaigns()
    flags = []
    for c in campaigns:
        run_id = c["run_id"]
        perf = overall_performance(run_id=run_id)
        issues = []
        if c["executed_trades"] < 30:
            issues.append("Low sample size (<30 trades)")
        if perf["profit_factor"] < 1.0:
            issues.append("Profit Factor < 1.0")
        if perf["expectancy"] < 0:
            issues.append("Negative expectancy")
        if perf["max_drawdown"] > 100000:
            issues.append("Excessive drawdown (>100k)")
        if issues:
            flags.append({
                "run_id": run_id, "symbol": c["symbols"], "mode": c["modes"],
                "issues": issues, "trades": c["executed_trades"],
                "win_rate": perf["win_rate"], "profit_factor": perf["profit_factor"],
                "expectancy": perf["expectancy"], "max_drawdown": perf["max_drawdown"]
            })
    return flags

def compare_campaigns_ranking():
    campaigns = get_all_campaigns()
    ranked = []
    for c in campaigns:
        perf = overall_performance(run_id=c["run_id"])
        ranked.append({
            "run_id": c["run_id"], "symbol": c["symbols"], "mode": c["modes"],
            "trades": c["executed_trades"], "win_rate": perf["win_rate"],
            "profit_factor": perf["profit_factor"], "expectancy": perf["expectancy"],
            "max_drawdown": perf["max_drawdown"]
        })
    ranked.sort(key=lambda x: x["win_rate"], reverse=True)
    return ranked

def two_proportion_z_test(wins1, total1, wins2, total2):
    if total1 == 0 or total2 == 0:
        return None, None
    p1 = wins1/total1
    p2 = wins2/total2
    p_pool = (wins1+wins2)/(total1+total2)
    se = sqrt(p_pool*(1-p_pool)*(1/total1 + 1/total2))
    if se == 0:
        return None, None
    z = (p1 - p2)/se
    from math import erf
    def phi(x):
        return (1.0 + erf(x / sqrt(2.0))) / 2.0
    p_value = 2*(1 - phi(abs(z))) if z else None
    return z, p_value

def compare_two_campaigns_statistical(run_id1, run_id2):
    perf1 = overall_performance(run_id1)
    perf2 = overall_performance(run_id2)
    wins1, total1 = perf1["wins"], perf1["total"]
    wins2, total2 = perf2["wins"], perf2["total"]
    z, p = two_proportion_z_test(wins1, total1, wins2, total2)
    return {
        "campaign1": {"run_id": run_id1, "win_rate": perf1["win_rate"], "trades": total1},
        "campaign2": {"run_id": run_id2, "win_rate": perf2["win_rate"], "trades": total2},
        "z_score": round(z, 3) if z else None,
        "p_value": round(p, 4) if p else None,
        "significant": (p is not None and p < 0.05)
    }

def generate_validation_report():
    print("\n" + "="*70)
    print("  JAGUAR QUANT X – MULTI-CAMPAIGN VALIDATION REPORT")
    print("="*70)

    ranked = compare_campaigns_ranking()
    print_section_header("1. CAMPAIGN RANKING (by Win Rate)")
    for i, c in enumerate(ranked, 1):
        print(f"  {i:2d}. {c['symbol']:8s} {c['mode']:6s} | Trades {c['trades']:4d} | WR {c['win_rate']:.1f}% | PF {c['profit_factor']:.2f} | Expect {c['expectancy']:.2f} | DD {c['max_drawdown']:.0f}")

    sym_ranking = rank_symbols()
    print_section_header("2. SYMBOL RANKING")
    for sym, data in sym_ranking.items():
        print(f"  {sym:10s}: Trades {data['trades']:5d} | Wins {data['wins']:5d} | WR {data['win_rate']:.1f}% | Campaigns {data['campaigns']}")

    tf_ranking = rank_timeframes()
    print_section_header("3. TIMEFRAME RANKING")
    for tf, data in tf_ranking.items():
        print(f"  {tf:6s}: Trades {data['trades']:5d} | Wins {data['wins']:5d} | WR {data['win_rate']:.1f}% | Campaigns {data['campaigns']}")

    flags = flag_campaigns()
    print_section_header("4. FLAGGED CAMPAIGNS")
    if not flags:
        print("  ✅ No campaigns flagged.")
    else:
        for f in flags:
            print(f"  ⚠️  {f['run_id'][:8]}... {f['symbol']} {f['mode']} | Trades {f['trades']} | WR {f['win_rate']:.1f}% | PF {f['profit_factor']:.2f} | Expect {f['expectancy']:.2f} | DD {f['max_drawdown']:.0f}")
            for issue in f["issues"]:
                print(f"     - {issue}")

    campaigns = get_all_campaigns()
    if len(campaigns) >= 2:
        print_section_header("5. STATISTICAL COMPARISON (first two campaigns)")
        rid1 = campaigns[0]["run_id"]
        rid2 = campaigns[1]["run_id"]
        comp = compare_two_campaigns_statistical(rid1, rid2)
        print(f"  Campaign A: {rid1[:8]}... (WR {comp['campaign1']['win_rate']:.1f}%, N={comp['campaign1']['trades']})")
        print(f"  Campaign B: {rid2[:8]}... (WR {comp['campaign2']['win_rate']:.1f}%, N={comp['campaign2']['trades']})")
        if comp["z_score"] is not None:
            sig = "SIGNIFICANT" if comp["significant"] else "not significant"
            print(f"  Z-score: {comp['z_score']:.3f}, p-value: {comp['p_value']:.4f} → {sig}")
        else:
            print("  Cannot compute statistics (zero variance or insufficient data).")
    else:
        print_section_header("5. STATISTICAL COMPARISON")
        print("  Need at least two campaigns with trades.")

    print("\n" + "="*70)
    print("END OF VALIDATION REPORT")
