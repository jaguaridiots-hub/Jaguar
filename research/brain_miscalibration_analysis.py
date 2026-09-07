# research/brain_miscalibration_analysis.py
import json
from datetime import datetime
from collections import defaultdict
from core.backtest_engine import BacktestEngine
from core.trade import Trade
from core.trade_simulator import TradeSimulator
from core.filter_attribution import get_attribution
from research.recorder import record_trade_close, record_decision_snapshot
from research.database import update_decision_outcome, update_decision_stage
from research.research_trade_planner import generate_research_plan


class MiscalibrationEngine(BacktestEngine):
    """Replays all candles and logs detailed trade-level data for miscalibration analysis."""

    def replay(self, state, candles):
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        records = []   # will hold dicts: brain_score, composite, contributions, plan, outcome (win/loss), reasons

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]
            attribution.count_candle()

            for tf, market in state.market.items():
                full_list = full_candles_by_tf[tf]
                historical_tf = [c for c in full_list if c.get("time", 0) <= replay_time]
                market["candles"] = historical_tf
            state.market_current = state.market.get(state.interval)
            if hasattr(state, 'indicators'):
                state.indicators = None
            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            self.registry.run(state, self.bus,
                              skip={"BacktestEngine", "YahooMarketEngine"})

            if state.market_current:
                full_current = full_candles_by_tf[state.interval]
                state.market_current["candles"] = [
                    c for c in full_current if c.get("time", 0) <= replay_time
                ]

            # Gather data
            master = getattr(state, "master_decision", {})
            brain = getattr(state, "ai_brain", {})
            brain_score = brain.get("score", 0)
            composite = master.get("score", 0)
            contributions_json = getattr(state, "brain_explain", {}).get("contributions", [])
            planner = getattr(state, "trade_plan", {})
            decision = master.get("decision", "UNKNOWN")
            reasons = master.get("reasons", [])

            # Plan
            if decision in ("BUY", "SELL") and planner:
                plan = {
                    "entry": planner["entry"],
                    "stop": planner["stop"],
                    "tp1": planner["tp1"],
                    "tp2": planner.get("tp2", planner["tp1"]),
                    "direction": decision,
                }
            else:
                plan = generate_research_plan(state)
                plan["direction"] = decision if decision in ("BUY", "SELL") else "BUY"

            # Simulate outcome
            trade = Trade(
                direction=plan["direction"],
                entry=plan["entry"],
                stop_loss=plan["stop"],
                take_profit_1=plan["tp1"],
                take_profit_2=plan["tp2"],
                entry_time=str(candles[index]["time"]),
                quantity=1.0,
                uuid=None
            )
            future = candles[index + 1:]
            simulator.simulate(trade, future)
            trade.compute_pnl()
            win_loss = 1 if trade.status == "WIN" else 0
            pnl = trade.pnl or 0

            records.append({
                "brain_score": brain_score,
                "composite_score": composite,
                "contributions": contributions_json,
                "outcome": "WIN" if win_loss else "LOSS",
                "pnl": pnl,
                "reasons": reasons,
                "plan": plan,
            })

            # Production trade handling (unchanged)
            decision_id = record_decision_snapshot(state, candle_timestamp=replay_time)
            trade_uuid = getattr(state, "_trade_id", None)
            if trade_uuid is None:
                continue
            quantity = state.risk.get("position_size", 1.0)
            entry_time_str = _to_iso(replay_time)
            trade_real = Trade(
                direction=plan["direction"], entry=plan["entry"],
                stop_loss=plan["stop"], take_profit_1=plan["tp1"],
                take_profit_2=plan["tp2"],
                entry_time=entry_time_str, quantity=quantity, uuid=trade_uuid
            )
            future = candles[index + 1:]
            trade_real = simulator.simulate(trade_real, future)
            trade_real.compute_pnl()
            if trade_real.status in ("WIN", "LOSS"):
                holding_seconds = 0
                if trade_real.entry_time and trade_real.exit_time:
                    try:
                        entry_dt = _parse_iso(trade_real.entry_time)
                        exit_dt = _parse_iso(trade_real.exit_time)
                        holding_seconds = (exit_dt - entry_dt).total_seconds()
                    except:
                        pass
                record_trade_close(
                    uuid=trade_real.uuid, exit_price=trade_real.exit_price,
                    pnl=trade_real.pnl, r_multiple=trade_real.rr,
                    win_loss=(trade_real.status == "WIN"), holding_time=holding_seconds,
                    exit_time=trade_real.exit_time
                )
                update_decision_outcome(decision_id, trade_real.status, trade_real.uuid)
            self.result.total_trades += 1
            if trade_real.status == "WIN":
                self.result.wins += 1
            elif trade_real.status == "LOSS":
                self.result.losses += 1

        if self.result.total_trades:
            self.result.win_rate = round(self.result.wins * 100 / self.result.total_trades, 2)
            self.result.loss_rate = round(self.result.losses * 100 / self.result.total_trades, 2)

        # Now analyze miscalibration
        self._analyze(records)


    def _analyze(self, records):
        total = len(records)

        # Buckets – include negative scores
        buckets = [(-1000, 0), (0,20), (20,40), (40,60), (60,80), (80,101)]
        bucket_stats = {}

        for lo, hi in buckets:
            subset = [r for r in records if lo <= r["brain_score"] < hi]
            if not subset:
                continue
            wins = sum(1 for r in subset if r["outcome"] == "WIN")
            cnt = len(subset)
            wr = wins / cnt * 100
            gp = sum(r["pnl"] for r in subset if r["pnl"] > 0)
            gl = abs(sum(r["pnl"] for r in subset if r["pnl"] < 0))
            pf = gp / gl if gl else float('inf')
            avg_win = gp / wins if wins else 0
            avg_loss = gl / (cnt - wins) if (cnt - wins) else 0
            expectancy = (wins/cnt * avg_win) - ((cnt-wins)/cnt * avg_loss)
            label = f"{lo}-{hi}" if lo >= 0 else "<0"
            bucket_stats[label] = {"trades": cnt, "wins": wins, "wr": wr, "pf": pf, "expectancy": expectancy}

        # Find high-score losing trades (score >= 80, LOSS)
        high_losers = [r for r in records if r["brain_score"] >= 80 and r["outcome"] == "LOSS"]
        # Find low-score winning trades (score < 40, WIN)
        low_winners = [r for r in records if r["brain_score"] < 40 and r["outcome"] == "WIN"]

        # Engine contribution analysis for misclassified trades
        engine_contrib_winners = defaultdict(list)
        engine_contrib_losers = defaultdict(list)
        for r in records:
            contribs = r["contributions"] if isinstance(r["contributions"], list) else []
            for eng in contribs:
                name = eng.get("engine") or eng.get("label") or "Unknown"
                if r["outcome"] == "WIN":
                    engine_contrib_winners[name].append(eng.get("contribution", 0))
                else:
                    engine_contrib_losers[name].append(eng.get("contribution", 0))

        # Rank engines by contribution difference (Loser mean - Winner mean)
        engine_diff = {}
        for eng in set(list(engine_contrib_winners.keys()) + list(engine_contrib_losers.keys())):
            winner_vals = engine_contrib_winners.get(eng, [])
            loser_vals = engine_contrib_losers.get(eng, [])
            mean_winner = sum(winner_vals)/len(winner_vals) if winner_vals else 0
            mean_loser = sum(loser_vals)/len(loser_vals) if loser_vals else 0
            engine_diff[eng] = mean_loser - mean_winner   # positive means higher contribution for losers

        # Calibration verdict
        high_wr = bucket_stats.get("80-101", {}).get("wr", 0)
        mid_wr = bucket_stats.get("40-60", {}).get("wr", 0)
        low_wr = bucket_stats.get("0-20", {}).get("wr", 0)
        calibration = "Well calibrated"
        if high_wr and mid_wr and high_wr < mid_wr - 5:
            calibration = "Overconfident (high scores underperform)"
        elif low_wr and mid_wr and low_wr > mid_wr + 5:
            calibration = "Underconfident (low scores overperform)"

        # Print report
        print("\n" + "=" * 70)
        print("  BRAIN MISCALIBRATION ANALYSIS")
        print("=" * 70)
        print(f"  Total simulated trades : {total}")

        print("\n  [1] PERFORMANCE BY BRAIN SCORE BUCKET")
        print(f"  {'Bucket':>8s} {'Trades':>7s} {'WinRate':>8s} {'PF':>7s} {'Expect':>8s}")
        print(f"  {'-'*8} {'-'*7} {'-'*8} {'-'*7} {'-'*8}")
        for bkey, stats in bucket_stats.items():
            print(f"  {bkey:>8s} {stats['trades']:>7d} {stats['wr']:>7.1f}% {stats['pf']:>7.2f} {stats['expectancy']:>+8.2f}")

        print(f"\n  [2] HIGH‑SCORE LOSING TRADES (score ≥ 80, LOSS) : {len(high_losers)}")
        if high_losers:
            print("  First 5 examples:")
            for i, r in enumerate(high_losers[:5], 1):
                print(f"    {i}. Brain={r['brain_score']:.1f}  Comp={r['composite_score']:.1f}  PnL={r['pnl']:+.2f}")

        print(f"\n  [3] LOW‑SCORE WINNING TRADES (score < 40, WIN) : {len(low_winners)}")
        if low_winners:
            print("  First 5 examples:")
            for i, r in enumerate(low_winners[:5], 1):
                print(f"    {i}. Brain={r['brain_score']:.1f}  Comp={r['composite_score']:.1f}  PnL={r['pnl']:+.2f}")

        print("\n  [4] ENGINE CONTRIBUTION IMBALANCE (Loser mean - Winner mean)")
        ranked = sorted(engine_diff.items(), key=lambda x: abs(x[1]), reverse=True)
        print(f"  {'Engine':25s} {'Loser Mean':>10s} {'Winner Mean':>10s} {'Diff':>8s}")
        print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*8}")
        for eng, diff in ranked[:10]:
            w_mean = sum(engine_contrib_winners.get(eng, [])) / max(1, len(engine_contrib_winners.get(eng, [])))
            l_mean = sum(engine_contrib_losers.get(eng, [])) / max(1, len(engine_contrib_losers.get(eng, [])))
            print(f"  {eng:25s} {l_mean:>+10.2f} {w_mean:>+10.2f} {diff:>+8.2f}")

        print(f"\n  [5] CALIBRATION VERDICT: {calibration}")
        print("=" * 70)


def _to_iso(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts).isoformat()
    try:
        datetime.fromisoformat(str(ts))
        return str(ts)
    except:
        return str(ts)


def _parse_iso(ts):
    try:
        return datetime.fromisoformat(ts)
    except:
        return datetime.fromtimestamp(float(ts))


def run_brain_miscalibration_analysis(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    app = JaguarOrchestrator()
    state = app.analyze(symbol, "15m", mode=mode)

    init_db()
    run_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()
    insert_research_run(run_id, JAGUAR_VERSION, symbol, mode, "15m", start_time=start_time)
    state.run_id = run_id

    backtest_state = copy.deepcopy(state)
    backtest_state.symbol = symbol
    backtest_state.interval = "15m"
    backtest_state.mode = mode
    backtest_state.run_id = run_id

    registry = EngineRegistry()
    register(registry)
    engine = MiscalibrationEngine(registry)
    bus = app.bus

    engine.run(backtest_state, bus)

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    stats = get_campaign_stats(run_id)
    update_research_run(run_id, end_time, duration, stats["total_decisions"],
                        stats["executed_trades"], stats["wins"], stats["losses"],
                        stats["avg_brain_score"], stats["avg_composite_score"],
                        stats["avg_confidence"])
